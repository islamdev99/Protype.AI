
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

# Initialize Flask application
app = Flask(__name__)
app.secret_key = os.urandom(24)

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

# Initialize database
init_db()

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
