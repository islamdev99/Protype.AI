
import json
import os
import random
import re
import spacy
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import networkx as nx
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
import google.generativeai as genai
from bs4 import BeautifulSoup
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError, NotFoundError
import time
from celery import Celery
import sqlite3

# Configure Celery with Redis (if available) or use local memory broker
if 'REDIS_URL' in os.environ:
    broker_url = os.environ['REDIS_URL']
else:
    broker_url = 'memory://'

celery_app = Celery('protype_tasks', broker=broker_url)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    worker_concurrency=2
)

# -------------------------
# DATABASE MODULE
# -------------------------

# Check if we're running in Replit with PostgreSQL available
USING_POSTGRES = 'DATABASE_URL' in os.environ

# Connection pool for PostgreSQL
pg_pool = None
if USING_POSTGRES:
    import psycopg2
    from psycopg2 import pool
    database_url = os.environ['DATABASE_URL']
    # Use connection pooling for better performance
    pg_pool = pool.ThreadedConnectionPool(1, 20, database_url)

# For backward compatibility with SQLite
SQLITE_DB_PATH = 'protype_e0.db'

def get_connection():
    """Returns either a PostgreSQL or SQLite connection based on environment"""
    if USING_POSTGRES and pg_pool:
        return pg_pool.getconn(), True
    else:
        return sqlite3.connect(SQLITE_DB_PATH), False

def release_connection(conn, is_postgres):
    """Properly releases/closes the connection based on type"""
    if is_postgres and pg_pool:
        pg_pool.putconn(conn)
    else:
        conn.close()

def init_db():
    """Initialize database with required tables"""
    conn, is_postgres = get_connection()
    try:
        cursor = conn.cursor()
        
        if is_postgres:
            # PostgreSQL schema with version control fields
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS knowledge (
                    id SERIAL PRIMARY KEY,
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
            
            # Add trigger to update modified_at automatically
            cursor.execute('''
                CREATE OR REPLACE FUNCTION update_modified_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.modified_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ language 'plpgsql';
            ''')
            
            # Check if trigger exists before creating
            cursor.execute('''
                SELECT EXISTS (
                    SELECT 1 FROM pg_trigger WHERE tgname = 'update_knowledge_modtime'
                );
            ''')
            trigger_exists = cursor.fetchone()[0]
            
            if not trigger_exists:
                cursor.execute('''
                    CREATE TRIGGER update_knowledge_modtime
                    BEFORE UPDATE ON knowledge
                    FOR EACH ROW
                    EXECUTE FUNCTION update_modified_column();
                ''')
        else:
            # SQLite schema with version control fields
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

def migrate_sqlite_to_postgres():
    """Migrate data from SQLite to PostgreSQL if needed"""
    if not USING_POSTGRES or not pg_pool:
        return False
        
    # Connect to SQLite
    sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
    sqlite_cursor = sqlite_conn.cursor()
    
    # Check if SQLite has the knowledge table with data
    sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='knowledge'")
    if not sqlite_cursor.fetchone():
        sqlite_conn.close()
        return False
    
    # Get data from SQLite
    sqlite_cursor.execute("SELECT question, answer, weight, source FROM knowledge")
    rows = sqlite_cursor.fetchall()
    
    if not rows:
        sqlite_conn.close()
        return False
    
    # Connect to PostgreSQL
    pg_conn, _ = get_connection()
    pg_cursor = pg_conn.cursor()
    
    # Insert data into PostgreSQL
    try:
        for row in rows:
            question, answer, weight, source = row
            pg_cursor.execute('''
                INSERT INTO knowledge (question, answer, weight, source)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (question) DO NOTHING
            ''', (question, answer, weight, source))
        
        pg_conn.commit()
        print(f"Successfully migrated {len(rows)} records from SQLite to PostgreSQL")
        return True
    except Exception as e:
        pg_conn.rollback()
        print(f"Migration error: {e}")
        return False
    finally:
        sqlite_conn.close()
        release_connection(pg_conn, True)

def save_data(question, answer, weight, source, user="system"):
    """Save data to database with version control"""
    conn, is_postgres = get_connection()
    try:
        cursor = conn.cursor()
        
        if is_postgres:
            # Check if record exists
            cursor.execute("SELECT id FROM knowledge WHERE question = %s", (question,))
            record = cursor.fetchone()
            
            if record:
                # Update existing record
                cursor.execute(
                    "UPDATE knowledge SET answer = %s, weight = %s, source = %s, modified_by = %s WHERE question = %s",
                    (answer, weight, source, user, question)
                )
            else:
                # Insert new record
                cursor.execute(
                    "INSERT INTO knowledge (question, answer, weight, source, created_by, modified_by) VALUES (%s, %s, %s, %s, %s, %s)",
                    (question, answer, weight, source, user, user)
                )
        else:
            # SQLite doesn't support the same level of constraint handling
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
        
        # For PostgreSQL, use parameterized placeholders with %s
        placeholder = "%s" if is_postgres else "?"
        
        query = f"SELECT question, answer, weight, source FROM knowledge"
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

def get_knowledge_history(question):
    """Get version history for a specific knowledge item"""
    conn, is_postgres = get_connection()
    history = []
    
    try:
        cursor = conn.cursor()
        placeholder = "%s" if is_postgres else "?"
        
        # The actual implementation would depend on how you track history
        # This is a simplified version that just returns the current state
        query = f"SELECT answer, weight, source, created_at, created_by, modified_at, modified_by FROM knowledge WHERE question = {placeholder}"
        cursor.execute(query, (question,))
        
        row = cursor.fetchone()
        if row:
            answer, weight, source, created_at, created_by, modified_at, modified_by = row
            history.append({
                "answer": answer,
                "weight": weight,
                "source": source,
                "created_at": created_at,
                "created_by": created_by,
                "modified_at": modified_at,
                "modified_by": modified_by
            })
        
        return history
    except Exception as e:
        print(f"Error retrieving history: {e}")
        return []
    finally:
        release_connection(conn, is_postgres)

def search_knowledge(query, limit=10):
    """Advanced search function with ranking"""
    conn, is_postgres = get_connection()
    try:
        cursor = conn.cursor()
        
        if is_postgres:
            # Full-text search with PostgreSQL
            search_query = f"""
                SELECT question, answer, weight, source, 
                       ts_rank(to_tsvector('english', question || ' ' || answer), plainto_tsquery('english', %s)) AS rank
                FROM knowledge
                WHERE to_tsvector('english', question || ' ' || answer) @@ plainto_tsquery('english', %s)
                ORDER BY rank DESC
                LIMIT %s
            """
            cursor.execute(search_query, (query, query, limit))
        else:
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

# -------------------------
# SEARCH ENGINE MODULE
# -------------------------

# Check if Elasticsearch is available
HAS_ELASTICSEARCH = 'ELASTICSEARCH_URL' in os.environ

# Setup Elasticsearch client if available
es_client = None
if HAS_ELASTICSEARCH:
    es_url = os.environ.get('ELASTICSEARCH_URL')
    es_client = Elasticsearch(es_url)

def init_elasticsearch():
    """Initialize Elasticsearch index and mappings"""
    if not HAS_ELASTICSEARCH or not es_client:
        return False
        
    try:
        # Check if index exists
        if not es_client.indices.exists(index="knowledge"):
            # Create index with custom mappings
            es_client.indices.create(
                index="knowledge",
                body={
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 0,
                        "analysis": {
                            "analyzer": {
                                "custom_analyzer": {
                                    "type": "custom",
                                    "tokenizer": "standard",
                                    "filter": ["lowercase", "stop", "snowball"]
                                }
                            }
                        }
                    },
                    "mappings": {
                        "properties": {
                            "question": {
                                "type": "text",
                                "analyzer": "custom_analyzer",
                                "fields": {
                                    "keyword": {
                                        "type": "keyword"
                                    }
                                }
                            },
                            "answer": {
                                "type": "text",
                                "analyzer": "custom_analyzer"
                            },
                            "source": {
                                "type": "keyword"
                            },
                            "weight": {
                                "type": "float"
                            },
                            "created_at": {
                                "type": "date"
                            },
                            "modified_at": {
                                "type": "date"
                            }
                        }
                    }
                }
            )
        return True
    except Exception as e:
        print(f"Elasticsearch initialization error: {e}")
        return False

