
import threading
import random
import time
from celery_tasks import learn_from_wikipedia, learn_from_gemini_flash
import database

class LearningManager:
    def __init__(self):
        self.topics = [
            "Artificial_intelligence", "Machine_learning", "Deep_learning",
            "Natural_language_processing", "Computer_vision", "Robotics",
            "Data_science", "Neural_networks", "Quantum_computing",
            "Blockchain", "Cryptocurrency", "Internet_of_Things",
            "Augmented_reality", "Virtual_reality", "Cloud_computing",
            "Cybersecurity", "Big_data", "Bioinformatics",
            "Space_exploration", "Renewable_energy", "Climate_change",
            "Nanotechnology", "Genetic_engineering", "Stem_cells",
            "Human_genome", "Neuroscience", "Psychology",
            "Philosophy", "Economics", "History"
        ]
        self.questions = [
            "What is the future of renewable energy?",
            "How do neural networks function?",
            "Why is quantum computing important?",
            "How does natural language processing work?",
            "What are the ethical implications of AI?",
            "How can machine learning improve healthcare?",
            "What are the latest advancements in space exploration?",
            "How does blockchain technology secure transactions?",
            "What is the impact of climate change on biodiversity?",
            "How is big data transforming business analytics?"
        ]
        self.running = False
        self.thread = None
        
    def start_learning(self):
        """Start the continuous learning process"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._learning_loop, daemon=True)
        self.thread.start()
        print("Continuous learning started")
        
    def stop_learning(self):
        """Stop the continuous learning process"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            self.thread = None
        print("Continuous learning stopped")
        
    def _learning_loop(self):
        """Main learning loop that rotates between different learning sources"""
        sources = ["wikipedia", "gemini", "topics"]
        current_index = 0
        wikipedia_index = 0
        
        while self.running:
            try:
                source = sources[current_index]
                
                if source == "wikipedia":
                    # Learn from Wikipedia
                    topic = self.topics[wikipedia_index]
                    wikipedia_index = (wikipedia_index + 1) % len(self.topics)
                    print(f"Learning from Wikipedia about: {topic}")
                    learn_from_wikipedia.delay(topic)
                    
                elif source == "gemini":
                    # Learn from Gemini
                    question = random.choice(self.questions)
                    print(f"Learning from Gemini: {question}")
                    learn_from_gemini_flash.delay(question)
                    
                elif source == "topics":
                    # Generate new topics to learn based on existing knowledge
                    self._generate_new_topics()
                
                # Rotate to next source
                current_index = (current_index + 1) % len(sources)
                
                # Sleep for 5 seconds before next learning task
                time.sleep(5)
                
            except Exception as e:
                print(f"Error in learning loop: {e}")
                time.sleep(5)  # Still wait 5 seconds on error
    
    def _generate_new_topics(self):
        """Generate new topics to learn about based on existing knowledge"""
        try:
            # Get some existing knowledge to find related topics
            data = database.load_data()
            if data:
                # Pick a random question from existing knowledge
                question = random.choice(list(data.keys()))
                # Extract potential topics from the question
                words = question.replace("?", "").replace(".", "").split()
                potential_topics = [w for w in words if len(w) > 5 and w.lower() not in ['about', 'would', 'could', 'should', 'their', 'there', 'where', 'which', 'what', 'when', 'with']]
                
                if potential_topics:
                    new_topic = random.choice(potential_topics)
                    print(f"Generated new learning topic: {new_topic}")
                    # Add to topics list if not already there
                    if new_topic not in self.topics:
                        self.topics.append(new_topic)
                        
        except Exception as e:
            print(f"Error generating new topics: {e}")

# Create a global instance
learning_manager = LearningManager()
