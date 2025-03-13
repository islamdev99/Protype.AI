
import threading
import time
import random
import os
import json
import datetime
from celery import Celery

# Configure Celery with Redis (if available) or use local memory broker
if 'REDIS_URL' in os.environ:
    broker_url = os.environ['REDIS_URL']
else:
    broker_url = 'memory://'

celery_app = Celery('protype_tasks', broker=broker_url)

# Learning topics
LEARNING_TOPICS = [
    "Artificial_intelligence", "Machine_learning", "Deep_learning",
    "Natural_language_processing", "Computer_vision", "Robotics",
    "Data_science", "Neural_networks", "Quantum_computing", "Blockchain"
]

# Learning questions
LEARNING_QUESTIONS = [
    "What is the future of renewable energy?",
    "How does blockchain technology secure transactions?",
    "How is big data transforming business analytics?",
    "How do neural networks function?",
    "What are the latest advancements in space exploration?",
    "Why is quantum computing important?",
    "How do self-driving cars navigate?"
]

class LearningManager:
    def __init__(self):
        self.learning_active = False
        self.learning_thread = None
        self.learning_interval = 5  # seconds between learning tasks
        self.log_file = "learning_logs.json"
        self.load_logs()
        
    def load_logs(self):
        """Load existing learning logs"""
        try:
            with open(self.log_file, 'r') as f:
                self.logs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.logs = {"logs": []}
            
    def save_logs(self):
        """Save learning logs to file"""
        try:
            with open(self.log_file, 'w') as f:
                json.dump(self.logs, f, indent=2)
        except Exception as e:
            print(f"Error saving learning logs: {e}")
            
    def log_activity(self, source, action, description):
        """Log learning activity"""
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "source": source,
            "action": action,
            "description": description
        }
        
        self.logs["logs"].append(log_entry)
        self.save_logs()
        
    def start_learning(self):
        """Start continuous learning process"""
        if self.learning_active:
            print("Learning already active")
            return
            
        self.learning_active = True
        self.learning_thread = threading.Thread(target=self.learning_loop, daemon=True)
        self.learning_thread.start()
        
        self.log_activity("system", "learning", "Started continuous learning")
        print("Continuous learning started")
        
    def stop_learning(self):
        """Stop continuous learning process"""
        if not self.learning_active:
            print("Learning not active")
            return
            
        self.learning_active = False
        if self.learning_thread:
            self.learning_thread = None
            
        self.log_activity("system", "learning", "Stopped continuous learning")
        print("Continuous learning stopped")
        
    def learning_loop(self):
        """Main learning loop"""
        topic_index = 0
        question_index = 0
        
        while self.learning_active:
            # Alternate between Wikipedia and generated questions
            if topic_index % 2 == 0:
                # Learn from Wikipedia
                topic = LEARNING_TOPICS[topic_index % len(LEARNING_TOPICS)]
                self.learn_from_wikipedia(topic)
                topic_index += 1
            else:
                # Learn from generated questions
                question = LEARNING_QUESTIONS[question_index % len(LEARNING_QUESTIONS)]
                self.learn_from_gemini(question)
                question_index += 1
                
            # Generate new topics periodically
            if topic_index % 3 == 0:
                self.log_activity("system", "topic_generation", "Generating new topics to learn")
                
            # Sleep before next learning cycle
            time.sleep(self.learning_interval)
            
    def learn_from_wikipedia(self, topic):
        """Learn from Wikipedia in the background"""
        try:
            # Import here to avoid circular imports
            from celery_tasks import learn_from_wikipedia
            
            # Schedule the task
            learn_from_wikipedia.delay(topic)
            
            # Log the action
            self.log_activity("wikipedia", "learning", f"Learning about: {topic}")
            
        except Exception as e:
            print(f"Error learning from Wikipedia: {e}")
            
    def learn_from_gemini(self, question):
        """Learn from Gemini in the background"""
        try:
            # Import here to avoid circular imports
            from celery_tasks import learn_from_gemini_flash
            
            # Schedule the task
            learn_from_gemini_flash.delay(question)
            
            # Log the action
            self.log_activity("gemini", "learning", f"Learning from question: {question}")
            
        except Exception as e:
            print(f"Error learning from Gemini: {e}")

# Create singleton instance
learning_manager = LearningManager()
