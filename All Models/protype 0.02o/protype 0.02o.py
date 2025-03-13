import json
import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from serpapi import GoogleSearch
import threading
import requests
from bs4 import BeautifulSoup
import re
import random
from datetime import datetime


# SQLite Database Setup
def setup_database():
    try:
        conn = sqlite3.connect('bot_knowledge.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS knowledge
                    (question TEXT PRIMARY KEY, answer TEXT, weight REAL, source TEXT)'''
                )
        conn.commit()
        conn.close()
    except sqlite3.DatabaseError:
        print("Database is corrupted. Creating a new one...")
        import os
        if os.path.exists('bot_knowledge.db'):
            os.remove('bot_knowledge.db')
        # Try again with a fresh database
        conn = sqlite3.connect('bot_knowledge.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS knowledge
                    (question TEXT PRIMARY KEY, answer TEXT, weight REAL, source TEXT)'''
                )
        conn.commit()
        conn.close()
        print("New database created successfully.")


# Load user data and bot response templates from JSON
def load_user_data(file_path='user_data.json'):
    try:
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        return {
            "users": {},
            "response_templates": {
                "definition": "Here’s the definition: ",
                "process": "Let me explain how it works: ",
                "reason": "Here’s why: ",
                "person": "Here’s who: ",
                "general": "Here’s what I know: "
            }
        }
    except json.JSONDecodeError:
        print("Error: Corrupted JSON file. Starting fresh.")
        return {
            "users": {},
            "response_templates": {
                "definition": "Here’s the definition: ",
                "process": "Let me explain how it works: ",
                "reason": "Here’s why: ",
                "person": "Here’s who: ",
                "general": "Here’s what I know: "
            }
        }
    except Exception as e:
        print(f"Error loading user data: {e}")
        return {
            "users": {},
            "response_templates": {
                "definition": "Here’s the definition: ",
                "process": "Let me explain how it works: ",
                "reason": "Here’s why: ",
                "person": "Here’s who: ",
                "general": "Here’s what I know: "
            }
        }


# Save user data and bot response templates to JSON
def save_user_data(data, file_path='user_data.json'):
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving user data: {e}")
        return False


# Load knowledge from SQLite
def load_knowledge(question=None):
    conn = sqlite3.connect('bot_knowledge.db')
    c = conn.cursor()
    if question:
        c.execute(
            "SELECT answer, weight, source FROM knowledge WHERE question = ?",
            (question, ))
        result = c.fetchone()
        conn.close()
        return {
            "answer": result[0],
            "weight": result[1],
            "source": result[2]
        } if result else None
    else:
        c.execute("SELECT question, answer, weight, source FROM knowledge")
        results = c.fetchall()
        conn.close()
        return {
            row[0]: {
                "answer": row[1],
                "weight": row[2],
                "source": row[3]
            }
            for row in results
        }


# Save knowledge to SQLite
def save_knowledge(question, answer, weight=0.5, source="user"):
    conn = sqlite3.connect('bot_knowledge.db')
    c = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO knowledge (question, answer, weight, source) VALUES (?, ?, ?, ?)",
        (question, answer, weight, source))
    conn.commit()
    conn.close()
    return True


# Perform Google search using SerpAPI
def perform_search(query):
    try:
        params = {
            "engine":
            "google",
            "q":
            query,
            "api_key":
            "f41082ce8546f83f717679baf1318d649d123ba213a92067de9dfdee2ea5accb"
        }
        search = GoogleSearch(params)
        results = search.get_dict()
        organic_results = results.get("organic_results", [])
        if organic_results:
            return organic_results[0].get("snippet", "No snippet available")
        return "Sorry, I couldn’t find anything relevant."
    except Exception as e:
        return f"Oops! Search failed: {e}"


