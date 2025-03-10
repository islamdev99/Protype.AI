
import os
import sys

# Add local libraries to Python path
from lib_setup import *

from web_app import app
from database import init_db
from search_engine import HAS_ELASTICSEARCH, init_elasticsearch, sync_database_to_elasticsearch

# Initialize database
init_db()

# Initialize Elasticsearch if available
if HAS_ELASTICSEARCH:
    init_elasticsearch()
    sync_database_to_elasticsearch()

# Initialize web application
if __name__ == "__main__":
    # Use production server with multiple workers for better performance
    import waitress

    # Enable logging
    import logging
    logger = logging.getLogger('waitress')
    logger.setLevel(logging.INFO)

    # Configure thread pool
    print("Starting Protype.AI web server on http://0.0.0.0:8080")
    print("Loading database and models...")

    # Use waitress for production-ready performance
    waitress.serve(app, host='0.0.0.0', port=8080, threads=4, 
                  connection_limit=1000, 
                  channel_timeout=30)
