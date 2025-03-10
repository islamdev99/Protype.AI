import json
import os
import random
import re
import spacy
from bs4 import BeautifulSoup
from serpapi import google_search
import sqlite3
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import networkx as nx
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
import google.generativeai as genai

# Load spaCy model for NLP
try:
    nlp = spacy.load("en_core_web_sm")
    print("Successfully loaded spaCy model 'en_core_web_sm'")
except OSError:
    print("Downloading spaCy model...")
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyBUDUURqkN5Lvid5P8V0ZXIRpseKC7ffMU"
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


# Function to load data from SQLite
def load_data(db_path='protype_e0.db'):
    conn = sqlite3.connect(db_path)
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
    return data


# Function to save data to SQLite
def save_data(question, answer, weight, source, db_path='protype_e0.db'):
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute(
            "INSERT OR REPLACE INTO knowledge (question, answer, weight, source) VALUES (?, ?, ?, ?)",
            (question, answer, weight, source))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving data: {e}")
        return False


# Function to perform Google search using SerpAPI
def perform_search(query):
    try:
        params = {
            "engine":
            "google",
            "q":
            query,
            "api_key":
            "f41082ce8546f83f717679baf1318d649d123ba213a92067de9dfdee2ea5accb"  # Replace with your key
        }
        search = google_search.GoogleSearch(params)
        results = search.get_dict()
        organic_results = results.get("organic_results", [])
        if organic_results:
            return organic_results[0].get("snippet", "No snippet available")
        return "Sorry, I couldn’t find anything relevant."
    except Exception as e:
        return f"Oops! Search failed: {e}"


# Function to query external AI API
def query_external_ai(query):
    try:
        url = "https://api.aimlapi.com/v1/chat/completions"
        headers = {
            "Authorization":
            "Bearer 753aa08c2b8344f38ff8bce052c0bec3",  # Replace with your key
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
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"Error querying external AI: {e}")
        return f"Failed to get response from external AI: {e}"