# Query external AI API
def query_external_ai(query):
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

        # Setup database and load user data
        setup_database()
        self.user_data = load_user_data()

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

        # Start continuous learning in the background
        self.start_continuous_learning()

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
                   command=lambda: self.teach_output.delete(1.0, tk.END),
                   style="TButton").grid(row=0, column=1, padx=5)
        ttk.Style().configure("TButton", background="#ff7043")

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
        ttk.Button(btn_frame,
                   text="Clear",
                   command=lambda: self.search_output.delete(1.0, tk.END),
                   style="TButton").grid(row=0, column=1, padx=5)
        ttk.Style().configure("TButton", background="#ff7043")

    def setup_chat_tab(self):
        ttk.Label(self.chat_frame,
                  text="Chat with Protype!",
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
            tk.END,
            "Hello! I’m Protype 0.01, created by Islam Ibrahim. Ask me anything, and I’ll think deeply to help you!\n"
        )

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
                   command=lambda: self.chat_output.delete(1.0, tk.END),
                   style="TButton").grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame,
                   text="Exit",
                   command=self.exit_app,
                   style="TButton").grid(row=0, column=2, padx=5)

    def process_teach_input(self):
        question = self.teach_question.get().strip()
        answer = self.teach_answer.get().strip()

        if not question or not answer:
            messagebox.showwarning(
                "Oops!", "Please fill in both the question and answer!")
            return

        self.teach_output.delete(1.0, tk.END)
        if save_knowledge(question, answer, 0.5, "user"):
            self.teach_output.insert(
                tk.END,
                f"Thanks! I’ve learned: '{question}' -> '{answer}'\nSaved successfully!\n"
            )
            # Log user action
            user_id = "default_user"  # Placeholder; extend for multi-user support
            if user_id not in self.user_data["users"]:
                self.user_data["users"][user_id] = {"actions": []}
            self.user_data["users"][user_id]["actions"].append({
                "action":
                "teach",
                "question":
                question,
                "timestamp":
                datetime.now().isoformat()
            })
            save_user_data(self.user_data)
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
        if save_knowledge(search_question, result, 0.5, "search"):
            self.search_output.insert(tk.END,
                                      "Knowledge saved successfully!\n")
            # Log user action
            user_id = "default_user"
            if user_id not in self.user_data["users"]:
                self.user_data["users"][user_id] = {"actions": []}
            self.user_data["users"][user_id]["actions"].append({
                "action":
                "search",
                "query":
                query,
                "timestamp":
                datetime.now().isoformat()
            })
            save_user_data(self.user_data)
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
        question_type = analyze_question(question)
        prefix = self.user_data["response_templates"][question_type]

        # Log user action
        user_id = "default_user"
        if user_id not in self.user_data["users"]:
            self.user_data["users"][user_id] = {"actions": []}
        self.user_data["users"][user_id]["actions"].append({
            "action":
            "chat",
            "question":
            question,
            "timestamp":
            datetime.now().isoformat()
        })
        save_user_data(self.user_data)

        # Respond based on current knowledge
        knowledge = load_knowledge(question)
        if knowledge:
            self.chat_output.insert(
                tk.END, f"Protype: {prefix}{knowledge['answer']}\n")
        else:
            data = load_knowledge()
            similar_found = False
            for stored_q in data:
                if question.lower() in stored_q.lower() or stored_q.lower(
                ) in question.lower():
                    answer = data[stored_q]["answer"]
                    self.chat_output.insert(
                        tk.END,
                        f"Protype: I don’t know '{question}' exactly, but about '{stored_q}': {answer}\n"
                    )
                    similar_found = True
                    break

            if not similar_found:
                self.chat_output.insert(
                    tk.END, "Protype: Sorry, I’m studying now for this!\n")
                threading.Thread(target=self.learn_from_external_ai,
                                 args=(question, ),
                                 daemon=True).start()

        self.chat_question.delete(0, tk.END)

    def learn_from_external_ai(self, question):
        ai_response = query_external_ai(question)
        if save_knowledge(question, ai_response, 0.6, "external_ai"):
            print(
                f"Learned from external AI: {question} -> {ai_response[:50]}..."
            )

    def exit_app(self):
        if messagebox.askyesno("Exit",
                               "Are you sure you want to leave Protype 0.01?"):
            self.root.quit()

    # Continuous Learning Functions
    def clean_text(self, text):
        text = re.sub(r'\[.*?\]|\{.*?\}|\<.*?\>', '', text)
        return text.strip()

    def get_wikipedia_content(self, topic):
        url = f"https://en.wikipedia.org/wiki/{topic}"
        try:
            response = requests.get(
                url, headers={'User-Agent': 'Protype.ai Educational Bot'})
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
            save_knowledge(question, answer, 0.6, "wikipedia")
            print(
                f"Learned: {question} → {answer[:50]}... (Total lines: {content.count(chr(10)) + 1})"
            )

        topics = [
            "Lionel_Messi", "Football", "Sport", "FIFA_World_Cup", "Olympics",
            "Athletics", "Basketball", "Tennis", "Serena_Williams",
            "Rafael_Nadal", "Physics", "Newton's_laws_of_motion", "Gravity",
            "Albert_Einstein", "Relativity"
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
            "Albert_Einstein", "Relativity"
        ]
        threading.Timer(3.0, self.learn_topic, args=(topics[0], 0)).start()


# Start the application
if __name__ == "__main__":
    root = tk.Tk()
    app = ProtypeApp(root)
    root.mainloop()
