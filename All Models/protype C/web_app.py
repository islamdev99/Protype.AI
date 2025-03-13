
import json
import os
import random
import re
import spacy
import threading
import requests
from flask import Flask, render_template, request, jsonify, session
import google.generativeai as genai
from bs4 import BeautifulSoup
import sqlite3
import time
import networkx as nx
from text_to_speech import text_to_speech, get_available_voices

# Initialize Flask application
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Initialize knowledge graph
knowledge_graph = nx.DiGraph()

# Database connection
SQLITE_DB_PATH = 'protype_e0.db'

def get_connection():
    """Returns a SQLite connection"""
    return sqlite3.connect(SQLITE_DB_PATH), False

def release_connection(conn, is_postgres):
    """Closes the connection"""
    conn.close()

def init_db():
    """Initialize database with required tables"""
    conn, is_postgres = get_connection()
    try:
        cursor = conn.cursor()
        
        # SQLite schema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT UNIQUE,
                answer TEXT,
                weight REAL,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT DEFAULT 'system',
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_by TEXT DEFAULT 'system'
            )
        ''')
        
        # Create index for faster searches
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_knowledge_question ON knowledge (question);
        ''')
            
        conn.commit()
    except Exception as e:
        print(f"Database initialization error: {e}")
        conn.rollback()
    finally:
        release_connection(conn, is_postgres)

def save_data(question, answer, weight, source, user="system"):
    """Save data to database"""
    conn, is_postgres = get_connection()
    try:
        cursor = conn.cursor()
        
        # Delete existing record if it exists
        cursor.execute("DELETE FROM knowledge WHERE question = ?", (question,))
        
        # Insert new record
        cursor.execute(
            "INSERT INTO knowledge (question, answer, weight, source, created_by, modified_by) VALUES (?, ?, ?, ?, ?, ?)",
            (question, answer, weight, source, user, user)
        )
            
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving data: {e}")
        conn.rollback()
        return False
    finally:
        release_connection(conn, is_postgres)

def load_data():
    """Load all knowledge data from database"""
    conn, is_postgres = get_connection()
    try:
        cursor = conn.cursor()
        
        query = "SELECT question, answer, weight, source FROM knowledge"
        cursor.execute(query)
        
        rows = cursor.fetchall()
        data = {}
        
        for question, answer, weight, source in rows:
            if question not in data:
                data[question] = []
            data[question].append({
                "answer": answer,
                "weight": weight,
                "source": source
            })
            
        return data
    except Exception as e:
        print(f"Error loading data: {e}")
        return {}
    finally:
        release_connection(conn, is_postgres)

def search_knowledge(query, limit=10):
    """Basic search function"""
    conn, is_postgres = get_connection()
    try:
        cursor = conn.cursor()
        
        # Basic search with SQLite
        search_query = """
            SELECT question, answer, weight, source
            FROM knowledge
            WHERE question LIKE ? OR answer LIKE ?
            LIMIT ?
        """
        search_param = f"%{query}%"
        cursor.execute(search_query, (search_param, search_param, limit))
        
        results = cursor.fetchall()
        return results
    except Exception as e:
        print(f"Search error: {e}")
        return []
    finally:
        release_connection(conn, is_postgres)

# Load spaCy model for NLP
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

# Configure Gemini API
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', "AIzaSyBUDUURqkN5Lvid5P8V0ZXIRpseKC7ffMU")
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini model
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}
gemini_model = genai.GenerativeModel(
    model_name="learnlm-1.5-pro-experimental",
    generation_config=generation_config,
)
chat_session = gemini_model.start_chat(history=[])

# Function to query Gemini Flash
def query_gemini_flash(question):
    try:
        response = chat_session.send_message(question)
        return response.text.strip()
    except Exception as e:
        print(f"Error querying Gemini Flash 2: {e}")
        return f"Failed to get response from Gemini Flash 2: {e}"

# Function to perform Google search
def perform_search(query):
    try:
        params = {
            "engine": "google",
            "q": query,
            "api_key": os.environ.get(
                'SERPAPI_KEY', 
                "f41082ce8546f83f717679baf1318d649d123ba213a92067de9dfdee2ea5accb"
            )
        }
        try:
            from serpapi import google_search
            search = google_search.GoogleSearch(params)
            results = search.get_dict()
            organic_results = results.get("organic_results", [])
            if organic_results:
                return organic_results[0].get("snippet", "No snippet available")
            return "Sorry, I couldn't find anything relevant."
        except ImportError:
            return "SerpAPI module not available. Please install it using 'pip install serpapi'."
    except Exception as e:
        return f"Oops! Search failed: {e}"