def sync_database_to_elasticsearch():
    """Sync all database records to Elasticsearch"""
    if not HAS_ELASTICSEARCH or not es_client:
        return False
        
    try:
        # Get all data from database
        data = load_data()
        if not data:
            return False
            
        # Bulk index data
        bulk_data = []
        for question, answers in data.items():
            for answer_data in answers:
                # Get additional fields if available
                history = get_knowledge_history(question)
                created_at = None
                created_by = None
                modified_at = None
                modified_by = None
                
                if history and len(history) > 0:
                    created_at = history[0].get('created_at')
                    created_by = history[0].get('created_by')
                    modified_at = history[0].get('modified_at')
                    modified_by = history[0].get('modified_by')
                
                # Add index action
                bulk_data.append({"index": {"_index": "knowledge"}})
                
                # Add document
                doc = {
                    "question": question,
                    "answer": answer_data["answer"],
                    "weight": answer_data["weight"],
                    "source": answer_data["source"]
                }
                
                # Add version control fields if available
                if created_at:
                    doc["created_at"] = created_at
                if created_by:
                    doc["created_by"] = created_by
                if modified_at:
                    doc["modified_at"] = modified_at
                if modified_by:
                    doc["modified_by"] = modified_by
                    
                bulk_data.append(doc)
                
        if bulk_data:
            es_client.bulk(body=bulk_data, refresh=True)
            return True
        return False
    except Exception as e:
        print(f"Elasticsearch sync error: {e}")
        return False

def index_document(question, answer, weight, source, created_at=None, modified_at=None, created_by=None, modified_by=None):
    """Index a single document in Elasticsearch"""
    if not HAS_ELASTICSEARCH or not es_client:
        return False
        
    try:
        doc = {
            "question": question,
            "answer": answer,
            "weight": weight,
            "source": source
        }
        
        # Add version control fields if available
        if created_at:
            doc["created_at"] = created_at
        if created_by:
            doc["created_by"] = created_by
        if modified_at:
            doc["modified_at"] = modified_at
        if modified_by:
            doc["modified_by"] = modified_by
            
        es_client.index(index="knowledge", body=doc, refresh=True)
        return True
    except Exception as e:
        print(f"Elasticsearch indexing error: {e}")
        return False

