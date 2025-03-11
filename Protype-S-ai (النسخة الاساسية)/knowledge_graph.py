
import os
import networkx as nx
import spacy
import json
import numpy as np
from database import get_connection, release_connection

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # If model not found, download it
    print("Downloading spaCy model...")
    try:
        spacy.cli.download("en_core_web_sm")
        nlp = spacy.load("en_core_web_sm")
    except Exception as e:
        print(f"Error downloading spaCy model: {e}")
        # Create a minimal nlp function as fallback
        from spacy.lang.en import English
        nlp = English()

class KnowledgeGraph:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.visualization_data = {
            "nodes": [],
            "links": []
        }
        self.node_types = {
            'question': 'blue',
            'entity': 'green',
            'source': 'red',
            'concept': 'purple',
            'inferred': 'orange'
        }
    
    def build_from_database(self):
        """Build knowledge graph from database"""
        self.graph = nx.DiGraph()
        
        try:
            # Get connection
            conn, is_postgres = get_connection()
            cursor = conn.cursor()
            
            # Get all questions and answers
            cursor.execute("SELECT question, answer, source FROM knowledge")
            data = cursor.fetchall()
            
            # Release connection
            release_connection(conn, is_postgres)
            
            # Process data and build graph
            for question, answer, source in data:
                # Add question node
                self.graph.add_node(question, type="question")
                
                # Process with spaCy to extract entities
                doc = nlp(answer)
                
                # Add entities as nodes
                for ent in doc.ents:
                    entity_text = ent.text
                    entity_type = ent.label_
                    
                    if not self.graph.has_node(entity_text):
                        self.graph.add_node(entity_text, type="entity", entity_type=entity_type)
                    
                    # Connect question to entity
                    self.graph.add_edge(question, entity_text, relation="contains")
                    
                # Add source as node
                if not self.graph.has_node(source):
                    self.graph.add_node(source, type="source")
                
                # Connect question to source
                self.graph.add_edge(question, source, relation="from")
                
            print(f"Built knowledge graph with {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges")
            return True
        except Exception as e:
            print(f"Error building knowledge graph: {e}")
            return False
    
    def add_inferred_edge(self, source, target, confidence, max_inferred=30):
        """Add inferred edge to the graph with limits to avoid noise"""
        # Count existing inferred edges
        inferred_count = sum(1 for _, _, attr in self.graph.edges(data=True) 
                            if attr.get('inferred', False))
        
        # Don't add too many inferred edges to avoid noise
        if inferred_count >= max_inferred:
            print(f"Maximum inferred edges ({max_inferred}) reached. Not adding new inference.")
            return False
        
        # Add the edge
        self.graph.add_edge(source, target, 
                           relation="inferred", 
                           confidence=confidence,
                           inferred=True)
        return True
    
    def get_related_concepts(self, concept, max_results=5):
        """Get concepts related to the given concept from the graph"""
        if concept not in self.graph:
            return []
        
        related = []
        
        # Get direct neighbors
        neighbors = list(self.graph.neighbors(concept))
        for neighbor in neighbors:
            node_type = self.graph.nodes[neighbor].get('type', 'unknown')
            edge_data = self.graph.get_edge_data(concept, neighbor) or {}
            confidence = edge_data.get('confidence', 1.0)
            relation = edge_data.get('relation', 'unknown')
            inferred = edge_data.get('inferred', False)
            
            related.append({
                'concept': neighbor,
                'type': node_type,
                'relation': relation,
                'confidence': confidence,
                'inferred': inferred
            })
        
        # Sort by confidence
        related.sort(key=lambda x: x['confidence'], reverse=True)
        
        return related[:max_results]
    
    def find_path(self, source, target, max_length=3):
        """Find shortest path between two concepts"""
        if source not in self.graph or target not in self.graph:
            return None
        
        try:
            path = nx.shortest_path(self.graph, source=source, target=target)
            
            # Only return if path is not too long
            if len(path) <= max_length:
                return path
            return None
        except nx.NetworkXNoPath:
            return None
    
    def get_visualization_data(self, max_nodes=100):
        """Prepare graph visualization data in D3.js format"""
        # Reset visualization data
        self.visualization_data = {
            "nodes": [],
            "links": []
        }
        
        # Node mapping to avoid duplicates
        node_map = {}
        
        # Limit nodes for visualization performance
        nodes = list(self.graph.nodes())[:max_nodes]
        
        # Create nodes
        for i, node in enumerate(nodes):
            node_type = self.graph.nodes[node].get('type', 'unknown')
            node_map[node] = i
            
            self.visualization_data["nodes"].append({
                "id": i,
                "name": node[:30] + "..." if len(node) > 30 else node,
                "type": node_type,
                "color": self.node_types.get(node_type, 'gray')
            })
        
        # Create edges
        for source, target in self.graph.edges():
            if source in node_map and target in node_map:
                edge_data = self.graph.get_edge_data(source, target)
                relation = edge_data.get('relation', 'unknown')
                inferred = edge_data.get('inferred', False)
                
                self.visualization_data["links"].append({
                    "source": node_map[source],
                    "target": node_map[target],
                    "relation": relation,
                    "dashed": inferred
                })
        
        return self.visualization_data
    
    def save_graph(self, filepath="knowledge_graph.json"):
        """Save the graph to a JSON file"""
        data = {
            "nodes": [],
            "edges": []
        }
        
        # Save nodes
        for node in self.graph.nodes():
            node_data = self.graph.nodes[node]
            data["nodes"].append({
                "id": node,
                "type": node_data.get('type', 'unknown'),
                "entity_type": node_data.get('entity_type', '')
            })
        
        # Save edges
        for source, target, edge_data in self.graph.edges(data=True):
            data["edges"].append({
                "source": source,
                "target": target,
                "relation": edge_data.get('relation', 'unknown'),
                "confidence": edge_data.get('confidence', 1.0),
                "inferred": edge_data.get('inferred', False)
            })
        
        # Save to file
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving graph: {e}")
            return False
    
    def load_graph(self, filepath="knowledge_graph.json"):
        """Load the graph from a JSON file"""
        if not os.path.exists(filepath):
            print(f"Graph file not found: {filepath}")
            return False
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Create new graph
            self.graph = nx.DiGraph()
            
            # Add nodes
            for node_data in data["nodes"]:
                node_attrs = {
                    'type': node_data.get('type', 'unknown')
                }
                if 'entity_type' in node_data:
                    node_attrs['entity_type'] = node_data['entity_type']
                    
                self.graph.add_node(node_data["id"], **node_attrs)
            
            # Add edges
            for edge_data in data["edges"]:
                self.graph.add_edge(
                    edge_data["source"],
                    edge_data["target"],
                    relation=edge_data.get('relation', 'unknown'),
                    confidence=edge_data.get('confidence', 1.0),
                    inferred=edge_data.get('inferred', False)
                )
            
            print(f"Loaded knowledge graph with {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges")
            return True
        except Exception as e:
            print(f"Error loading graph: {e}")
            return False
    
    def suggest_learning_topics(self, count=5):
        """Suggest learning topics based on current knowledge graph"""
        # Find nodes with few connections but high importance
        node_scores = {}
        
        for node in self.graph.nodes():
            node_type = self.graph.nodes[node].get('type', '')
            if node_type == 'entity':
                # Count connections
                connections = len(list(self.graph.neighbors(node)))
                
                # Calculate PageRank importance
                if connections > 0:
                    node_scores[node] = connections
        
        # Sort by score
        sorted_nodes = sorted(node_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Return top suggestion
        return [node for node, score in sorted_nodes[:count]]
