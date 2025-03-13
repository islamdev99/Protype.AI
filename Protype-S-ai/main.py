
import os
from web_app import app
from database import init_db
import threading
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('protype_ai')

# Initialize database
try:
    init_db()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Error initializing database: {e}")

try:
    # Initialize enhanced AI components
    from symbolic_reasoning import symbolic_reasoning
    from temporal_awareness import temporal_awareness
    from self_reflection import self_reflection
    from advanced_memory import advanced_memory
    from autonomous_agent import autonomous_agent
    from learning_manager import learning_manager

    # Start the continuous learning process in a separate thread
    def start_learning_thread():
        logger.info("Starting continuous learning processes...")
        try:
            learning_manager.start_learning()
        except Exception as e:
            logger.error(f"Error starting learning: {e}")

    learning_thread = threading.Thread(target=start_learning_thread)
    learning_thread.daemon = True
    learning_thread.start()

    # Start autonomous agent with limited autonomy
    def start_agent_thread():
        logger.info("Starting autonomous agent in background...")
        try:
            autonomous_agent.start_agent(autonomous_mode=False)
        except Exception as e:
            logger.error(f"Error starting agent: {e}")

    agent_thread = threading.Thread(target=start_agent_thread)
    agent_thread.daemon = True
    agent_thread.start()

except Exception as e:
    logger.error(f"Error initializing AI components: {e}")

# Initialize web application
if __name__ == "__main__":
    # Print startup message
    logger.info("Starting Protype.AI web server on http://0.0.0.0:8080")
    logger.info("Loading database and models...")
    
    # Run the application
    try:
        app.run(host='0.0.0.0', port=8080, threaded=True)
    except Exception as e:
        logger.error(f"Error starting web server: {e}")