def log_action(action_type, description, details=None):
    """Log user actions for analytics"""
    import datetime
    
    # Load existing log
    try:
        with open('user_actions.json', 'r') as f:
            action_log = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        action_log = {
            "version": "1.0",
            "actions": []
        }
    
    action = {
        "timestamp": datetime.datetime.now().isoformat(),
        "user": "web_user",
        "action": action_type,
        "description": description
    }
    
    if details:
        action["details"] = details
        
    action_log["actions"].append(action)
    
    # Save log
    try:
        with open('user_actions.json', 'w') as f:
            json.dump(action_log, f, indent=2)
    except Exception as e:
        print(f"Error saving action log: {e}")

# Flask routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    question = request.json.get('question', '').strip()
    if not question:
        return jsonify({"status": "error", "message": "No question provided"})
    
    # Log chat action
    log_action("chat", f"Asked: {question}")
    
    # Search the knowledge base
    search_results = search_knowledge(question, limit=1)
    
    if search_results:
        # Use existing knowledge
        result = search_results[0]
        return jsonify({
            "status": "success", 
            "answer": result[1],
            "source": result[3]
        })
    else:
        # Query Gemini for new information
        answer = query_gemini_flash(question)
        
        # Save the new knowledge
        save_data(question, answer, 0.6, "gemini_flash_2", "web_user")
        
        return jsonify({
            "status": "success", 
            "answer": answer,
            "source": "gemini_flash_2"
        })

@app.route('/teach', methods=['POST'])
def teach():
    question = request.json.get('question', '').strip()
    answer = request.json.get('answer', '').strip()
    
    if not question or not answer:
        return jsonify({"status": "error", "message": "Question and answer are required"})
    
    # Log teach action
    log_action("teach", f"Added new knowledge: {question}")
    
    # Save to database
    if save_data(question, answer, 0.5, "web_user", "web_user"):
        return jsonify({"status": "success", "message": "Knowledge saved successfully"})
    else:
        return jsonify({"status": "error", "message": "Failed to save knowledge"})

@app.route('/search', methods=['POST'])
def search():
    query = request.json.get('query', '').strip()
    
    if not query:
        return jsonify({"status": "error", "message": "No query provided"})
    
    # Log search action
    log_action("search", f"Searched for: {query}")
    
    # First search knowledge base
    search_results = search_knowledge(query)
    
    if search_results:
        results = []
        for result in search_results:
            results.append({
                "question": result[0],
                "answer": result[1],
                "source": result[3]
            })
        return jsonify({"status": "success", "results": results})
    else:
        # Fall back to search engine
        result = perform_search(query)
        
        # Save the search result
        search_question = f"search: {query}"
        save_data(search_question, result, 0.5, "serpapi", "web_user")
        
        return jsonify({
            "status": "success", 
            "results": [{
                "question": query,
                "answer": result,
                "source": "serpapi"
            }]
        })

