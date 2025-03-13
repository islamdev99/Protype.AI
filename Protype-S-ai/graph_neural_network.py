
import torch
import torch.nn as nn
import torch.nn.functional as F
import networkx as nx
import numpy as np
from torch_geometric.nn import GCNConv
from torch_geometric.data import Data

class KnowledgeGNN:
    def __init__(self, knowledge_graph=None):
        """Initialize Knowledge Graph Neural Network"""
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.knowledge_graph = knowledge_graph
        self.node_mapping = {}  # Maps node names to indices
        self.reverse_mapping = {}  # Maps indices to node names
        self.model = None
        self.embeddings = None
        
    def prepare_graph_data(self):
        """Convert NetworkX graph to PyTorch Geometric data format"""
        if not self.knowledge_graph:
            return None
            
        # Create node mappings
        for i, node in enumerate(self.knowledge_graph.nodes()):
            self.node_mapping[node] = i
            self.reverse_mapping[i] = node
            
        # Prepare edge index
        edge_index = []
        for source, target in self.knowledge_graph.edges():
            edge_index.append([self.node_mapping[source], self.node_mapping[target]])
            
        # Convert to tensor
        edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
        
        # Create node features (one-hot encoding of node type)
        node_types = ['question', 'answer', 'entity', 'source', 'unknown']
        type_to_idx = {t: i for i, t in enumerate(node_types)}
        
        # Default features
        x = torch.zeros((len(self.knowledge_graph.nodes()), len(node_types)), dtype=torch.float)
        
        for node, idx in self.node_mapping.items():
            node_type = self.knowledge_graph.nodes[node].get('type', 'unknown')
            type_idx = type_to_idx.get(node_type, type_to_idx['unknown'])
            x[idx, type_idx] = 1.0
            
        return Data(x=x, edge_index=edge_index)
        
    def build_model(self, hidden_channels=64):
        """Build the GNN model"""
        num_features = 5  # Number of node types
        
        class GCN(torch.nn.Module):
            def __init__(self, num_features, hidden_channels):
                super().__init__()
                self.conv1 = GCNConv(num_features, hidden_channels)
                self.conv2 = GCNConv(hidden_channels, hidden_channels)
                
            def forward(self, x, edge_index):
                x = self.conv1(x, edge_index)
                x = F.relu(x)
                x = F.dropout(x, p=0.1, training=self.training)
                x = self.conv2(x, edge_index)
                return x
                
        self.model = GCN(num_features, hidden_channels).to(self.device)
        
    def train(self, epochs=100, lr=0.01):
        """Train the GNN model"""
        if not self.model:
            self.build_model()
            
        data = self.prepare_graph_data()
        if data is None:
            return False
            
        # Move data to device
        data = data.to(self.device)
        
        # Set up training
        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr, weight_decay=5e-4)
        criterion = nn.MSELoss()
        
        # Train model
        self.model.train()
        for epoch in range(epochs):
            optimizer.zero_grad()
            out = self.model(data.x, data.edge_index)
            
            # Self-supervised loss: similar nodes should have similar embeddings
            loss = 0
            for (u, v) in self.knowledge_graph.edges():
                u_idx = self.node_mapping[u]
                v_idx = self.node_mapping[v]
                
                # Edge prediction loss
                similarity = F.cosine_similarity(out[u_idx].unsqueeze(0), out[v_idx].unsqueeze(0))
                loss += criterion(similarity, torch.tensor([1.0], device=self.device))
                
            # Add random negative samples
            for _ in range(len(self.knowledge_graph.edges()) // 2):
                u_idx = np.random.randint(0, len(self.node_mapping))
                v_idx = np.random.randint(0, len(self.node_mapping))
                
                if not self.knowledge_graph.has_edge(self.reverse_mapping[u_idx], self.reverse_mapping[v_idx]):
                    similarity = F.cosine_similarity(out[u_idx].unsqueeze(0), out[v_idx].unsqueeze(0))
                    loss += criterion(similarity, torch.tensor([0.0], device=self.device))
            
            loss.backward()
            optimizer.step()
            
            if (epoch + 1) % 20 == 0:
                print(f'Epoch {epoch+1}/{epochs}, Loss: {loss.item():.4f}')
                
        # Generate and store node embeddings
        self.model.eval()
        with torch.no_grad():
            self.embeddings = self.model(data.x, data.edge_index)
            
        return True
    
    def find_related_concepts(self, concept, top_k=5):
        """Find concepts related to the given concept using GNN embeddings"""
        if concept not in self.node_mapping or self.embeddings is None:
            return []
            
        concept_idx = self.node_mapping[concept]
        concept_embedding = self.embeddings[concept_idx]
        
        # Calculate similarities
        similarities = []
        for node, idx in self.node_mapping.items():
            if node != concept:
                node_embedding = self.embeddings[idx]
                similarity = F.cosine_similarity(concept_embedding.unsqueeze(0), node_embedding.unsqueeze(0))
                similarities.append((node, similarity.item()))
                
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    def infer_new_knowledge(self, threshold=0.7):
        """Infer new knowledge edges that are not explicitly in the graph"""
        if self.embeddings is None:
            return []
            
        inferred_edges = []
        
        # Check pairs of nodes that aren't directly connected
        for node1, idx1 in self.node_mapping.items():
            for node2, idx2 in self.node_mapping.items():
                if node1 != node2 and not self.knowledge_graph.has_edge(node1, node2):
                    # If they're both entities, check similarity
                    node1_type = self.knowledge_graph.nodes[node1].get('type', 'unknown')
                    node2_type = self.knowledge_graph.nodes[node2].get('type', 'unknown')
                    
                    # Only infer certain types of connections
                    if (node1_type == 'entity' and node2_type == 'entity') or \
                       (node1_type == 'question' and node2_type == 'question'):
                        
                        # Calculate similarity
                        node1_embedding = self.embeddings[idx1]
                        node2_embedding = self.embeddings[idx2]
                        similarity = F.cosine_similarity(node1_embedding.unsqueeze(0), node2_embedding.unsqueeze(0))
                        
                        # If similarity is high enough, suggest a new edge
                        if similarity.item() > threshold:
                            inferred_edges.append((node1, node2, similarity.item()))
                            
        # Sort by similarity score
        inferred_edges.sort(key=lambda x: x[2], reverse=True)
        
        return inferred_edges
