
import os
import psycopg2
from psycopg2 import pool
import sqlite3

# Check if we're running in Replit with PostgreSQL available
USING_POSTGRES = 'DATABASE_URL' in os.environ

# Connection pool for PostgreSQL
pg_pool = None
if USING_POSTGRES:
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
    # For SQLite, first check if database is corrupted
    if not USING_POSTGRES:
        try:
            # Try to open the database to check if it's corrupted
            test_conn = sqlite3.connect(SQLITE_DB_PATH)
            test_conn.execute("PRAGMA integrity_check")
            test_conn.close()
        except sqlite3.DatabaseError as e:
            print(f"SQLite database corrupted: {e}")
            print("Recreating database...")
            try:
                # Remove corrupted database
                import os
                if os.path.exists(SQLITE_DB_PATH):
                    os.remove(SQLITE_DB_PATH)
                print(f"Removed corrupted database file: {SQLITE_DB_PATH}")
            except Exception as remove_err:
                print(f"Error removing corrupted database: {remove_err}")
    
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
        print("Database initialized successfully")
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

# Initialize database connection and schema
init_db()

# Try to migrate data if needed
if USING_POSTGRES:
    migrate_sqlite_to_postgres()