@app.route('/text-to-speech', methods=['POST'])
def generate_speech():
    """API endpoint to convert text to speech"""
    text = request.json.get('text', '').strip()
    voice_id = request.json.get('voice_id', '21m00Tcm4TlvDq8ikWAM')
    
    if not text:
        return jsonify({"status": "error", "message": "No text provided"})
    
    # Log TTS action
    log_action("text_to_speech", f"Generated speech for text: {text[:30]}...")
    
    try:
        # Generate speech using Eleven Labs API
        audio_base64 = text_to_speech(text, voice_id)
        
        if audio_base64:
            return jsonify({
                "status": "success",
                "audio_base64": audio_base64
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to generate speech"
            })
    except Exception as e:
        print(f"Error generating speech: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        })

@app.route('/voices', methods=['GET'])
def get_voices():
    """API endpoint to get available voices"""
    try:
        voices = get_available_voices()
        return jsonify({
            "status": "success",
            "voices": voices.get("voices", [])
        })
    except Exception as e:
        print(f"Error getting voices: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        })

@app.route('/dashboard-stats', methods=['GET'])
def get_dashboard_stats():
    """API endpoint to get dashboard statistics"""
    try:
        # Load data
        data = load_data()
        question_count = len(data.keys()) if data else 0
        
        # Build knowledge graph on-demand
        global knowledge_graph
        if not knowledge_graph.nodes:
            build_knowledge_graph()
        
        node_count = knowledge_graph.number_of_nodes()
        edge_count = knowledge_graph.number_of_edges()
        
        # Get recent activities
        activities = get_recent_activities(10)
        
        return jsonify({
            "status": "success",
            "question_count": question_count,
            "node_count": node_count,
            "edge_count": edge_count,
            "activities": activities
        })
    except Exception as e:
        print(f"Error getting dashboard stats: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        })

def get_recent_activities(limit=10):
    """Get recent activities from log"""
    try:
        with open('user_actions.json', 'r') as f:
            action_log = json.load(f)
            
        recent_actions = action_log.get("actions", [])[-limit:]
        
        activities = []
        for action in reversed(recent_actions):
            timestamp = action.get("timestamp", "").split("T")[0] + " " + action.get("timestamp", "").split("T")[1][:8]
            user = action.get("user", "unknown")
            action_type = action.get("action", "unknown")
            description = action.get("description", "")
            
            activities.append({
                "timestamp": timestamp,
                "user": user,
                "action": action_type,
                "description": description
            })
            
        return activities
    except Exception as e:
        print(f"Error loading activities: {e}")
        return []

def build_knowledge_graph():
    """Build knowledge graph from database"""
    global knowledge_graph
    knowledge_graph = nx.DiGraph()
    
    try:
        # Load data
        data = load_data()
        
        if not data:
            return
        
        # Extract entities and relationships
        for question, answers in data.items():
            # Add question node
            knowledge_graph.add_node(question, type="question")
            
            for answer_data in answers:
                answer = answer_data["answer"]
                source = answer_data["source"]
                
                # Process with spaCy to extract entities
                doc = nlp(answer)
                
                # Add entities as nodes
                for ent in doc.ents:
                    entity_text = ent.text
                    entity_type = ent.label_
                    
                    if not knowledge_graph.has_node(entity_text):
                        knowledge_graph.add_node(entity_text, type="entity", entity_type=entity_type)
                    
                    # Connect question to entity
                    knowledge_graph.add_edge(question, entity_text, relation="contains")
                    
                # Add source as node
                if not knowledge_graph.has_node(source):
                    knowledge_graph.add_node(source, type="source")
                
                # Connect question to source
                knowledge_graph.add_edge(question, source, relation="from")
    except Exception as e:
        print(f"Error building knowledge graph: {e}")

@app.route('/start-learning', methods=['POST'])
def start_continuous_learning():
    """API endpoint to start continuous learning"""
    try:
        # In a real implementation, you would start a background thread for learning
        # For this demo, we'll just log the action
        log_action("system", "learning_started", "Started continuous learning process")
        
        return jsonify({
            "status": "success",
            "message": "Continuous learning process started"
        })
    except Exception as e:
        print(f"Error starting learning: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        })

@app.route('/stop-learning', methods=['POST'])
def stop_continuous_learning():
    """API endpoint to stop continuous learning"""
    try:
        # In a real implementation, you would stop the background thread
        # For this demo, we'll just log the action
        log_action("system", "learning_stopped", "Stopped continuous learning process")
        
        return jsonify({
            "status": "success",
            "message": "Continuous learning process stopped"
        })
    except Exception as e:
        print(f"Error stopping learning: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        })

@app.route('/generate-report', methods=['POST'])
def generate_kb_report():
    """API endpoint to generate knowledge base report"""
    try:
        report_path = "knowledge_report.txt"
        
        # Collect data
        data = load_data()
        question_count = len(data.keys()) if data else 0
        
        # Build knowledge graph if needed
        global knowledge_graph
        if not knowledge_graph.nodes:
            build_knowledge_graph()
            
        node_count = knowledge_graph.number_of_nodes()
        edge_count = knowledge_graph.number_of_edges()
        
        # Get source counts
        conn, is_postgres = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT source, COUNT(*) FROM knowledge GROUP BY source")
        source_data = cursor.fetchall()
        release_connection(conn, is_postgres)
        
        # Write report
        with open(report_path, 'w') as f:
            f.write("Protype.AI Knowledge Base Report\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("Knowledge Base Stats:\n")
            f.write(f"- Total questions: {question_count}\n")
            f.write(f"- Knowledge graph nodes: {node_count}\n")
            f.write(f"- Knowledge graph connections: {edge_count}\n\n")
            
            f.write("Knowledge Sources:\n")
            for source, count in source_data:
                f.write(f"- {source}: {count} items\n")
                
            f.write("\nRecent Knowledge:\n")
            items_shown = 0
            for question, answers in data.items():
                if items_shown >= 10:
                    break
                f.write(f"Q: {question}\n")
                f.write(f"A: {answers[0]['answer'][:100]}...\n")
                f.write(f"Source: {answers[0]['source']}\n\n")
                items_shown += 1
        
        # Log report generation
        log_action("system", "report_generated", f"Generated knowledge report: {report_path}")
        
        return jsonify({
            "status": "success",
            "message": "Knowledge base report generated",
            "report_path": report_path
        })
    except Exception as e:
        print(f"Error generating report: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        })

# Initialize database
init_db()

# Build initial knowledge graph
build_knowledge_graph()

# Optimize server performance
if __name__ == '__main__':
    # Use production server with multiple workers for better performance
    import waitress
    
    # Enable logging
    import logging
    logger = logging.getLogger('waitress')
    logger.setLevel(logging.INFO)
    
    # Configure thread pool
    print("Starting Protype.AI server on http://0.0.0.0:8080")
    print("Loading database and models...")
    data = load_data()  # Pre-load data before server starts
    print(f"Loaded {len(data.keys() if data else [])} knowledge items")
    
    # Initialize database connection pool
    init_db()
    
    # Use waitress for production-ready performance
    waitress.serve(app, host='0.0.0.0', port=8080, threads=4, 
                  connection_limit=1000, 
                  channel_timeout=30)
