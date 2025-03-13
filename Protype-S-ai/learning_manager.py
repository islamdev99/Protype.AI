
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
        self.reinforcement_file = "reinforcement_data.json"
        self.unanswered_questions_file = "unanswered_questions.json"
        self.load_logs()
        self.load_reinforcement_data()
        self.load_unanswered_questions()
        
    def load_logs(self):
        """Load existing learning logs"""
        try:
            with open(self.log_file, 'r') as f:
                self.logs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.logs = {"logs": []}
            
    def load_reinforcement_data(self):
        """Load reinforcement learning data"""
        try:
            with open(self.reinforcement_file, 'r') as f:
                self.reinforcement_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.reinforcement_data = {
                "successful_responses": [],
                "failed_responses": [],
                "model_adjustments": [],
                "confidence_thresholds": {
                    "default": 0.7,
                    "sensitive_topics": 0.85,
                    "factual_questions": 0.8
                }
            }
    
    def load_unanswered_questions(self):
        """Load questions the system couldn't answer"""
        try:
            with open(self.unanswered_questions_file, 'r') as f:
                self.unanswered_questions = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.unanswered_questions = {"questions": []}
    
    def save_reinforcement_data(self):
        """Save reinforcement learning data"""
        try:
            with open(self.reinforcement_file, 'w') as f:
                json.dump(self.reinforcement_data, f, indent=2)
        except Exception as e:
            print(f"Error saving reinforcement data: {e}")
            
    def save_unanswered_questions(self):
        """Save unanswered questions for future learning"""
        try:
            with open(self.unanswered_questions_file, 'w') as f:
                json.dump(self.unanswered_questions, f, indent=2)
        except Exception as e:
            print(f"Error saving unanswered questions: {e}")
            
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
        
        # Start self-learning thread
        self.self_learning_thread = threading.Thread(target=self.self_learning_loop, daemon=True)
        self.self_learning_thread.start()
        
        self.log_activity("system", "learning", "Started continuous learning with self-learning capabilities")
        print("Continuous learning with self-learning started")
        
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
        gnn_counter = 0
        
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
            
            # Train GNN model periodically to understand relationships
            gnn_counter += 1
            if gnn_counter >= 5:  # Train after every 5 learning cycles
                self.train_gnn_model()
                gnn_counter = 0
                
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
            self.log_activity("gemini", "error", f"Error learning from question: {question}")

    def train_gnn_model(self):
        """Train GNN model to understand concept relationships"""
        try:
            # Import here to avoid circular imports
            from celery_tasks import train_knowledge_gnn
            
            # Schedule the task
            train_knowledge_gnn.delay()
            
            # Log the action
            self.log_activity("gnn", "training", "Training GNN model for knowledge inference")
            
        except Exception as e:
            print(f"Error training GNN model: {e}")
    
    def record_failed_response(self, question, attempted_answer, feedback=None):
        """Record a failed response for reinforcement learning"""
        failure_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "question": question,
            "attempted_answer": attempted_answer,
            "feedback": feedback,
            "processed": False
        }
        
        self.reinforcement_data["failed_responses"].append(failure_data)
        self.save_reinforcement_data()
        self.log_activity("reinforcement", "failure", f"Recorded failed response for: {question[:50]}...")
        
        # Add to unanswered questions for self-learning
        self.add_unanswered_question(question)
        
    def record_successful_response(self, question, answer, confidence_score=0.8):
        """Record a successful response for reinforcement learning"""
        success_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "question": question,
            "answer": answer,
            "confidence_score": confidence_score
        }
        
        self.reinforcement_data["successful_responses"].append(success_data)
        self.save_reinforcement_data()
        self.log_activity("reinforcement", "success", f"Recorded successful response for: {question[:50]}...")
    
    def add_unanswered_question(self, question):
        """Add question to unanswered questions list for future learning"""
        # Check if question already exists
        for existing in self.unanswered_questions["questions"]:
            if existing["question"] == question:
                return
                
        question_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "question": question,
            "attempts": 0,
            "resolved": False
        }
        
        self.unanswered_questions["questions"].append(question_data)
        self.save_unanswered_questions()
        self.log_activity("self-learning", "unanswered", f"Added unanswered question: {question[:50]}...")
    
    def process_unanswered_questions(self, max_questions=3):
        """Process unanswered questions to learn from them"""
        if not self.learning_active:
            return
            
        unresolved = [q for q in self.unanswered_questions["questions"] 
                      if not q["resolved"] and q["attempts"] < 3]
                      
        if not unresolved:
            return
            
        # Sort by attempts (fewer attempts first)
        unresolved.sort(key=lambda x: x["attempts"])
        
        # Process up to max_questions
        for i, question_data in enumerate(unresolved[:max_questions]):
            question = question_data["question"]
            
            try:
                # Try to find answer from external sources
                self.log_activity("self-learning", "research", f"Researching answer for: {question[:50]}...")
                
                # Call more advanced AI model or external API to get answer
                from celery_tasks import learn_from_gemini_flash
                
                # Schedule task and mark attempt
                learn_from_gemini_flash.delay(question)
                
                # Update attempt count
                question_data["attempts"] += 1
                self.save_unanswered_questions()
                
            except Exception as e:
                print(f"Error processing unanswered question: {e}")
    
    def apply_reinforcement_learning(self):
        """Apply reinforcement learning to improve the system"""
        if not self.learning_active:
            return
            
        try:
            # Process failed responses to learn from them
            unprocessed_failures = [r for r in self.reinforcement_data["failed_responses"] 
                                    if not r.get("processed", False)]
                                    
            if unprocessed_failures:
                self.log_activity("reinforcement", "learning", f"Learning from {len(unprocessed_failures)} failed responses")
                
                for failure in unprocessed_failures:
                    # Mark as processed
                    failure["processed"] = True
                    
                    # Try to learn a better answer for this question
                    question = failure["question"]
                    self.add_unanswered_question(question)
                
                self.save_reinforcement_data()
                
            # Process successful responses to reinforce good patterns
            recent_successes = self.reinforcement_data["successful_responses"][-20:]
            if recent_successes:
                topics = set()
                for success in recent_successes:
                    # Extract potential topics from successful questions
                    question_words = success["question"].lower().split()
                    for word in question_words:
                        if len(word) > 4 and word not in ["what", "when", "where", "which", "there"]:
                            topics.add(word)
                
                # Learn more about successful topics
                if topics:
                    selected_topics = random.sample(list(topics), min(3, len(topics)))
                    for topic in selected_topics:
                        self.log_activity("reinforcement", "expansion", f"Expanding knowledge on topic: {topic}")
                        # Schedule learning task for this topic
                        from celery_tasks import learn_from_wikipedia
                        learn_from_wikipedia.delay(topic)
        
        except Exception as e:
            print(f"Error applying reinforcement learning: {e}")
            
    def self_learning_loop(self):
        """Dedicated loop for self-learning activities"""
        while self.learning_active:
            try:
                # Process unanswered questions
                self.process_unanswered_questions()
                
                # Apply reinforcement learning
                self.apply_reinforcement_learning()
                
                # Adjust confidence thresholds based on performance
                self.adjust_confidence_thresholds()
                
                # Sleep before next cycle
                time.sleep(self.learning_interval * 5)  # Less frequent than main learning loop
                
            except Exception as e:
                print(f"Error in self-learning loop: {e}")
                time.sleep(self.learning_interval * 2)
    
    def adjust_confidence_thresholds(self):
        """Dynamically adjust confidence thresholds based on performance"""
        try:
            # Calculate success rate
            total_responses = (len(self.reinforcement_data["successful_responses"]) + 
                              len(self.reinforcement_data["failed_responses"]))
            
            if total_responses < 10:
                return  # Not enough data
                
            success_rate = len(self.reinforcement_data["successful_responses"]) / total_responses
            
            # Adjust thresholds based on success rate
            default_threshold = self.reinforcement_data["confidence_thresholds"]["default"]
            
            if success_rate < 0.6:
                # Increase threshold if success rate is low
                new_threshold = min(default_threshold + 0.05, 0.9)
            elif success_rate > 0.9:
                # Decrease threshold if success rate is high
                new_threshold = max(default_threshold - 0.05, 0.6)
            else:
                return  # No adjustment needed
                
            # Update threshold
            self.reinforcement_data["confidence_thresholds"]["default"] = new_threshold
            
            # Log adjustment
            self.log_activity("reinforcement", "threshold", 
                            f"Adjusted confidence threshold to {new_threshold:.2f} (success rate: {success_rate:.2f})")
            
            # Save changes
            self.save_reinforcement_data()
            
            # Record model adjustment
            adjustment = {
                "timestamp": datetime.datetime.now().isoformat(),
                "type": "confidence_threshold",
                "old_value": default_threshold,
                "new_value": new_threshold,
                "reason": f"Success rate: {success_rate:.2f}"
            }
            
            self.reinforcement_data["model_adjustments"].append(adjustment)
            
        except Exception as e:
            print(f"Error adjusting confidence thresholds: {e}")

# Create singleton instance
learning_manager = LearningManager()
