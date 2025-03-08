# Database module for Protype.AI
import sqlite3
import time
import os
import json
from datetime import datetime

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
        # Log the learning action
        log_learning("knowledge_added", {
            "question": question[:50] + "..." if len(question) > 50 else question,
            "source": source,
            "added_by": user
        })
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

def log_learning(action, details):
    """Log learning activities"""
    try:
        # Load existing log
        try:
            with open('learning_logs.json', 'r') as f:
                logs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logs = {"logs": []}

        # Add new log entry
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details
        }

        logs["logs"].append(log_entry)

        # Save log
        with open('learning_logs.json', 'w') as f:
            json.dump(logs, f, indent=2)
    except Exception as e:
        print(f"Error logging learning activity: {e}")

def get_knowledge_by_source(source, limit=100):
    """Get knowledge entries by source"""
    conn, is_postgres = get_connection()
    try:
        cursor = conn.cursor()

        query = """
            SELECT question, answer, weight, source 
            FROM knowledge 
            WHERE source = ?
            LIMIT ?
        """
        cursor.execute(query, (source, limit))

        results = cursor.fetchall()
        return results
    except Exception as e:
        print(f"Error getting knowledge by source: {e}")
        return []
    finally:
        release_connection(conn, is_postgres)

# Initialize database connection and schema
init_db()