def search(query, limit=10, min_score=0.1):
    """Perform advanced search using Elasticsearch"""
    if not HAS_ELASTICSEARCH or not es_client:
        # Fallback to database search if Elasticsearch is not available
        return search_knowledge(query, limit)
        
    try:
        response = es_client.search(
            index="knowledge",
            body={
                "size": limit,
                "min_score": min_score,
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["question^3", "answer^2"],
                        "type": "best_fields",
                        "fuzziness": "AUTO"
                    }
                },
                "highlight": {
                    "fields": {
                        "question": {},
                        "answer": {}
                    }
                }
            }
        )
        
        results = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            highlight = hit.get("highlight", {})
            
            # Get highlighted snippets or use original text
            question = highlight.get("question", [source["question"]])[0]
            answer_highlights = highlight.get("answer", [])
            answer_snippet = answer_highlights[0] if answer_highlights else source["answer"][:150] + "..."
            
            results.append({
                "question": source["question"],
                "answer": source["answer"],
                "answer_snippet": answer_snippet,
                "weight": source["weight"],
                "source": source["source"],
                "score": hit["_score"]
            })
            
        return results
    except Exception as e:
        print(f"Elasticsearch search error: {e}")
        # Fallback to database search
        return search_knowledge(query, limit)

# -------------------------
# CELERY TASKS MODULE
# -------------------------

@celery_app.task
def learn_from_wikipedia(topic):
    """Task to learn from Wikipedia in the background"""
    try:
        content = get_wikipedia_content(topic)
        if content:
            question = generate_question(topic)
            answer = f"According to Wikipedia under CC BY-SA 3.0:\n{content}"
            save_data(question, answer, 0.6, "wikipedia", "celery_worker")
            return {"status": "success", "topic": topic, "question": question}
        return {"status": "error", "topic": topic, "reason": "No content found"}
    except Exception as e:
        return {"status": "error", "topic": topic, "reason": str(e)}

@celery_app.task
def batch_wikipedia_learning(topics):
    """Process multiple Wikipedia topics in a batch"""
    results = []
    for topic in topics:
        result = learn_from_wikipedia.delay(topic)
        results.append(result.id)
    return results

@celery_app.task
def learn_from_external_ai(question):
    """Task to get answer from external AI API"""
    try:
        ai_response = query_external_ai(question)
        if save_data(question, ai_response, 0.6, "external_ai", "celery_worker"):
            return {"status": "success", "question": question, "answer_snippet": ai_response[:50]}
        return {"status": "error", "question": question, "reason": "Failed to save data"}
    except Exception as e:
        return {"status": "error", "question": question, "reason": str(e)}

@celery_app.task
def learn_from_gemini_flash(question):
    """Task to get answer from Gemini Flash API"""
    try:
        gemini_response = query_gemini_flash(question)
        if save_data(question, gemini_response, 0.6, "gemini_flash_2", "celery_worker"):
            return {"status": "success", "question": question, "answer_snippet": gemini_response[:50]}
        return {"status": "error", "question": question, "reason": "Failed to save data"}
    except Exception as e:
        return {"status": "error", "question": question, "reason": str(e)}

# -------------------------
# HELPER FUNCTIONS
# -------------------------

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
        print("Please run 'python -m spacy download en_core_web_sm' manually")
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

def clean_text(text):
    """Clean Wikipedia text"""
    return re.sub(r'\[.*?\]|\{.*?\}|\<.*?\>', '', text).strip()

def get_wikipedia_content(topic):
    """Get content from Wikipedia with error handling and retries"""
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            response = requests.get(
                f"https://en.wikipedia.org/wiki/{topic}",
                headers={'User-Agent': 'ProtypeAI/1.0'},
                timeout=10
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            paragraphs = soup.find_all('p')
            content = ""
            line_count = 0
            
            for p in paragraphs:
                text = clean_text(p.get_text())
                if text and len(text) > 10:
                    content += text + "\n"
                    line_count += text.count('\n') + 1
                    if line_count >= 200:
                        break
                        
            return content if content else None
            
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                raise Exception(f"Failed to fetch Wikipedia content after {max_retries} attempts: {e}")

def generate_question(topic):
    """Generate a question about a topic"""
    question_types = [
        f"What is {topic}?", 
        f"How does {topic} work?",
        f"Why is {topic} important?", 
        f"Who discovered {topic}?",
        f"What are the benefits of {topic}?",
        f"How is {topic} used today?", 
        f"Why did {topic} become popular?",
        f"Who contributed to {topic}?"
    ]
    return random.choice(question_types)

# Function to perform Google search using SerpAPI
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

# Function to query external AI API
def query_external_ai(query):
    try:
        url = "https://api.aimlapi.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {os.environ.get('AIMLAPI_KEY', '753aa08c2b8344f38ff8bce052c0bec3')}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [{
                "role": "user",
                "content": query
            }],
            "max_tokens": 150
        }
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"Error querying external AI: {e}")
        return f"Failed to get response from external AI: {e}"

