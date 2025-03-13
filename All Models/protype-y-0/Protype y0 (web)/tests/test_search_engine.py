
import sys
import os
import pytest
from unittest import mock

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import search_engine
import database

@pytest.fixture
def mock_elasticsearch():
    """Mock Elasticsearch for testing"""
    with mock.patch('search_engine.HAS_ELASTICSEARCH', True), \
         mock.patch('search_engine.es_client') as mock_es:
        # Setup mock responses
        mock_es.indices.exists.return_value = False
        mock_es.indices.create.return_value = {"acknowledged": True}
        mock_es.bulk.return_value = {"errors": False}
        mock_es.index.return_value = {"_id": "test_id", "result": "created"}
        
        # Mock search results
        mock_search_result = {
            "hits": {
                "total": {"value": 1},
                "hits": [
                    {
                        "_score": 0.8,
                        "_source": {
                            "question": "What is Python?",
                            "answer": "Python is a programming language.",
                            "weight": 0.7,
                            "source": "test"
                        },
                        "highlight": {
                            "question": ["What is <em>Python</em>?"],
                            "answer": ["<em>Python</em> is a programming language."]
                        }
                    }
                ]
            }
        }
        mock_es.search.return_value = mock_search_result
        
        yield mock_es

def test_init_elasticsearch(mock_elasticsearch):
    """Test Elasticsearch initialization"""
    assert search_engine.init_elasticsearch() is True
    mock_elasticsearch.indices.exists.assert_called_once_with(index="knowledge")
    mock_elasticsearch.indices.create.assert_called_once()

def test_sync_database_to_elasticsearch(mock_elasticsearch):
    """Test syncing database to Elasticsearch"""
    # Mock database.load_data to return test data
    test_data = {
        "What is Python?": [
            {
                "answer": "Python is a programming language.",
                "weight": 0.7,
                "source": "test"
            }
        ]
    }
    
    with mock.patch('database.load_data', return_value=test_data), \
         mock.patch('database.get_knowledge_history', return_value=[]):
        assert search_engine.sync_database_to_elasticsearch() is True
        mock_elasticsearch.bulk.assert_called_once()

def test_index_document(mock_elasticsearch):
    """Test indexing a single document"""
    assert search_engine.index_document(
        "What is Python?",
        "Python is a programming language.",
        0.7,
        "test"
    ) is True
    
    mock_elasticsearch.index.assert_called_once()

def test_search(mock_elasticsearch):
    """Test search functionality"""
    results = search_engine.search("Python")
    
    # Verify results
    assert len(results) == 1
    assert results[0]["question"] == "What is Python?"
    assert results[0]["answer"] == "Python is a programming language."
    assert results[0]["score"] == 0.8
    
    # Verify search call parameters
    mock_elasticsearch.search.assert_called_once()
    call_args = mock_elasticsearch.search.call_args[1]
    assert call_args["index"] == "knowledge"
    assert "query" in call_args["body"]
    assert "multi_match" in call_args["body"]["query"]
    assert call_args["body"]["query"]["multi_match"]["query"] == "Python"
