import json
import os
import tkinter as tk
from tkinter import ttk, messagebox
from serpapi import GoogleSearch
import threading
import requests
from bs4 import BeautifulSoup
import re
import random

# Function to load data from JSON file
def load_data(file_path='bot_data.json'):
    try:
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        return {}
    except json.JSONDecodeError:
        print("Error: Corrupted JSON file. Starting fresh.")
        return {}
    except Exception as e:
        print(f"Error loading data: {e}")
        return {}

# Function to save data to JSON file
def save_data(data, file_path='bot_data.json'):
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving data: {e}")
        return False

# Function to perform Google search using SerpAPI
def perform_search(query):
    try:
        params = {
            "engine": "google",
            "q": query,
            "api_key": "f41082ce8546f83f717679baf1318d649d123ba213a92067de9dfdee2ea5accb"
        }
        search = GoogleSearch(params)
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
            "Authorization": "Bearer 753aa08c2b8344f38ff8bce052c0bec3",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-3.5-turbo",  # Assuming a compatible model; adjust if needed
            "messages": [{"role": "user", "content": query}],
            "max_tokens": 150
        }
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"Error querying external AI: {e}")
        return f"Failed to get response from external AI: {e}"

# Analyze question for deep thinking
def analyze_question(question):
    question = question.lower().strip()
    if question.startswith("what is"):
        return "definition"
    elif question.startswith("how"):
        return "process"
    elif question.startswith("why"):
        return "reason"
    elif question.startswith("who"):
        return "person"
    else:
        return "general"

