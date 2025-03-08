
import sys
import os
import pytest
import sqlite3
from unittest import mock

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database

@pytest.fixture
def setup_sqlite_db():
    """Setup a temporary SQLite database for testing"""
    # Use in-memory database for tests
    test_db_path = ":memory:"
    
    # Mock the get_connection function to use our test db
    original_get_connection = database.get_connection
    
    def mock_get_connection():
        return sqlite3.connect(test_db_path), False
    
    database.get_connection = mock_get_connection
    database.init_db()
    
    yield
    
    # Restore original function
    database.get_connection = original_get_connection

def test_init_db(setup_sqlite_db):
    """Test database initialization"""
    # This should just run without errors
    database.init_db()
    
    # Verify the table exists
    conn, _ = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='knowledge'")
    assert cursor.fetchone() is not None
    database.release_connection(conn, False)

def test_save_and_load_data(setup_sqlite_db):
    """Test saving and loading data"""
    # Save test data
    test_question = "What is the meaning of life?"
    test_answer = "42"
    assert database.save_data(test_question, test_answer, 0.5, "test", "test_user")
    
    # Load the data
    data = database.load_data()
    
    # Verify the data was saved correctly
    assert test_question in data
    assert len(data[test_question]) == 1
    assert data[test_question][0]["answer"] == test_answer
    assert data[test_question][0]["weight"] == 0.5
    assert data[test_question][0]["source"] == "test"

def test_update_existing_data(setup_sqlite_db):
    """Test updating existing data"""
    # Save initial data
    test_question = "What is Python?"
    test_answer1 = "A programming language"
    assert database.save_data(test_question, test_answer1, 0.5, "test", "user1")
    
    # Update the data
    test_answer2 = "A high-level programming language"
    assert database.save_data(test_question, test_answer2, 0.7, "test_updated", "user2")
    
    # Load and verify the updated data
    data = database.load_data()
    assert test_question in data
    assert len(data[test_question]) == 1  # Should still be one record
    assert data[test_question][0]["answer"] == test_answer2
    assert data[test_question][0]["weight"] == 0.7
    assert data[test_question][0]["source"] == "test_updated"

def test_get_knowledge_history(setup_sqlite_db):
    """Test getting version history"""
    # Save data
    test_question = "Who created Python?"
    test_answer = "Guido van Rossum"
    assert database.save_data(test_question, test_answer, 0.8, "wiki", "test_user")
    
    # Get history
    history = database.get_knowledge_history(test_question)
    
    # Verify history
    assert len(history) > 0
    assert history[0]["answer"] == test_answer
    assert history[0]["weight"] == 0.8
    assert history[0]["source"] == "wiki"
    assert "created_at" in history[0]
    assert history[0]["created_by"] == "test_user"

def test_search_knowledge(setup_sqlite_db):
    """Test knowledge search functionality"""
    # Save multiple data entries
    database.save_data("What is Python?", "A programming language", 0.8, "wiki", "user1")
    database.save_data("What is Java?", "Another programming language", 0.7, "wiki", "user1")
    database.save_data("What is C++?", "A systems programming language", 0.6, "wiki", "user1")
    
    # Test search
    results = database.search_knowledge("programming")
    
    # Verify results
    assert len(results) > 0
    # At least one result should contain "programming" in question or answer
    programming_found = False
    for result in results:
        if "programming" in result[0].lower() or "programming" in result[1].lower():
            programming_found = True
            break
    assert programming_found