# Function to query Gemini Flash 2
def query_gemini_flash(question):
    try:
        response = chat_session.send_message(question)
        return response.text.strip()
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

    def __init__(self, root):
        self.root = root
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

    def load_knowledge_graph(self):
        self.data = load_data()
        for question, answers in self.data.items():
            for answer_data in answers:
                answer = answer_data["answer"]
                doc = nlp(question.lower() + " " + answer.lower())
                entities = [ent.text for ent in doc.ents]
                self.knowledge_graph.add_node(question, type="question")
                self.knowledge_graph.add_node(answer, type="answer")
                self.knowledge_graph.add_edge(question,
                                              answer,
                                              weight=answer_data["weight"])
                for entity in entities:
                    self.knowledge_graph.add_node(entity, type="entity")
                    self.knowledge_graph.add_edge(question,
                                                  entity,
                                                  relation="mentions")
                    self.knowledge_graph.add_edge(answer,
                                                  entity,
                                                  relation="mentions")

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
        question_type = analyze_question_ml(question)
        doc = nlp(question.lower())

        # Search Knowledge Graph with NLP similarity
        best_match = None
        max_similarity = 0.0
        for node in self.knowledge_graph.nodes:
            if self.knowledge_graph.nodes[node].get("type") == "question":
                node_doc = nlp(node.lower())
                similarity = doc.similarity(node_doc)
                if similarity > max_similarity and similarity > 0.7:
                    max_similarity = similarity
                    best_match = node

        if best_match:
            answers = sorted(self.data[best_match],
                             key=lambda x: x["weight"],
                             reverse=True)
            answer = answers[0]["answer"]
            prefix = self.response_templates.get(question_type,
                                                 "Here’s what I know: ")
            self.chat_output.insert(tk.END, f"Protype: {prefix}{answer}\n")
        else:
            self.chat_output.insert(
                tk.END, "Protype: Sorry, I’m studying now for this!\n")
            threading.Thread(target=self.learn_from_gemini_flash,
                             args=(question, ),
                             daemon=True).start()

        # Suggest related questions
        suggestions = self.suggest_related_questions(question)
        if suggestions:
            self.chat_output.insert(tk.END,
                                    "Related questions you might like:\n")
            for sug in suggestions:
                self.chat_output.insert(tk.END, f"- {sug}\n")

        self.chat_question.delete(0, tk.END)

    def suggest_related_questions(self, question):
        doc = nlp(question.lower())
        suggestions = []
        for node in self.knowledge_graph.nodes:
            if self.knowledge_graph.nodes[node].get(
                    "type") == "question" and node != question:
                node_doc = nlp(node.lower())
                if doc.similarity(node_doc) > 0.8:
                    suggestions.append(node)
        return suggestions[:3]

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

    def get_wikipedia_content(self, topic):
        try:
            response = requests.get(f"https://en.wikipedia.org/wiki/{topic}",
                                    headers={'User-Agent': 'ProtypeE0'})
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            paragraphs = soup.find_all('p')
            content = ""
            line_count = 0
            for p in paragraphs:
                text = self.clean_text(p.get_text())
                if text and len(text) > 10:
                    content += text + "\n"
                    line_count += text.count('\n') + 1
                    if line_count >= 200:
                        break
            return content if content else None
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

    def learn_topic(self, topic, index):
        content = self.get_wikipedia_content(topic)
        if content:
            question = self.generate_question(topic)
            answer = f"According to Wikipedia under CC BY-SA 3.0:\n{content}"
            if save_data(question, answer, 0.6, "wikipedia"):
                self.load_knowledge_graph()
                print(f"Learned: {question} -> {answer[:50]}...")

        topics = [
            "Lionel_Messi", "Football", "Sport", "FIFA_World_Cup", "Olympics",
            "Athletics", "Basketball", "Tennis", "Serena_Williams",
            "Rafael_Nadal", "Physics", "Newton's_laws_of_motion", "Gravity",
            "Albert_Einstein", "Relativity", "Quantum_mechanics", "Chemistry",
            "Periodic_table", "Oxygen", "Water", "Biology", "DNA", "Genetics",
            "Charles_Darwin", "Evolution", "Science", "Scientific_method",
            "Mathematics", "Algebra", "Calculus", "Isaac_Newton", "Geometry",
            "Pythagorean_theorem", "Statistics", "Probability", "Technology",
            "Computer_science", "Artificial_intelligence", "Machine_learning",
            "Deep_learning", "Internet", "World_Wide_Web", "Tim_Berners-Lee",
            "Programming", "Python_(programming_language)", "History",
            "World_War_I", "World_War_II", "Industrial_Revolution",
            "Renaissance", "Leonardo_da_Vinci", "Art", "Painting", "Mona_Lisa",
            "Music", "Beethoven", "Classical_music", "Jazz", "Louis_Armstrong",
            "Cinema", "Hollywood", "Steven_Spielberg", "Literature",
            "William_Shakespeare", "Hamlet", "Philosophy", "Socrates", "Plato",
            "Aristotle", "Ethics", "Psychology", "Sigmund_Freud",
            "Behaviorism", "Neuroscience", "Brain", "Astronomy",
            "Solar_System", "Sun", "Moon", "Mars", "Space_exploration", "NASA",
            "Apollo_11", "Neil_Armstrong", "Black_hole", "Geography", "Earth",
            "Continents", "Oceans", "Climate_change", "Environment",
            "Global_warming", "Renewable_energy", "Solar_power", "Wind_power",
            "Medicine", "Vaccines", "Antibiotics", "Human_body", "Heart"
        ]
        next_index = (index + 1) % len(topics)
        threading.Timer(3.0,
                        self.learn_topic,
                        args=(topics[next_index], next_index)).start()

    def start_continuous_learning(self):
        topics = [
            "Lionel_Messi", "Football", "Sport", "FIFA_World_Cup", "Olympics",
            "Athletics", "Basketball", "Tennis", "Serena_Williams",
            "Rafael_Nadal", "Physics", "Newton's_laws_of_motion", "Gravity",
            "Albert_Einstein", "Relativity", "Quantum_mechanics", "Chemistry",
            "Periodic_table", "Oxygen", "Water", "Biology", "DNA", "Genetics",
            "Charles_Darwin", "Evolution", "Science", "Scientific_method",
            "Mathematics", "Algebra", "Calculus", "Isaac_Newton", "Geometry",
            "Pythagorean_theorem", "Statistics", "Probability", "Technology",
            "Computer_science", "Artificial_intelligence", "Machine_learning",
            "Deep_learning", "Internet", "World_Wide_Web", "Tim_Berners-Lee",
            "Programming", "Python_(programming_language)", "History",
            "World_War_I", "World_War_II", "Industrial_Revolution",
            "Renaissance", "Leonardo_da_Vinci", "Art", "Painting", "Mona_Lisa",
            "Music", "Beethoven", "Classical_music", "Jazz", "Louis_Armstrong",
            "Cinema", "Hollywood", "Steven_Spielberg", "Literature",
            "William_Shakespeare", "Hamlet", "Philosophy", "Socrates", "Plato",
            "Aristotle", "Ethics", "Psychology", "Sigmund_Freud",
            "Behaviorism", "Neuroscience", "Brain", "Astronomy",
            "Solar_System", "Sun", "Moon", "Mars", "Space_exploration", "NASA",
            "Apollo_11", "Neil_Armstrong", "Black_hole", "Geography", "Earth",
            "Continents", "Oceans", "Climate_change", "Environment",
            "Global_warming", "Renewable_energy", "Solar_power", "Wind_power",
            "Medicine", "Vaccines", "Antibiotics", "Human_body", "Heart",
            "Machine_learning"
        ]
        threading.Timer(3.0, self.learn_topic, args=(topics[0], 0)).start()


# Start the application
if __name__ == "__main__":
    root = tk.Tk()
    app = ProtypeE0App(root)
    root.mainloop()