# GUI Application
class ProtypeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Protype 0.01 - Made by Islam Ibrahim")
        self.root.geometry("800x600")
        self.root.configure(bg="#e8f1f5")

        self.data = load_data()

        # Style Configuration
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", font=("Arial", 10, "bold"), padding=8, background="#4CAF50", foreground="white")
        style.map("TButton", background=[("active", "#45a049")])
        style.configure("TLabel", font=("Arial", 12), background="#e8f1f5", foreground="#333333")
        style.configure("TNotebook", background="#e8f1f5", tabmargins=[5, 5, 5, 0])
        style.configure("TNotebook.Tab", font=("Arial", 11, "bold"), padding=[10, 5])

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

        # Start continuous learning in the background
        self.start_continuous_learning()

    def setup_teach_tab(self):
        ttk.Label(self.teach_frame, text="Teach Protype Something New!", font=("Arial", 16, "bold"), foreground="#0288d1").pack(pady=10)

        ttk.Label(self.teach_frame, text="What’s your question?").pack(pady=5)
        self.teach_question = ttk.Entry(self.teach_frame, width=70, font=("Arial", 11))
        self.teach_question.pack()

        ttk.Label(self.teach_frame, text="What’s the answer?").pack(pady=5)
        self.teach_answer = ttk.Entry(self.teach_frame, width=70, font=("Arial", 11))
        self.teach_answer.pack()

        self.teach_output = tk.Text(self.teach_frame, height=12, width=80, bg="#ffffff", fg="#333333", font=("Arial", 10), relief="flat", borderwidth=2)
        self.teach_output.pack(pady=15)
        self.teach_output.insert(tk.END, "Hey there! Teach me something cool by entering a question and answer!\n")

        btn_frame = ttk.Frame(self.teach_frame)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Teach Me", command=self.process_teach_input).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Clear", command=lambda: self.teach_output.delete(1.0, tk.END), style="TButton").grid(row=0, column=1, padx=5)
        ttk.Style().configure("TButton", background="#ff7043")

    def setup_search_tab(self):
        ttk.Label(self.search_frame, text="Search & Learn with Protype!", font=("Arial", 16, "bold"), foreground="#0288d1").pack(pady=10)

        ttk.Label(self.search_frame, text="What do you want to search for?").pack(pady=5)
        self.search_query = ttk.Entry(self.search_frame, width=70, font=("Arial", 11))
        self.search_query.pack()

        self.search_output = tk.Text(self.search_frame, height=12, width=80, bg="#ffffff", fg="#333333", font=("Arial", 10), relief="flat", borderwidth=2)
        self.search_output.pack(pady=15)
        self.search_output.insert(tk.END, "Enter a search query, and I’ll fetch something useful!\n")

        btn_frame = ttk.Frame(self.search_frame)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Search", command=self.process_search_input).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Clear", command=lambda: self.search_output.delete(1.0, tk.END), style="TButton").grid(row=0, column=1, padx=5)
        ttk.Style().configure("TButton", background="#ff7043")

    def setup_chat_tab(self):
        ttk.Label(self.chat_frame, text="Chat with Protype!", font=("Arial", 16, "bold"), foreground="#0288d1").pack(pady=10)

        self.chat_output = tk.Text(self.chat_frame, height=15, width=80, bg="#ffffff", fg="#333333", font=("Arial", 10), relief="flat", borderwidth=2)
        self.chat_output.pack(pady=15)
        self.chat_output.insert(tk.END, "Hello! I’m Protype 0.01, created by Islam Ibrahim. Ask me anything, and I’ll think deeply to help you!\n")

        ttk.Label(self.chat_frame, text="Ask me something:").pack()
        self.chat_question = ttk.Entry(self.chat_frame, width=70, font=("Arial", 11))
        self.chat_question.pack(pady=5)

        btn_frame = ttk.Frame(self.chat_frame)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Ask Me", command=self.process_chat_input).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Clear Chat", command=lambda: self.chat_output.delete(1.0, tk.END), style="TButton").grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="Exit", command=self.exit_app, style="TButton").grid(row=0, column=2, padx=5)

    def process_teach_input(self):
        question = self.teach_question.get().strip()
        answer = self.teach_answer.get().strip()

        if not question or not answer:
            messagebox.showwarning("Oops!", "Please fill in both the question and answer!")
            return

        self.teach_output.delete(1.0, tk.END)
        if question not in self.data:
            self.data[question] = []
        self.data[question].append({"answer": answer, "weight": 0.5})

        if save_data(self.data):
            self.teach_output.insert(tk.END, f"Thanks! I’ve learned: '{question}' -> '{answer}'\nSaved successfully!\n")
        else:
            self.teach_output.insert(tk.END, "Uh-oh! Something went wrong while saving. Try again?\n")

        self.teach_question.delete(0, tk.END)
        self.teach_answer.delete(0, tk.END)

    def process_search_input(self):
        query = self.search_query.get().strip()
        if not query:
            messagebox.showwarning("Oops!", "Please enter something to search for!")
            return

        self.search_output.delete(1.0, tk.END)
        self.search_output.insert(tk.END, f"Searching for '{query}'...\n")
        result = perform_search(query)
        self.search_output.insert(tk.END, f"Here’s what I found: {result}\n")

        search_question = f"search: {query}"
        if search_question not in self.data:
            self.data[search_question] = []
        self.data[search_question].append({"answer": result, "weight": 0.5})

        if save_data(self.data):
            self.search_output.insert(tk.END, "Knowledge saved successfully!\n")
        else:
            self.search_output.insert(tk.END, "Failed to save the knowledge. Please try again!\n")

        self.search_query.delete(0, tk.END)

    def process_chat_input(self):
        question = self.chat_question.get().strip()
        if not question:
            messagebox.showwarning("Oops!", "Please ask me something!")
            return

        self.chat_output.insert(tk.END, f"You asked: {question}\n")
        question_type = analyze_question(question)

        # Part 1: Respond based on current knowledge
        if question in self.data and self.data[question]:
            answers = sorted(self.data[question], key=lambda x: x["weight"], reverse=True)
            answer = answers[0]["answer"]
            prefix = {
                "definition": "Here’s the definition: ",
                "process": "Let me explain how it works: ",
                "reason": "Here’s why: ",
                "person": "Here’s who: ",
                "general": "Here’s what I know: "
            }
            self.chat_output.insert(tk.END, f"Protype: {prefix[question_type]}{answer}\n")
        else:
            similar_found = False
            for stored_q in self.data:
                if question.lower() in stored_q.lower() or stored_q.lower() in question.lower():
                    answer = self.data[stored_q][0]["answer"]
                    self.chat_output.insert(tk.END, f"Protype: I don’t know '{question}' exactly, but about '{stored_q}': {answer}\n")
                    similar_found = True
                    break

            if not similar_found:
                self.chat_output.insert(tk.END, "Protype: Sorry, I’m studying now for this!\n")
                # Part 2: Send to external AI in the background
                threading.Thread(target=self.learn_from_external_ai, args=(question,), daemon=True).start()

        self.chat_question.delete(0, tk.END)

    def learn_from_external_ai(self, question):
        # Query the external AI
        ai_response = query_external_ai(question)
        # Store the response in the JSON data
        if question not in self.data:
            self.data[question] = []
        self.data[question].append({"answer": ai_response, "weight": 0.6, "source": "external_ai"})
        save_data(self.data)
        print(f"Learned from external AI: {question} -> {ai_response[:50]}...")

    def exit_app(self):
        if messagebox.askyesno("Exit", "Are you sure you want to leave Protype 0.01?"):
            self.root.quit()

    # Functions for Continuous Learning from Wikipedia
    def clean_text(self, text):
        """Clean text from unnecessary symbols"""
        text = re.sub(r'\[.*?\]|\{.*?\}|\<.*?\>', '', text)  # Remove links and tags
        text = text.strip()
        return text

    def get_wikipedia_content(self, topic):
        """Fetch extensive content from Wikipedia about a topic"""
        url = f"https://en.wikipedia.org/wiki/{topic}"
        try:
            response = requests.get(url, headers={'User-Agent': 'Protype.ai Educational Bot'})
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
                    if line_count >= 200:  # Stop at ~200 lines
                        break
            if not content:
                return None
            return content
        except Exception as e:
            print(f"Error fetching data for {topic}: {e}")
            return None

    def generate_question(self, topic):
        """Generate a random question type for the topic"""
        question_types = [
            f"What is {topic}?",
            f"How does {topic} work?",
            f"Why is {topic} important?",
            f"Who discovered {topic}?",
            f"What are the benefits of {topic}?",
            f"How is {topic} used today?",
            f"Why did {topic} become popular?",
            f"Who contributed to {topic}?"
        ]
        return random.choice(question_types)

    def learn_topic(self, topic, index):
        """Learn about a single topic and schedule the next"""
        content = self.get_wikipedia_content(topic)
        if content:
            question = self.generate_question(topic)
            answer = f"According to Wikipedia under CC BY-SA 3.0:\n{content}"
            if question not in self.data:
                self.data[question] = []
            self.data[question].append({"answer": answer, "weight": 0.6, "source": "wikipedia"})
            save_data(self.data)
            print(f"Learned: {question} → {answer[:50]}... (Total lines: {content.count(chr(10)) + 1})")

        # Schedule the next topic
        topics = [
            "Lionel_Messi", "Football", "Sport", "FIFA_World_Cup", "Olympics",
            "Athletics", "Basketball", "Tennis", "Serena_Williams", "Rafael_Nadal",
            "Physics", "Newton's_laws_of_motion", "Gravity", "Albert_Einstein", "Relativity",
            "Quantum_mechanics", "Chemistry", "Periodic_table", "Oxygen", "Water",
            "Biology", "DNA", "Genetics", "Charles_Darwin", "Evolution",
            "Science", "Scientific_method", "Mathematics", "Algebra", "Calculus",
            "Isaac_Newton", "Geometry", "Pythagorean_theorem", "Statistics", "Probability",
            "Technology", "Computer_science", "Artificial_intelligence", "Machine_learning", "Deep_learning",
            "Internet", "World_Wide_Web", "Tim_Berners-Lee", "Programming", "Python_(programming_language)",
            "History", "World_War_I", "World_War_II", "Industrial_Revolution", "Renaissance",
            "Leonardo_da_Vinci", "Art", "Painting", "Mona_Lisa", "Music",
            "Beethoven", "Classical_music", "Jazz", "Louis_Armstrong", "Cinema",
            "Hollywood", "Steven_Spielberg", "Literature", "William_Shakespeare", "Hamlet",
            "Philosophy", "Socrates", "Plato", "Aristotle", "Ethics",
            "Psychology", "Sigmund_Freud", "Behaviorism", "Neuroscience", "Brain",
            "Astronomy", "Solar_System", "Sun", "Moon", "Mars",
            "Space_exploration", "NASA", "Apollo_11", "Neil_Armstrong", "Black_hole",
            "Geography", "Earth", "Continents", "Oceans", "Climate_change",
            "Environment", "Global_warming", "Renewable_energy", "Solar_power", "Wind_power",
            "Medicine", "Vaccines", "Antibiotics", "Human_body", "Heart"
        ]
        next_index = (index + 1) % len(topics)  # Loop back to start if at end
        threading.Timer(3.0, self.learn_topic, args=(topics[next_index], next_index)).start()

    def start_continuous_learning(self):
        """Start the continuous learning process"""
        topics = [
            "Lionel_Messi", "Football", "Sport", "FIFA_World_Cup", "Olympics",
            "Athletics", "Basketball", "Tennis", "Serena_Williams", "Rafael_Nadal",
            "Physics", "Newton's_laws_of_motion", "Gravity", "Albert_Einstein", "Relativity",
            "Quantum_mechanics", "Chemistry", "Periodic_table", "Oxygen", "Water",
            "Biology", "DNA", "Genetics", "Charles_Darwin", "Evolution",
            "Science", "Scientific_method", "Mathematics", "Algebra", "Calculus",
            "Isaac_Newton", "Geometry", "Pythagorean_theorem", "Statistics", "Probability",
            "Technology", "Computer_science", "Artificial_intelligence", "Machine_learning", "Deep_learning",
            "Internet", "World_Wide_Web", "Tim_Berners-Lee", "Programming", "Python_(programming_language)",
            "History", "World_War_I", "World_War_II", "Industrial_Revolution", "Renaissance",
            "Leonardo_da_Vinci", "Art", "Painting", "Mona_Lisa", "Music",
            "Beethoven", "Classical_music", "Jazz", "Louis_Armstrong", "Cinema",
            "Hollywood", "Steven_Spielberg", "Literature", "William_Shakespeare", "Hamlet",
            "Philosophy", "Socrates", "Plato", "Aristotle", "Ethics",
            "Psychology", "Sigmund_Freud", "Behaviorism", "Neuroscience", "Brain",
            "Astronomy", "Solar_System", "Sun", "Moon", "Mars",
            "Space_exploration", "NASA", "Apollo_11", "Neil_Armstrong", "Black_hole",
            "Geography", "Earth", "Continents", "Oceans", "Climate_change",
            "Environment", "Global_warming", "Renewable_energy", "Solar_power", "Wind_power",
            "Medicine", "Vaccines", "Antibiotics", "Human_body", "Heart"
        ]
        threading.Timer(3.0, self.learn_topic, args=(topics[0], 0)).start()

# Start the application
if __name__ == "__main__":
    root = tk.Tk()
    app = ProtypeApp(root)
    root.mainloop()