# Function to query Gemini Flash 2
def query_gemini_flash(question):
    try:
        response = chat_session.send_message(question)
        return response.text.strip()
    except Exception as e:
        print(f"Error querying Gemini Flash 2: {e}")
        return f"Failed to get response from Gemini Flash 2: {e}"

# Machine Learning model for question classification
training_data = [
    ("what is physics", "definition"),
    ("how does tennis work", "process"),
    ("why is messi important", "reason"),
    ("who discovered gravity", "person"),
    ("explain the concept of", "definition"),
    ("how can I", "process"),
    ("why should we", "reason"),
    ("which person was", "person")
]
questions, labels = zip(*training_data)
model = make_pipeline(TfidfVectorizer(), MultinomialNB())
model.fit(questions, labels)

def analyze_question_ml(question):
    return model.predict([question.lower().strip()])[0]

# -------------------------
# GUI APPLICATION
# -------------------------

class ProtypeAIApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Protype.AI - Developed by Islam Ibrahim")
        self.root.geometry("900x700")
        self.root.configure(bg="#e8f1f5")

        # Initialize database
        init_db()
        self.data = load_data()
        self.knowledge_graph = nx.DiGraph()
        self.load_knowledge_graph()

        # Initialize logger
        self.setup_logger()

        # Response templates
        self.response_templates = {
            "definition": "Here's the definition: ",
            "process": "Let me explain how it works: ",
            "reason": "Here's why: ",
            "person": "Here's who: ",
            "general": "Here's what I know: "
        }

        # Style Configuration
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton",
                        font=("Arial", 10, "bold"),
                        padding=8,
                        background="#4CAF50",
                        foreground="white")
        style.map("TButton", background=[("active", "#45a049")])
        style.configure("TLabel",
                        font=("Arial", 12),
                        background="#e8f1f5",
                        foreground="#333333")
        style.configure("TNotebook",
                        background="#e8f1f5",
                        tabmargins=[5, 5, 5, 0])
        style.configure("TNotebook.Tab",
                        font=("Arial", 11, "bold"),
                        padding=[10, 5])

        # Notebook (Tabs)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(pady=15, padx=15, fill="both", expand=True)

        # Teach Tab
        self.teach_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.teach_frame, text="Teach Protype")
        self.setup_teach_tab()

        # Search Tab
        self.search_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.search_frame, text="Search & Learn")
        self.setup_search_tab()

        # Chat Tab
        self.chat_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.chat_frame, text="Chat with Protype")
        self.setup_chat_tab()
        
        # Dashboard Tab (New)
        self.dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.dashboard_frame, text="Dashboard")
        self.setup_dashboard_tab()

        # Start continuous learning
        self.start_continuous_learning()
        
        # Log startup
        self.log_action("system", "application_start", "Protype.AI started successfully")

    def setup_logger(self):
        """Set up logger for tracking actions"""
        try:
            with open('user_actions.json', 'r') as f:
                self.action_log = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.action_log = {
                "version": "1.0",
                "actions": []
            }
    
    def log_action(self, user, action_type, description, details=None):
        """Log user actions for analytics"""
        import datetime
        
        action = {
            "timestamp": datetime.datetime.now().isoformat(),
            "user": user,
            "action": action_type,
            "description": description
        }
        
        if details:
            action["details"] = details
            
        self.action_log["actions"].append(action)
        
        # Save periodically (could optimize to save less frequently)
        try:
            with open('user_actions.json', 'w') as f:
                json.dump(self.action_log, f, indent=2)
        except Exception as e:
            print(f"Error saving action log: {e}")

    def load_knowledge_graph(self):
        """Load and build knowledge graph from database"""
        self.data = load_data()
        for question, answers in self.data.items():
            for answer_data in answers:
                answer = answer_data["answer"]
                doc = nlp(question.lower() + " " + answer.lower())
                entities = [ent.text for ent in doc.ents]
                self.knowledge_graph.add_node(question, type="question")
                self.knowledge_graph.add_node(answer, type="answer")
                self.knowledge_graph.add_edge(question,
                                              answer,
                                              weight=answer_data["weight"])
                for entity in entities:
                    self.knowledge_graph.add_node(entity, type="entity")
                    self.knowledge_graph.add_edge(question,
                                                  entity,
                                                  relation="mentions")
                    self.knowledge_graph.add_edge(answer,
                                                  entity,
                                                  relation="mentions")

    def setup_teach_tab(self):
        """Setup the teaching interface"""
        ttk.Label(self.teach_frame,
                  text="Teach Protype Something New!",
                  font=("Arial", 16, "bold"),
                  foreground="#0288d1").pack(pady=10)

        ttk.Label(self.teach_frame, text="What's your question?").pack(pady=5)
        self.teach_question = ttk.Entry(self.teach_frame,
                                        width=70,
                                        font=("Arial", 11))
        self.teach_question.pack()

        ttk.Label(self.teach_frame, text="What's the answer?").pack(pady=5)
        self.teach_answer = ttk.Entry(self.teach_frame,
                                      width=70,
                                      font=("Arial", 11))
        self.teach_answer.pack()

        self.teach_output = tk.Text(self.teach_frame,
                                    height=12,
                                    width=80,
                                    bg="#ffffff",
                                    fg="#333333",
                                    font=("Arial", 10),
                                    relief="flat",
                                    borderwidth=2)
        self.teach_output.pack(pady=15)
        self.teach_output.insert(
            tk.END,
            "Hey there! Teach me something cool by entering a question and answer!\n"
        )

        btn_frame = ttk.Frame(self.teach_frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame,
                   text="Teach Me",
                   command=self.process_teach_input).grid(row=0,
                                                          column=0,
                                                          padx=5)
        ttk.Button(btn_frame,
                   text="Clear",
                   command=lambda: self.teach_output.delete(1.0, tk.END)).grid(
                       row=0, column=1, padx=5)

    def setup_search_tab(self):
        """Setup the search interface"""
        ttk.Label(self.search_frame,
                  text="Search & Learn with Protype!",
                  font=("Arial", 16, "bold"),
                  foreground="#0288d1").pack(pady=10)

        ttk.Label(self.search_frame,
                  text="What do you want to search for?").pack(pady=5)
        self.search_query = ttk.Entry(self.search_frame,
                                      width=70,
                                      font=("Arial", 11))
        self.search_query.pack()

        self.search_output = tk.Text(self.search_frame,
                                     height=12,
                                     width=80,
                                     bg="#ffffff",
                                     fg="#333333",
                                     font=("Arial", 10),
                                     relief="flat",
                                     borderwidth=2)
        self.search_output.pack(pady=15)
        self.search_output.insert(
            tk.END, "Enter a search query, and I'll fetch something useful!\n")

        btn_frame = ttk.Frame(self.search_frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Search",
                   command=self.process_search_input).grid(row=0,
                                                           column=0,
                                                           padx=5)
        ttk.Button(
            btn_frame,
            text="Clear",
            command=lambda: self.search_output.delete(1.0, tk.END)).grid(
                row=0, column=1, padx=5)

    def setup_chat_tab(self):
        """Setup the chat interface"""
        ttk.Label(self.chat_frame,
                  text="Chat with Protype.AI!",
                  font=("Arial", 16, "bold"),
                  foreground="#0288d1").pack(pady=10)

        self.chat_output = tk.Text(self.chat_frame,
                                   height=15,
                                   width=80,
                                   bg="#ffffff",
                                   fg="#333333",
                                   font=("Arial", 10),
                                   relief="flat",
                                   borderwidth=2)
        self.chat_output.pack(pady=15)
        self.chat_output.insert(
            tk.END, "Hello! I'm Protype.AI, ready to help. Ask me anything!\n")

        ttk.Label(self.chat_frame, text="Ask me something:").pack()
        self.chat_question = ttk.Entry(self.chat_frame,
                                       width=70,
                                       font=("Arial", 11))
        self.chat_question.pack(pady=5)

        btn_frame = ttk.Frame(self.chat_frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Ask Me",
                   command=self.process_chat_input).grid(row=0,
                                                         column=0,
                                                         padx=5)
        ttk.Button(btn_frame,
                   text="Clear Chat",
                   command=lambda: self.chat_output.delete(1.0, tk.END)).grid(
                       row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="Exit",
                   command=self.exit_app).grid(row=0, column=2, padx=5)
                   
    def setup_dashboard_tab(self):
        """Setup the dashboard interface with advanced visualizations"""
        # Import the dashboard module
        import dashboard
        
        # Create and initialize the dashboard
        self.dashboard = dashboard.Dashboard(self.dashboard_frame, self.knowledge_graph)

    def update_kb_stats(self):
        """Update knowledge base statistics"""
        self.kb_stats_text.delete(1.0, tk.END)
        
        # Count items in database
        question_count = len(self.data.keys()) if self.data else 0
        
        # Get node and edge counts from knowledge graph
        node_count = self.knowledge_graph.number_of_nodes()
        edge_count = self.knowledge_graph.number_of_edges()
        
        stats = (
            f"Questions: {question_count}\n"
            f"Knowledge Graph Nodes: {node_count}\n"
            f"Knowledge Graph Connections: {edge_count}\n"
        )
        
        self.kb_stats_text.insert(tk.END, stats)
        
    def update_activity_log(self):
        """Update activity log display"""
        self.activity_text.delete(1.0, tk.END)
        
        # Get recent actions (last 10)
        recent_actions = self.action_log.get("actions", [])[-10:]
        
        if not recent_actions:
            self.activity_text.insert(tk.END, "No activity recorded yet.")
            return
            
        for action in reversed(recent_actions):
            timestamp = action.get("timestamp", "").split("T")[0]
            time = action.get("timestamp", "").split("T")[1][:8]
            user = action.get("user", "unknown")
            action_type = action.get("action", "unknown")
            description = action.get("description", "")
            
            entry = f"[{timestamp} {time}] {user}: {action_type} - {description}\n"
            self.activity_text.insert(tk.END, entry)
            
    def refresh_dashboard(self):
        """Refresh all dashboard elements"""
        self.update_kb_stats()
        self.update_activity_log()
        
    def sync_elasticsearch(self):
        """Sync database to Elasticsearch"""
        if not HAS_ELASTICSEARCH:
            messagebox.showinfo("Elasticsearch", "Elasticsearch is not configured.")
            return
            
        if sync_database_to_elasticsearch():
            messagebox.showinfo("Sync Complete", "Knowledge base synced to Elasticsearch successfully!")
            self.log_action("system", "elasticsearch_sync", "Database synced to Elasticsearch")
        else:
            messagebox.showerror("Sync Failed", "Failed to sync with Elasticsearch.")
            
    def start_rapid_learning(self):
        """Start rapid continuous learning (every 5 seconds)"""
        try:
            from learning_manager import learning_manager
            learning_manager.start_learning()
            messagebox.showinfo("Learning Started", 
                                "Continuous learning started (every 5 seconds)")
            self.log_action("system", "rapid_learning_start", 
                            "Started rapid continuous learning (5s interval)")
        except Exception as e:
            messagebox.showerror("Learning Failed", f"Failed to start learning: {e}")
            
    def stop_learning(self):
        """Stop continuous learning"""
        try:
            from learning_manager import learning_manager
            learning_manager.stop_learning()
            messagebox.showinfo("Learning Stopped", 
                                "Continuous learning has been stopped")
            self.log_action("system", "learning_stop", 
                            "Stopped continuous learning")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop learning: {e}")
            
    def trigger_batch_learning(self):
        """Trigger batch Wikipedia learning"""
        topics = [
            "Artificial_intelligence", "Machine_learning", "Deep_learning",
            "Natural_language_processing", "Computer_vision", "Robotics"
        ]
        try:
            result = batch_wikipedia_learning.delay(topics)
            messagebox.showinfo("Batch Learning Started", 
                                f"Batch learning started for {len(topics)} topics.")
            self.log_action("system", "batch_learning", 
                            f"Started learning {len(topics)} topics", 
                            {"task_id": str(result), "topics": topics})
        except Exception as e:
            messagebox.showerror("Learning Failed", f"Failed to start learning: {e}")

    def process_teach_input(self):
        """Process input from teach tab"""
        question = self.teach_question.get().strip()
        answer = self.teach_answer.get().strip()

        if not question or not answer:
            messagebox.showwarning(
                "Oops!", "Please fill in both the question and answer!")
            return

        self.teach_output.delete(1.0, tk.END)
        if save_data(question, answer, 0.5, "user", "user"):
            self.teach_output.insert(
                tk.END,
                f"Thanks! I've learned: '{question}' -> '{answer}'\nSaved successfully!\n"
            )
            
            # Log the action
            self.log_action("user", "teach", f"Added new knowledge: {question}")
            
            # Update knowledge graph
            self.load_knowledge_graph()
            
            # Index in Elasticsearch if available
            if HAS_ELASTICSEARCH:
                index_document(question, answer, 0.5, "user")
        else:
            self.teach_output.insert(
                tk.END,
                "Uh-oh! Something went wrong while saving. Try again?\n"
            )

        self.teach_question.delete(0, tk.END)
        self.teach_answer.delete(0, tk.END)

    def process_search_input(self):
        """Process input from search tab"""
        query = self.search_query.get().strip()
        if not query:
            messagebox.showwarning("Oops!",
                                   "Please enter something to search for!")
            return

        self.search_output.delete(1.0, tk.END)
        self.search_output.insert(tk.END, f"Searching for '{query}'...\n")
        
        # Log the search action
        self.log_action("user", "search", f"Searched for: {query}")
        
        # First try Elasticsearch
        if HAS_ELASTICSEARCH:
            search_results = search(query)
            if search_results:
                self.search_output.insert(tk.END, "Found in knowledge base:\n")
                for result in search_results:
                    if isinstance(result, dict):  # Elasticsearch result format
                        self.search_output.insert(tk.END, f"Q: {result['question']}\n")
                        self.search_output.insert(tk.END, f"A: {result['answer_snippet']}\n\n")
                    else:  # Database result format (fallback)
                        self.search_output.insert(tk.END, f"Q: {result[0]}\n")
                        self.search_output.insert(tk.END, f"A: {result[1][:150]}...\n\n")
                return
                
        # Fall back to Google search
        result = perform_search(query)
        self.search_output.insert(tk.END, f"Here's what I found online: {result}\n")

        search_question = f"search: {query}"
        if save_data(search_question, result, 0.5, "serpapi", "user"):
            self.search_output.insert(tk.END,
                                      "Knowledge saved successfully!\n")
            self.load_knowledge_graph()
            
            # Index in Elasticsearch if available
            if HAS_ELASTICSEARCH:
                index_document(search_question, result, 0.5, "serpapi")
        else:
            self.search_output.insert(
                tk.END, "Failed to save the knowledge. Please try again!\n")

        self.search_query.delete(0, tk.END)

    def process_chat_input(self):
        """Process input from chat tab"""
        question = self.chat_question.get().strip()
        if not question:
            messagebox.showwarning("Oops!", "Please ask me something!")
            return

        self.chat_output.insert(tk.END, f"You: {question}\n")
        
        # Log the chat action
        self.log_action("user", "chat", f"Asked: {question}")
        
        # Analyze question type
        question_type = analyze_question_ml(question)
        doc = nlp(question.lower())

        # First try Elasticsearch search
        if HAS_ELASTICSEARCH:
            search_results = search(question, limit=1)
            if search_results:
                result = search_results[0]
                if isinstance(result, dict):  # Elasticsearch result format
                    prefix = self.response_templates.get(question_type, "Here's what I know: ")
                    self.chat_output.insert(tk.END, f"Protype: {prefix}{result['answer']}\n")
                    self.chat_question.delete(0, tk.END)
                    return

        # Search Knowledge Graph with NLP similarity
        best_match = None
        max_similarity = 0.0
        for node in self.knowledge_graph.nodes:
            if self.knowledge_graph.nodes[node].get("type") == "question":
                node_doc = nlp(node.lower())
                similarity = doc.similarity(node_doc)
                if similarity > max_similarity and similarity > 0.7:
                    max_similarity = similarity
                    best_match = node

        if best_match:
            answers = sorted(self.data[best_match],
                             key=lambda x: x["weight"],
                             reverse=True)
            answer = answers[0]["answer"]
            prefix = self.response_templates.get(question_type,
                                                 "Here's what I know: ")
            self.chat_output.insert(tk.END, f"Protype: {prefix}{answer}\n")
        else:
            self.chat_output.insert(
                tk.END, "Protype: I'm learning about this topic. Please wait...\n")
            
            # First check if we can use Elasticsearch for a quicker response
            if HAS_ELASTICSEARCH:
                self.chat_output.insert(tk.END, "Searching my knowledge base...\n")
            
            # Use Gemini Flash in a separate thread to avoid UI freezing
            threading.Thread(target=self.learn_from_gemini_flash,
                             args=(question, ),
                             daemon=True).start()

        # Suggest related questions
        suggestions = self.suggest_related_questions(question)
        if suggestions:
            self.chat_output.insert(tk.END,
                                    "Related questions you might like:\n")
            for sug in suggestions:
                self.chat_output.insert(tk.END, f"- {sug}\n")

        self.chat_question.delete(0, tk.END)

    def suggest_related_questions(self, question):
        """Find related questions from knowledge graph"""
        doc = nlp(question.lower())
        suggestions = []
        for node in self.knowledge_graph.nodes:
            if self.knowledge_graph.nodes[node].get(
                    "type") == "question" and node != question:
                node_doc = nlp(node.lower())
                if doc.similarity(node_doc) > 0.8:
                    suggestions.append(node)
        return suggestions[:3]

    def learn_from_gemini_flash(self, question):
        """Learn from Gemini Flash in the background"""
        try:
            gemini_response = query_gemini_flash(question)
            
            # Update UI from the main thread
            self.root.after(0, lambda: self.update_chat_with_ai_response(question, gemini_response))
            
            # Save the knowledge
            if save_data(question, gemini_response, 0.6, "gemini_flash_2", "gemini"):
                self.load_knowledge_graph()
                
                # Log the learning action
                self.log_action("gemini", "learn", f"Learned from Gemini: {question[:30]}...")
                
                # Index in Elasticsearch if available
                if HAS_ELASTICSEARCH:
                    index_document(question, gemini_response, 0.6, "gemini_flash_2")
                
                self.root.after(0, lambda: self.chat_output.insert(
                    tk.END, "I've learned this and saved it for next time!\n"))
            else:
                self.root.after(0, lambda: self.chat_output.insert(
                    tk.END, "Failed to save the new knowledge.\n"))
                    
        except Exception as e:
            print(f"Error learning from Gemini: {e}")
            # Update UI with error
            self.root.after(0, lambda: self.chat_output.insert(
                tk.END, f"Protype: Sorry, I encountered an error while learning: {e}\n"))
    
    def update_chat_with_ai_response(self, question, response):
        """Update chat with AI response (called from main thread)"""
        self.chat_output.insert(tk.END, f"Protype: {response}\n")
        self.chat_output.insert(tk.END, "I've learned this for next time!\n")

    def exit_app(self):
        """Clean exit from application"""
        if messagebox.askyesno("Exit",
                               "Are you sure you want to leave Protype.AI?"):
            # Log the exit action
            self.log_action("user", "application_exit", "User exited the application")
            self.root.quit()

    def clean_text(self, text):
        """Clean Wikipedia text"""
        return re.sub(r'\[.*?\]|\{.*?\}|\<.*?\>', '', text).strip()

    def learn_topic(self, topic, index):
        """Learn from a topic (now using Celery)"""
        try:
            # Instead of processing directly, use Celery task
            learn_from_wikipedia.delay(topic)
            
            # Log background learning
            self.log_action("system", "background_learn", f"Learning about: {topic}")
        except Exception as e:
            print(f"Error scheduling learning task: {e}")

        topics = [
            "Lionel_Messi", "Football", "FIFA_World_Cup", "Olympics",
            "Physics", "Newton's_laws_of_motion", "Gravity",
            "Albert_Einstein", "Relativity", "Quantum_mechanics", 
            "DNA", "Genetics", "Charles_Darwin", "Evolution", 
            "Mathematics", "Algebra", "Calculus", "Isaac_Newton", 
            "Artificial_intelligence", "Machine_learning",
            "Deep_learning", "World_Wide_Web", "Python_(programming_language)",
            "Leonardo_da_Vinci", "Music", "Beethoven", 
            "William_Shakespeare", "Philosophy", "Socrates", 
            "Psychology", "Neuroscience", "Space_exploration", 
            "Black_hole", "Climate_change", "Renewable_energy"
        ]
        next_index = (index + 1) % len(topics)
        threading.Timer(30.0,  # Reduced frequency to prevent overloading
                        self.learn_topic,
                        args=(topics[next_index], next_index)).start()

    def start_continuous_learning(self):
        """Start continuous learning in background"""
        # Import learning manager here to avoid circular imports
        from learning_manager import learning_manager
        learning_manager.start_learning()


