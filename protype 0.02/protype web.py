import functools
import json
import os
import random
import re
import sqlite3
import time
import threading
from queue import Queue
import queue # Added import for queue.Empty
from concurrent.futures import ThreadPoolExecutor
import spacy
from bs4 import BeautifulSoup
from serpapi import google_search
import tkinter as tk
from tkinter import ttk, messagebox
import networkx as nx
import requests
import google.generativeai as genai
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline

# Load spaCy model for NLP
nlp = spacy.load("en_core_web_sm")

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyBUDUURqkN5Lvid5P8V0ZXIRpseKC7ffMU"  # Replace with your actual key
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini model
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}
gemini_model = genai.GenerativeModel(
    model_name="learnlm-1.5-pro-experimental",
    generation_config=generation_config,
)
chat_session = gemini_model.start_chat(history=[])


# SQLite Database Setup
def init_db(db_path='protype_e0.db'):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS knowledge
                 (question TEXT PRIMARY KEY, answer TEXT, weight REAL, source TEXT)'''
              )
    conn.commit()
    conn.close()


# Cache to avoid frequent database reads
data_cache = {}
last_cache_update = 0
CACHE_EXPIRY = 60  # Cache expires after 60 seconds

# Function to get a database connection
def get_db_connection(db_path='protype_e0.db'):
    return sqlite3.connect(db_path)

# Memoize function to cache results
def memoize(func):
    cache = {}
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        key = str(args) + str(kwargs)
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        return cache[key]
    return wrapper

# Function to load data from SQLite with caching
def load_data(db_path='protype_e0.db', force_reload=False):
    global data_cache, last_cache_update

    current_time = time.time()
    if force_reload or not data_cache or (current_time - last_cache_update) > CACHE_EXPIRY:
        conn = get_db_connection(db_path)
        c = conn.cursor()
        c.execute("SELECT question, answer, weight, source FROM knowledge")
        rows = c.fetchall()
        conn.close()

        data = {}
        for question, answer, weight, source in rows:
            if question not in data:
                data[question] = []
            data[question].append({
                "answer": answer,
                "weight": weight,
                "source": source
            })

        data_cache = data
        last_cache_update = current_time

    return data_cache


# Function to save data to SQLite with optimized connection handling
def save_data(question, answer, weight, source, db_path='protype_e0.db'):
    global data_cache, last_cache_update

    try:
        conn = get_db_connection(db_path)
        c = conn.cursor()
        c.execute(
            "INSERT OR REPLACE INTO knowledge (question, answer, weight, source) VALUES (?, ?, ?, ?)",
            (question, answer, weight, source))
        conn.commit()
        conn.close()

        # Update cache
        if question not in data_cache:
            data_cache[question] = []

        # Update or add to existing entries
        entry_updated = False
        for entry in data_cache.get(question, []):
            if entry["source"] == source:
                entry["answer"] = answer
                entry["weight"] = weight
                entry_updated = True
                break

        if not entry_updated:
            data_cache[question].append({
                "answer": answer,
                "weight": weight,
                "source": source
            })

        return True
    except Exception as e:
        print(f"Error saving data: {e}")
        return False


# Create a thread pool for network requests
network_executor = ThreadPoolExecutor(max_workers=5)
# Add request caching
search_cache = {}
ai_cache = {}

# Function to perform Google search using SerpAPI with caching
def perform_search(query):
    # Check cache first
    if query in search_cache:
        return search_cache[query]

    try:
        params = {
            "engine": "google",
            "q": query,
            "api_key": "f41082ce8546f83f717679baf1318d649d123ba213a92067de9dfdee2ea5accb"
        }
        search = google_search.GoogleSearch(params)
        results = search.get_dict()
        organic_results = results.get("organic_results", [])
        if organic_results:
            result = organic_results[0].get("snippet", "No snippet available")
        else:
            result = "Sorry, I couldn't find anything relevant."

        # Cache the result
        search_cache[query] = result
        return result
    except Exception as e:
        print(f"Search error: {e}")
        return f"Oops! Search failed: {e}"

# Function to query external AI API asynchronously
def query_external_ai(query):
    # Check cache first
    if query in ai_cache:
        return ai_cache[query]

    try:
        url = "https://api.aimlapi.com/v1/chat/completions"
        headers = {
            "Authorization": "Bearer 753aa08c2b8344f38ff8bce052c0bec3",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [{
                "role": "user",
                "content": query
            }],
            "max_tokens": 150
        }
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        result = data["choices"][0]["message"]["content"].strip()

        # Cache the result
        ai_cache[query] = result
        return result
    except Exception as e:
        print(f"Error querying external AI: {e}")
        return f"Failed to get response from external AI: {e}"

# Function to query Gemini Flash 2 with caching
gemini_cache = {}
def query_gemini_flash(question):
    # Check cache first
    if question in gemini_cache:
        return gemini_cache[question]

    try:
        response = chat_session.send_message(question)
        result = response.text.strip()

        # Cache the result
        gemini_cache[question] = result
        return result
    except Exception as e:
        print(f"Error querying Gemini Flash 2: {e}")
        return f"Failed to get response from Gemini Flash 2: {e}"


# Machine Learning model for question classification
training_data = [("what is physics", "definition"),
                 ("how does tennis work", "process"),
                 ("why is messi important", "reason"),
                 ("who discovered gravity", "person")]
questions, labels = zip(*training_data)
model = make_pipeline(TfidfVectorizer(), MultinomialNB())
model.fit(questions, labels)


def analyze_question_ml(question):
    return model.predict([question.lower().strip()])[0]


# GUI Application
class ProtypeE0App:

    def __init__(self, root=None):
        self.root = root
        self.use_tkinter = root is not None
        
        if self.use_tkinter:
            self.root.title("Protype Standard - Develop by Islam Ibrahim")
            self.root.geometry("800x600")
            self.root.configure(bg="#e8f1f5")

        # Initialize SQLite database
        init_db()
        self.data = load_data()
        self.knowledge_graph = nx.DiGraph()
        self.load_knowledge_graph()

        # Response templates
        self.response_templates = {
            "definition": "Here’s the definition: ",
            "process": "Let me explain how it works: ",
            "reason": "Here’s why: ",
            "person": "Here’s who: ",
            "general": "Here’s what I know: "
        }

        # Style Configuration
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton",
                        font=("Arial", 10, "bold"),
                        padding=8,
                        background="#4CAF50",
                        foreground="white")
        style.map("TButton", background=[("active", "#45a049")])
        style.configure("TLabel",
                        font=("Arial", 12),
                        background="#e8f1f5",
                        foreground="#333333")
        style.configure("TNotebook",
                        background="#e8f1f5",
                        tabmargins=[5, 5, 5, 0])
        style.configure("TNotebook.Tab",
                        font=("Arial", 11, "bold"),
                        padding=[10, 5])

        if self.use_tkinter:
            # Notebook (Tabs)
            self.notebook = ttk.Notebook(root)
            self.notebook.pack(pady=15, padx=15, fill="both", expand=True)

            # Teach Tab
            self.teach_frame = ttk.Frame(self.notebook)
            self.notebook.add(self.teach_frame, text="Teach Protype")
            self.setup_teach_tab()

            # Search Tab
            self.search_frame = ttk.Frame(self.notebook)
            self.notebook.add(self.search_frame, text="Search & Learn")
            self.setup_search_tab()

            # Chat Tab
            self.chat_frame = ttk.Frame(self.notebook)
            self.notebook.add(self.chat_frame, text="Chat with Protype")
            self.setup_chat_tab()

        # Start continuous learning
        self.start_continuous_learning()

    def load_knowledge_graph(self, force_reload=False):
        start_time = time.time()

        # Only reload data if forced or it's been more than 60 seconds
        if force_reload or time.time() - getattr(self, 'last_graph_update', 0) > 60:
            self.data = load_data(force_reload=force_reload)

            # Initialize a new graph for better performance
            new_graph = nx.DiGraph()

            # Process in batches for better performance
            batch_size = 50
            questions = list(self.data.keys())

            for i in range(0, len(questions), batch_size):
                batch = questions[i:i+batch_size]

                for question in batch:
                    answers = self.data[question]
                    new_graph.add_node(question, type="question")

                    for answer_data in answers:
                        answer = answer_data["answer"]
                        # Limit text processing to improve performance
                        doc = nlp(question.lower()[:500] + " " + answer.lower()[:500])
                        entities = [ent.text for ent in doc.ents]

                        new_graph.add_node(answer, type="answer")
                        new_graph.add_edge(question, answer, weight=answer_data["weight"])

                        # Limit number of entities to process
                        for entity in entities[:10]:  # Only process up to 10 entities per answer
                            new_graph.add_node(entity, type="entity")
                            new_graph.add_edge(question, entity, relation="mentions")
                            new_graph.add_edge(answer, entity, relation="mentions")

            self.knowledge_graph = new_graph
            self.last_graph_update = time.time()

        print(f"Knowledge graph loaded in {time.time() - start_time:.2f} seconds")

    def setup_teach_tab(self):
        ttk.Label(self.teach_frame,
                  text="Teach Protype Something New!",
                  font=("Arial", 16, "bold"),
                  foreground="#0288d1").pack(pady=10)

        ttk.Label(self.teach_frame, text="What’s your question?").pack(pady=5)
        self.teach_question = ttk.Entry(self.teach_frame,
                                        width=70,
                                        font=("Arial", 11))
        self.teach_question.pack()

        ttk.Label(self.teach_frame, text="What’s the answer?").pack(pady=5)
        self.teach_answer = ttk.Entry(self.teach_frame,
                                      width=70,
                                      font=("Arial", 11))
        self.teach_answer.pack()

        self.teach_output = tk.Text(self.teach_frame,
                                    height=12,
                                    width=80,
                                    bg="#ffffff",
                                    fg="#333333",
                                    font=("Arial", 10),
                                    relief="flat",
                                    borderwidth=2)
        self.teach_output.pack(pady=15)
        self.teach_output.insert(
            tk.END,
            "Hey there! Teach me something cool by entering a question and answer!\n"
        )

        btn_frame = ttk.Frame(self.teach_frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame,
                   text="Teach Me",
                   command=self.process_teach_input).grid(row=0,
                                                          column=0,
                                                          padx=5)
        ttk.Button(btn_frame,
                   text="Clear",
                   command=lambda: self.teach_output.delete(1.0, tk.END)).grid(
                       row=0, column=1, padx=5)

    def setup_search_tab(self):
        ttk.Label(self.search_frame,
                  text="Search & Learn with Protype!",
                  font=("Arial", 16, "bold"),
                  foreground="#0288d1").pack(pady=10)

        ttk.Label(self.search_frame,
                  text="What do you want to search for?").pack(pady=5)
        self.search_query = ttk.Entry(self.search_frame,
                                      width=70,
                                      font=("Arial", 11))
        self.search_query.pack()

        self.search_output = tk.Text(self.search_frame,
                                     height=12,
                                     width=80,
                                     bg="#ffffff",
                                     fg="#333333",
                                     font=("Arial", 10),
                                     relief="flat",
                                     borderwidth=2)
        self.search_output.pack(pady=15)
        self.search_output.insert(
            tk.END, "Enter a search query, and I’ll fetch something useful!\n")

        btn_frame = ttk.Frame(self.search_frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Search",
                   command=self.process_search_input).grid(row=0,
                                                           column=0,
                                                           padx=5)
        ttk.Button(
            btn_frame,
            text="Clear",
            command=lambda: self.search_output.delete(1.0, tk.END)).grid(
                row=0, column=1, padx=5)

    def setup_chat_tab(self):
        ttk.Label(self.chat_frame,
                  text="Chat with Protype s (learn with gemini flash )!",
                  font=("Arial", 16, "bold"),
                  foreground="#0288d1").pack(pady=10)

        self.chat_output = tk.Text(self.chat_frame,
                                   height=15,
                                   width=80,
                                   bg="#ffffff",
                                   fg="#333333",
                                   font=("Arial", 10),
                                   relief="flat",
                                   borderwidth=2)
        self.chat_output.pack(pady=15)
        self.chat_output.insert(
            tk.END, "Hello! I’m Protype s, one piece 3mk . Ask me anything!\n")

        ttk.Label(self.chat_frame, text="Ask me something:").pack()
        self.chat_question = ttk.Entry(self.chat_frame,
                                       width=70,
                                       font=("Arial", 11))
        self.chat_question.pack(pady=5)

        btn_frame = ttk.Frame(self.chat_frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Ask Me",
                   command=self.process_chat_input).grid(row=0,
                                                         column=0,
                                                         padx=5)
        ttk.Button(btn_frame,
                   text="Clear Chat",
                   command=lambda: self.chat_output.delete(1.0, tk.END)).grid(
                       row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="Exit",
                   command=self.exit_app).grid(row=0, column=2, padx=5)

    def process_teach_input(self):
        question = self.teach_question.get().strip()
        answer = self.teach_answer.get().strip()

        if not question or not answer:
            messagebox.showwarning(
                "Oops!", "Please fill in both the question and answer!")
            return

        self.teach_output.delete(1.0, tk.END)
        if save_data(question, answer, 0.5, "user"):
            self.teach_output.insert(
                tk.END,
                f"Thanks! I’ve learned: '{question}' -> '{answer}'\nSaved successfully!\n"
            )
            self.load_knowledge_graph()  # Update Knowledge Graph
        else:
            self.teach_output.insert(
                tk.END,
                "Uh-oh! Something went wrong while saving. Try again?\n")

        self.teach_question.delete(0, tk.END)
        self.teach_answer.delete(0, tk.END)

    def process_search_input(self):
        query = self.search_query.get().strip()
        if not query:
            messagebox.showwarning("Oops!",
                                   "Please enter something to search for!")
            return

        self.search_output.delete(1.0, tk.END)
        self.search_output.insert(tk.END, f"Searching for '{query}'...\n")
        result = perform_search(query)
        self.search_output.insert(tk.END, f"Here’s what I found: {result}\n")

        search_question = f"search: {query}"
        if save_data(search_question, result, 0.5, "serpapi"):
            self.search_output.insert(tk.END,
                                      "Knowledge saved successfully!\n")
            self.load_knowledge_graph()  # Update Knowledge Graph
        else:
            self.search_output.insert(
                tk.END, "Failed to save the knowledge. Please try again!\n")

        self.search_query.delete(0, tk.END)

    def process_chat_input(self):
        question = self.chat_question.get().strip()
        if not question:
            messagebox.showwarning("Oops!", "Please ask me something!")
            return

        self.chat_output.insert(tk.END, f"You asked: {question}\n")
        self.chat_output.see(tk.END)  # Auto-scroll to the end

        # Clear the input field immediately for better UX
        self.chat_question.delete(0, tk.END)

        # Process in a separate thread to keep UI responsive
        threading.Thread(target=self._process_chat_question,
                         args=(question,),
                         daemon=True).start()

    def _process_chat_question(self, question):
        start_time = time.time()
        question_type = analyze_question_ml(question)

        # Use a fixed-length version of the question for NLP to improve performance
        doc = nlp(question.lower()[:200])  # Limit to first 200 chars for processing speed

        # Optimize search - first try exact match
        if question in self.data:
            best_match = question
        else:
            # Use a more efficient similarity search with early stopping
            best_match = None
            max_similarity = 0.7  # Minimum threshold

            # Get all question nodes first (more efficient than checking each node)
            question_nodes = [node for node in self.knowledge_graph.nodes
                             if self.knowledge_graph.nodes[node].get("type") == "question"]

            # Sort by node string length for potential early matches (optimization)
            question_nodes.sort(key=lambda x: abs(len(x) - len(question)))

            # Limit to checking only 100 most promising nodes for performance
            for node in question_nodes[:100]:
                # Simple string matching first (faster than NLP)
                if question.lower() in node.lower() or node.lower() in question.lower():
                    similarity = 0.8  # Give high score to substring matches
                else:
                    # Only use expensive NLP for non-substring matches
                    node_doc = nlp(node.lower()[:200])  # Limit to first 200 chars
                    similarity = doc.similarity(node_doc)

                if similarity > max_similarity:
                    max_similarity = similarity
                    best_match = node
                    # Early stopping if we find a great match
                    if similarity > 0.9:
                        break

        def update_ui():
            if best_match:
                answers = sorted(self.data[best_match],
                                 key=lambda x: x["weight"],
                                 reverse=True)
                answer = answers[0]["answer"]
                prefix = self.response_templates.get(question_type,
                                                     "Here's what I know: ")
                self.chat_output.insert(tk.END, f"Protype: {prefix}{answer}\n")
            else:
                self.chat_output.insert(
                    tk.END, "Protype: Sorry, I'm studying now for this!\n")
                # Start Gemini query in a separate thread
                threading.Thread(target=self.learn_from_gemini_flash,
                                 args=(question,),
                                 daemon=True).start()

            # Get suggestions in a more efficient way
            suggestions = self.suggest_related_questions(question)
            if suggestions:
                self.chat_output.insert(tk.END,
                                        "Related questions you might like:\n")
                for sug in suggestions:
                    self.chat_output.insert(tk.END, f"- {sug}\n")

            self.chat_output.see(tk.END)  # Auto-scroll to the end
            print(f"Chat processing completed in {time.time() - start_time:.2f} seconds")

        # Schedule UI update from main thread
        self.root.after(0, update_ui)

    # Optimize suggestion algorithm
    @memoize
    def suggest_related_questions(self, question):
        # Use shorter text to process for performance
        doc = nlp(question.lower()[:150])
        suggestions = []

        # First check for keyword matches (faster than NLP similarity)
        keywords = [token.text for token in doc if not token.is_stop and not token.is_punct and len(token.text) > 3]

        # Get all question nodes first
        question_nodes = [node for node in self.knowledge_graph.nodes
                         if self.knowledge_graph.nodes[node].get("type") == "question" and node != question]

        # First, try to find matches based on keywords (more efficient)
        for node in question_nodes:
            for keyword in keywords:
                if keyword in node.lower():
                    suggestions.append(node)
                    break

            # If we have enough suggestions, stop
            if len(suggestions) >= 5:
                break

        # If we don't have enough keyword matches, use similarity but limit to 50 nodes
        if len(suggestions) < 3:
            remaining_nodes = [node for node in question_nodes if node not in suggestions][:50]

            for node in remaining_nodes:
                node_doc = nlp(node.lower()[:150])
                similarity = doc.similarity(node_doc)
                if similarity > 0.7:
                    suggestions.append((node, similarity))

            # Sort by similarity and take top ones
            suggestions = [s[0] for s in sorted(suggestions, key=lambda x: x[1], reverse=True)]

        # Return unique suggestions
        return list(dict.fromkeys(suggestions))[:3]  # Remove duplicates and limit to 3

    def learn_from_external_ai(self, question):
        ai_response = query_external_ai(question)
        if save_data(question, ai_response, 0.6, "external_ai"):
            self.load_knowledge_graph()
            print(
                f"Learned from external AI: {question} -> {ai_response[:50]}..."
            )

    def learn_from_gemini_flash(self, question):
        gemini_response = query_gemini_flash(question)
        self.chat_output.insert(
            tk.END, f"Protype (via Gemini Flash 2): {gemini_response}\n")
        if save_data(question, gemini_response, 0.6, "gemini_flash_2"):
            self.load_knowledge_graph()
            self.chat_output.insert(
                tk.END,
                "Protype: I’ve learned this and saved it for next time!\n")
            print(
                f"Learned from Gemini Flash 2: {question} -> {gemini_response[:50]}..."
            )
        else:
            self.chat_output.insert(
                tk.END, "Protype: Failed to save the new knowledge.\n")

    def exit_app(self):
        if messagebox.askyesno("Exit",
                               "Are you sure you want to leave Protype E0?"):
            self.root.quit()

    # Continuous Learning Functions
    def clean_text(self, text):
        return re.sub(r'\[.*?\]|\{.*?\}|\<.*?\>', '', text).strip()

    # Cache for Wikipedia content to avoid redundant network requests
    wikipedia_cache = {}

    def get_wikipedia_content(self, topic):
        # Check cache first
        if topic in self.wikipedia_cache:
            return self.wikipedia_cache[topic]

        try:
            # Use a timeout to avoid hanging
            response = requests.get(
                f"https://en.wikipedia.org/wiki/{topic}",
                headers={'User-Agent': 'ProtypeE0'},
                timeout=5  # 5 second timeout
            )
            response.raise_for_status()

            # Use a more efficient parsing approach
            soup = BeautifulSoup(response.text, 'html.parser')

            # Only get the main content area for better performance
            content_div = soup.find('div', {'id': 'mw-content-text'})
            if not content_div:
                return None

            # Get only first few paragraphs for better performance
            paragraphs = content_div.find_all('p', limit=10)

            content = ""
            for p in paragraphs:
                text = self.clean_text(p.get_text())
                if text and len(text) > 10:
                    content += text + "\n"
                    # Stop after collecting reasonable amount of content
                    if len(content) > 2000:
                        break

            result = content if content else None

            # Cache the result
            self.wikipedia_cache[topic] = result
            return result
        except requests.exceptions.Timeout:
            print(f"Timeout fetching data for {topic}")
            return None
        except Exception as e:
            print(f"Error fetching data for {topic}: {e}")
            return None

    def generate_question(self, topic):
        question_types = [
            f"What is {topic}?", f"How does {topic} work?",
            f"Why is {topic} important?", f"Who discovered {topic}?",
            f"What are the benefits of {topic}?",
            f"How is {topic} used today?", f"Why did {topic} become popular?",
            f"Who contributed to {topic}?"
        ]
        return random.choice(question_types)

    # Learning task queue and worker
    learning_queue = Queue(maxsize=20)
    is_learning_worker_running = False

    def learning_worker(self):
        """Background worker to process continuous learning tasks"""
        while True:
            try:
                topic = self.learning_queue.get(timeout=1)
                if topic is None:  # Sentinel value to stop the worker
                    break

                # Process the learning task
                self._learn_single_topic(topic)

                # Short delay between tasks
                time.sleep(0.5)
                self.learning_queue.task_done()
            except queue.Empty: #Corrected import
                # No tasks in queue, continue waiting
                pass

    def _learn_single_topic(self, topic):
        """Process a single topic learning task"""
        try:
            content = self.get_wikipedia_content(topic)
            if content:
                question = self.generate_question(topic)
                # Truncate content to avoid massive database entries
                if len(content) > 5000:
                    content = content[:5000] + "... (content truncated for performance)"

                answer = f"According to Wikipedia under CC BY-SA 3.0:\n{content}"
                if save_data(question, answer, 0.6, "wikipedia"):
                    # Don't rebuild knowledge graph on every save - just update the cache
                    if question not in data_cache:
                        data_cache[question] = []
                    data_cache[question].append({
                        "answer": answer,
                        "weight": 0.6,
                        "source": "wikipedia"
                    })
                    print(f"Learned: {question}")
        except Exception as e:
            print(f"Error learning topic {topic}: {e}")

    def learn_topic(self, topic, index):
        """Queue a topic for learning"""
        # Add to queue instead of processing immediately
        try:
            self.learning_queue.put_nowait(topic)
        except queue.Full: #Corrected import
            # Queue is full, just skip this topic
            pass

        # Schedule next topic with a longer delay (10 seconds instead of 3)
        topics = self.get_learning_topics()
        next_index = (index + 1) % len(topics)

        # Schedule next topic based on whether we're using tkinter or not
        if self.use_tkinter:
            # Use root.after for tkinter mode
            self.root.after(10000, lambda: self.learn_topic(topics[next_index], next_index))
        else:
            # Use threading.Timer for web server mode
            threading.Timer(10.0, lambda: self.learn_topic(topics[next_index], next_index)).start()

    def start_continuous_learning(self):
        """Start the continuous learning process"""
        global is_learning_worker_running

        # Start the learning worker thread if not already running
        if not self.is_learning_worker_running:
            self.is_learning_worker_running = True
            threading.Thread(target=self.learning_worker, daemon=True).start()

        # Get topics and start learning process
        topics = self.get_learning_topics()

        # Start with a delay to let the application finish initializing
        if self.use_tkinter:
            self.root.after(5000, lambda: self.learn_topic(topics[0], 0))
        else:
            # For web server mode, use threading.Timer instead
            threading.Timer(5.0, lambda: self.learn_topic(topics[0], 0)).start()

    def get_learning_topics(self):
        """Get the list of topics to learn about"""
        return [
            "Lionel_Messi", "Football", "Sport", "FIFA_World_Cup",
            "Physics", "Newton's_laws_of_motion", "Gravity",
            "Albert_Einstein", "Relativity", "Quantum_mechanics",
            "Biology", "DNA", "Genetics", "Mathematics",
            "Artificial_intelligence", "Machine_learning",
            "Deep_learning", "Internet", "World_Wide_Web",
            "Programming", "Python_programming_language",
            "World_War_II", "Industrial_Revolution", "Art",
            "Music", "Classical_music", "Jazz", "Cinema",
            "Philosophy", "Psychology", "Astronomy",
            "Solar_System", "Space_exploration", "NASA",
            "Climate_change", "Renewable_energy",
            "Medicine", "Vaccines", "Human_body"
        ]


# Start the application
# Simple HTTP server for web interface
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class ProtypeHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Protype Web Interface</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background-color: #e8f1f5; }
                .container { max-width: 800px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
                h1 { color: #0288d1; }
                input, textarea { width: 100%; padding: 8px; margin: 8px 0; }
                button { background-color: #4CAF50; color: white; padding: 10px 15px; border: none; border-radius: 4px; cursor: pointer; margin-right: 10px; }
                button:hover { background-color: #45a049; }
                .output { margin-top: 20px; background-color: #f9f9f9; padding: 10px; border-radius: 4px; min-height: 100px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Protype Web Interface</h1>
                
                <div id="tabs">
                    <button onclick="showTab('teach')">Teach Protype</button>
                    <button onclick="showTab('search')">Search & Learn</button>
                    <button onclick="showTab('chat')">Chat with Protype</button>
                </div>
                
                <div id="teach-tab" class="tab-content">
                    <h2>Teach Protype Something New!</h2>
                    <input id="teach-question" placeholder="What's your question?" />
                    <input id="teach-answer" placeholder="What's the answer?" />
                    <button onclick="teachPrtype()">Teach Me</button>
                    <button onclick="clearOutput('teach-output')">Clear</button>
                    <div id="teach-output" class="output">Hey there! Teach me something cool by entering a question and answer!</div>
                </div>
                
                <div id="search-tab" class="tab-content" style="display:none;">
                    <h2>Search & Learn with Protype!</h2>
                    <input id="search-query" placeholder="What do you want to search for?" />
                    <button onclick="searchPrtype()">Search</button>
                    <button onclick="clearOutput('search-output')">Clear</button>
                    <div id="search-output" class="output">Enter a search query, and I'll fetch something useful!</div>
                </div>
                
                <div id="chat-tab" class="tab-content" style="display:none;">
                    <h2>Chat with Protype</h2>
                    <div id="chat-output" class="output">Hello! I'm Protype s, one piece 3mk. Ask me anything!</div>
                    <input id="chat-question" placeholder="Ask me something" />
                    <button onclick="chatWithPrtype()">Ask Me</button>
                    <button onclick="clearOutput('chat-output')">Clear Chat</button>
                </div>
            </div>
            
            <script>
                function showTab(tabName) {
                    document.querySelectorAll('.tab-content').forEach(tab => {
                        tab.style.display = 'none';
                    });
                    document.getElementById(tabName + '-tab').style.display = 'block';
                }
                
                function clearOutput(id) {
                    document.getElementById(id).innerHTML = '';
                }
                
                function teachPrtype() {
                    const question = document.getElementById('teach-question').value;
                    const answer = document.getElementById('teach-answer').value;
                    
                    if (!question || !answer) {
                        alert('Please fill in both the question and answer!');
                        return;
                    }
                    
                    fetch('/teach', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ question, answer })
                    })
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('teach-output').innerHTML = data.message;
                        document.getElementById('teach-question').value = '';
                        document.getElementById('teach-answer').value = '';
                    });
                }
                
                function searchPrtype() {
                    const query = document.getElementById('search-query').value;
                    
                    if (!query) {
                        alert('Please enter something to search for!');
                        return;
                    }
                    
                    document.getElementById('search-output').innerHTML = `Searching for '${query}'...`;
                    
                    fetch('/search', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ query })
                    })
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('search-output').innerHTML = data.message;
                        document.getElementById('search-query').value = '';
                    });
                }
                
                function chatWithPrtype() {
                    const question = document.getElementById('chat-question').value;
                    
                    if (!question) {
                        alert('Please ask me something!');
                        return;
                    }
                    
                    document.getElementById('chat-output').innerHTML += `<br>You asked: ${question}<br>`;
                    document.getElementById('chat-question').value = '';
                    
                    fetch('/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ question })
                    })
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('chat-output').innerHTML += data.message;
                    });
                }
            </script>
        </body>
        </html>
        '''
        self.wfile.write(html.encode())
    
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        if self.path == '/teach':
            question = data.get('question', '')
            answer = data.get('answer', '')
            
            if save_data(question, answer, 0.5, "user"):
                response = {"message": f"Thanks! I've learned: '{question}' -> '{answer}'\nSaved successfully!"}
            else:
                response = {"message": "Uh-oh! Something went wrong while saving. Try again?"}
                
        elif self.path == '/search':
            query = data.get('query', '')
            result = perform_search(query)
            
            search_question = f"search: {query}"
            if save_data(search_question, result, 0.5, "serpapi"):
                response = {"message": f"Here's what I found: {result}\nKnowledge saved successfully!"}
            else:
                response = {"message": f"Here's what I found: {result}\nFailed to save the knowledge. Please try again!"}
                
        elif self.path == '/chat':
            question = data.get('question', '')
            question_type = analyze_question_ml(question)
            
            doc = nlp(question.lower()[:200])
            
            # Get the best match (this is simplified from your original implementation)
            data = load_data()
            best_match = None
            max_similarity = 0.7
            
            for node in data.keys():
                node_doc = nlp(node.lower()[:200])
                similarity = doc.similarity(node_doc)
                if similarity > max_similarity:
                    max_similarity = similarity
                    best_match = node
            
            if best_match:
                answers = sorted(data[best_match], key=lambda x: x["weight"], reverse=True)
                answer = answers[0]["answer"]
                response_templates = {
                    "definition": "Here's the definition: ",
                    "process": "Let me explain how it works: ",
                    "reason": "Here's why: ",
                    "person": "Here's who: ",
                    "general": "Here's what I know: "
                }
                prefix = response_templates.get(question_type, "Here's what I know: ")
                response = {"message": f"<br>Protype: {prefix}{answer}<br>"}
            else:
                # Get answer from Gemini
                gemini_response = query_gemini_flash(question)
                save_data(question, gemini_response, 0.6, "gemini_flash_2")
                response = {"message": f"<br>Protype (via Gemini Flash 2): {gemini_response}<br>"}
        else:
            response = {"message": "Invalid request"}
            
        self.wfile.write(json.dumps(response).encode())

if __name__ == "__main__":
    # Initialize SQLite database
    init_db()
    
    # Performance monitoring
    start_time = time.time()
    print("Starting Protype Web Server...")
    
    # Create the app
    app = ProtypeE0App(None)  # Pass None instead of Tk root
    
    # Start continuous learning in a background thread
    app.start_continuous_learning()
    
    # Start HTTP server
    server_address = ('0.0.0.0', 8080)  # Use 0.0.0.0 to make it accessible outside
    httpd = HTTPServer(server_address, ProtypeHandler)
    
    print(f"Application initialized in {time.time() - start_time:.2f} seconds")
    print("Protype Web Server is running on port 8080!")
    
    # Start the HTTP server
    httpd.serve_forever()