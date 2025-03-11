
import os
import time
import json
import pickle
import numpy as np
from datetime import datetime
import torch
from transformers import AutoTokenizer, AutoModel
import faiss

# Configure FAISS and embeddings
USE_GPU = torch.cuda.is_available()
EMBEDDING_DIM = 384  # Using BERT embeddings dimension

class AdvancedMemory:
    def __init__(self):
        self.index = None
        self.metadata = {}
        self.tokenizer = None
        self.model = None
        self.initialize_embeddings()
        self.initialize_index()
        
    def initialize_embeddings(self):
        """Initialize the embedding model"""
        try:
            print("Loading embedding model...")
            # Using a smaller model for efficiency while maintaining quality
            model_name = "sentence-transformers/all-MiniLM-L6-v2"
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name)
            
            # Move model to GPU if available
            if USE_GPU:
                self.model = self.model.cuda()
            
            self.model.eval()  # Set to evaluation mode
            print("Embedding model loaded successfully")
        except Exception as e:
            print(f"Error loading embedding model: {e}")
            self.tokenizer = None
            self.model = None
    
    def initialize_index(self):
        """Initialize FAISS index or load existing one"""
        if os.path.exists('memory_index.faiss') and os.path.exists('memory_metadata.pkl'):
            try:
                # Load existing index
                self.index = faiss.read_index('memory_index.faiss')
                
                # Load metadata
                with open('memory_metadata.pkl', 'rb') as f:
                    self.metadata = pickle.load(f)
                
                print(f"Loaded existing memory index with {self.index.ntotal} entries")
                
                # Move index to GPU if available
                if USE_GPU and self.index.ntotal > 0:
                    res = faiss.StandardGpuResources()
                    self.index = faiss.index_cpu_to_gpu(res, 0, self.index)
                
                return
            except Exception as e:
                print(f"Error loading existing index: {e}")
        
        # Create new index
        try:
            self.index = faiss.IndexFlatL2(EMBEDDING_DIM)
            self.metadata = {}
            print("Created new FAISS index")
            
            # Move index to GPU if available
            if USE_GPU:
                res = faiss.StandardGpuResources()
                self.index = faiss.index_cpu_to_gpu(res, 0, self.index)
        except Exception as e:
            print(f"Error creating FAISS index: {e}")
    
    def save_index(self):
        """Save the FAISS index and metadata to disk"""
        try:
            # Move index to CPU if it's on GPU
            if USE_GPU:
                index_cpu = faiss.index_gpu_to_cpu(self.index)
            else:
                index_cpu = self.index
                
            # Save index and metadata
            faiss.write_index(index_cpu, 'memory_index.faiss')
            
            with open('memory_metadata.pkl', 'wb') as f:
                pickle.dump(self.metadata, f)
                
            print(f"Saved memory index with {self.index.ntotal} entries")
            return True
        except Exception as e:
            print(f"Error saving index: {e}")
            return False
    
    def get_embedding(self, text):
        """Get embedding for text using the model"""
        if self.tokenizer is None or self.model is None:
            raise ValueError("Embedding model not initialized")
            
        # Tokenize and prepare for model
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
        
        # Move to GPU if available
        if USE_GPU:
            inputs = {k: v.cuda() for k, v in inputs.items()}
        
        # Get embeddings
        with torch.no_grad():
            outputs = self.model(**inputs)
            
        # Use mean of last hidden state as embedding
        embeddings = outputs.last_hidden_state.mean(dim=1)
        
        # Convert to numpy array
        return embeddings[0].cpu().numpy()
    
    def add_knowledge(self, question, answer, source="system", metadata=None):
        """Add knowledge to the memory index"""
        if self.index is None:
            self.initialize_index()
            
        try:
            # Get embeddings for question and answer
            question_embedding = self.get_embedding(question)
            answer_embedding = self.get_embedding(answer)
            
            # Combine embeddings (simple average)
            combined_embedding = (question_embedding + answer_embedding) / 2
            combined_embedding = np.array([combined_embedding.astype('float32')])
            
            # Add to index
            self.index.add(combined_embedding)
            
            # Store metadata
            index_id = self.index.ntotal - 1
            self.metadata[index_id] = {
                'question': question,
                'answer': answer,
                'source': source,
                'timestamp': time.time(),
                'access_count': 0,
                'additional': metadata or {}
            }
            
            # Periodically save index
            if self.index.ntotal % 10 == 0:
                self.save_index()
                
            return True
        except Exception as e:
            print(f"Error adding knowledge to memory: {e}")
            return False
    
    def search(self, query, k=5):
        """Search for similar knowledge in the memory"""
        if self.index is None or self.index.ntotal == 0:
            return []
            
        try:
            # Get query embedding
            query_embedding = self.get_embedding(query)
            query_embedding = np.array([query_embedding.astype('float32')])
            
            # Search index
            distances, indices = self.index.search(query_embedding, k)
            
            results = []
            for i, idx in enumerate(indices[0]):
                if idx != -1 and idx in self.metadata:  # -1 means no result
                    # Update access count
                    self.metadata[idx]['access_count'] += 1
                    
                    # Add to results
                    results.append({
                        'question': self.metadata[idx]['question'],
                        'answer': self.metadata[idx]['answer'],
                        'source': self.metadata[idx]['source'],
                        'similarity': 1.0 - distances[0][i] / 10.0,  # Normalize distance to similarity
                        'timestamp': self.metadata[idx]['timestamp'],
                        'metadata': self.metadata[idx].get('additional', {})
                    })
            
            return results
        except Exception as e:
            print(f"Error searching memory: {e}")
            return []
    
    def get_rag_context(self, query, max_results=3, min_similarity=0.6):
        """Get RAG context for query"""
        search_results = self.search(query, k=max_results*2)  # Get more to filter by similarity
        
        # Filter by similarity
        rag_context = [
            f"Q: {result['question']}\nA: {result['answer']}"
            for result in search_results
            if result['similarity'] >= min_similarity
        ]
        
        # Limit context length
        return rag_context[:max_results]
    
    def augment_with_rag(self, query, base_answer):
        """Augment an answer with RAG context"""
        rag_context = self.get_rag_context(query)
        
        if not rag_context:
            return base_answer
        
        # Prepare RAG context as a single string
        context_str = "\n\n".join(rag_context)
        
        # Augment the answer using the RAG context
        augmented_answer = f"{base_answer}\n\nAdditional context that may be helpful:\n\n{context_str}"
        
        return augmented_answer
    
    def cleanup_old_entries(self, max_age_days=90, min_access_count=5):
        """Clean up old entries that haven't been accessed much"""
        if self.index is None or self.index.ntotal == 0:
            return 0
        
        try:
            # Calculate cutoff timestamp
            cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
            
            # Collect entries to keep
            keep_indices = []
            keep_embeddings = []
            new_metadata = {}
            
            # Current index as numpy array
            all_embeddings = np.zeros((self.index.ntotal, EMBEDDING_DIM), dtype='float32')
            
            # Iterate through all entries
            for i in range(self.index.ntotal):
                if i in self.metadata:
                    entry = self.metadata[i]
                    
                    # Keep if recently accessed or frequently accessed
                    if entry['timestamp'] > cutoff_time or entry['access_count'] >= min_access_count:
                        # Get the embedding
                        self.index.reconstruct(i, all_embeddings[len(keep_indices)])
                        
                        # Add to keep lists
                        keep_indices.append(i)
                        keep_embeddings.append(all_embeddings[len(keep_indices)-1])
                        new_metadata[len(keep_indices)-1] = entry
            
            # Build new index with kept embeddings
            if keep_embeddings:
                keep_embeddings = np.array(keep_embeddings)
                
                # Create new index
                new_index = faiss.IndexFlatL2(EMBEDDING_DIM)
                new_index.add(keep_embeddings)
                
                # Replace old index and metadata
                self.index = new_index
                self.metadata = new_metadata
                
                # Move to GPU if available
                if USE_GPU:
                    res = faiss.StandardGpuResources()
                    self.index = faiss.index_cpu_to_gpu(res, 0, self.index)
                
                # Save updated index
                self.save_index()
                
                return self.index.ntotal
            
            return 0
        except Exception as e:
            print(f"Error cleaning up old entries: {e}")
            return -1

# Create singleton instance
advanced_memory = AdvancedMemory()