# Start the application
if __name__ == "__main__":
    # Initialize database
    init_db()
    
    # Initialize Elasticsearch if available
    if HAS_ELASTICSEARCH:
        init_elasticsearch()
        sync_database_to_elasticsearch()
    
    # Import the modern interface
    from modern_interface import ModernChatInterface
    
    # Start the GUI with modern interface
    root = tk.Tk()
    
    # Set up callback functions
    def process_message(message):
        """Process user message and get AI response"""
        # Get question type
        question_type = analyze_question_ml(message)
        
        # Try Elasticsearch search
        response = None
        if HAS_ELASTICSEARCH:
            search_results = search(message, limit=1)
            if search_results:
                result = search_results[0]
                if isinstance(result, dict):  # Elasticsearch result format
                    prefix = app.response_templates.get(question_type, "Here's what I know: ")
                    response = f"{prefix}{result['answer']}"
        
        # If no response yet, search knowledge graph
        if not response:
            doc = nlp(message.lower())
            best_match = None
            max_similarity = 0.0
            
            for node in app.knowledge_graph.nodes:
                if app.knowledge_graph.nodes[node].get("type") == "question":
                    node_doc = nlp(node.lower())
                    similarity = doc.similarity(node_doc)
                    if similarity > max_similarity and similarity > 0.7:
                        max_similarity = similarity
                        best_match = node
            
            if best_match:
                answers = sorted(app.data[best_match],
                                key=lambda x: x["weight"],
                                reverse=True)
                answer = answers[0]["answer"]
                prefix = app.response_templates.get(question_type, "Here's what I know: ")
                response = f"{prefix}{answer}"
        
        # If still no response, use Gemini Flash
        if not response:
            # Show a loading message
            interface.add_message("Protype.AI", "I'm thinking about this...", "ai")
            
            # Start a thread to get response from Gemini
            threading.Thread(
                target=lambda: learn_from_gemini_and_update(message, interface),
                daemon=True
            ).start()
            return
        
        # Add response to chat
        interface.add_message("Protype.AI", response, "ai")
        
        # Log the action
        app.log_action("user", "chat", f"Asked: {message}")
    
    def learn_from_gemini_and_update(question, interface):
        """Learn from Gemini and update the interface"""
        try:
            gemini_response = query_gemini_flash(question)
            
            # Update the interface from the main thread
            root.after(0, lambda: interface.add_message("Protype.AI", gemini_response, "ai"))
            
            # Save the knowledge
            if save_data(question, gemini_response, 0.6, "gemini_flash_2", "gemini"):
                app.load_knowledge_graph()
                app.log_action("gemini", "learn", f"Learned from Gemini: {question[:30]}...")
                
                # Index in Elasticsearch if available
                if HAS_ELASTICSEARCH:
                    index_document(question, gemini_response, 0.6, "gemini_flash_2")
        except Exception as e:
            print(f"Error learning from Gemini: {e}")
            # Update UI with error
            root.after(0, lambda: interface.add_message(
                "Protype.AI", f"Sorry, I encountered an error while learning: {e}", "ai"))
    
    def show_dashboard():
        """Show dashboard in a new window"""
        dashboard_window = tk.Toplevel(root)
        dashboard_window.title("Protype.AI Dashboard")
        dashboard_window.geometry("900x700")
        
        # Import dashboard module and create instance
        import dashboard
        dash = dashboard.Dashboard(dashboard_window, app.knowledge_graph)
    
    # Set up callback functions for the interface
    callbacks = {
        'process_message': process_message,
        'show_dashboard': show_dashboard
    }
    
    # Create app for backend operations
    app = ProtypeAIApp(root)
    
    # Hide the default UI
    app.root.withdraw()
    
    # Create the modern interface
    modern_root = tk.Toplevel(root)
    interface = ModernChatInterface(modern_root, callbacks)
    
    # Configure window close to exit the application
    def on_close():
        app.exit_app()
        root.quit()
    
    modern_root.protocol("WM_DELETE_WINDOW", on_close)
    
    # Start the main loop
    root.mainloop()
