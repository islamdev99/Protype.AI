
import os
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError, NotFoundError
import database

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
        data = database.load_data()
        if not data:
            return False
            
        # Bulk index data
        bulk_data = []
        for question, answers in data.items():
            for answer_data in answers:
                # Get additional fields if available
                history = database.get_knowledge_history(question)
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
    """Perform advanced search using Elasticsearch with improved relevance"""
    if not HAS_ELASTICSEARCH or not es_client:
        # Fallback to database search if Elasticsearch is not available
        return database.search_knowledge(query, limit)
        
    try:
        response = es_client.search(
            index="knowledge",
            body={
                "size": limit,
                "min_score": min_score,
                "query": {
                    "bool": {
                        "should": [
                            {
                                "multi_match": {
                                    "query": query,
                                    "fields": ["question^4", "answer^2"],
                                    "type": "best_fields",
                                    "fuzziness": "AUTO",
                                    "boost": 1.5
                                }
                            },
                            {
                                "match_phrase": {
                                    "question": {
                                        "query": query,
                                        "boost": 2.0
                                    }
                                }
                            },
                            {
                                "match_phrase": {
                                    "answer": {
                                        "query": query,
                                        "boost": 1.0
                                    }
                                }
                            }
                        ]
                    }
                },
                "highlight": {
                    "fields": {
                        "question": {"fragment_size": 150, "number_of_fragments": 3},
                        "answer": {"fragment_size": 150, "number_of_fragments": 3}
                    }
                },
                "sort": [
                    "_score",
                    {"weight": {"order": "desc"}}
                ]
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
        return database.search_knowledge(query, limit)

# Initialize Elasticsearch
if HAS_ELASTICSEARCH:
    if init_elasticsearch():
        sync_database_to_elasticsearch()
