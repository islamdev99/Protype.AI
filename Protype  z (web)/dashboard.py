
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import json
import threading
import time
import os
from datetime import datetime

import database
import visualization
from celery_tasks import batch_wikipedia_learning, generate_topic_suggestions

class Dashboard:
    def __init__(self, parent_frame, knowledge_graph):
        self.parent_frame = parent_frame
        self.knowledge_graph = knowledge_graph
        self.setup_dashboard()
        
    def setup_dashboard(self):
        """Setup the dashboard interface"""
        self.notebook = ttk.Notebook(self.parent_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Overview Tab
        self.overview_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.overview_frame, text="Overview")
        self.setup_overview_tab()
        
        # Analytics Tab
        self.analytics_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.analytics_frame, text="Analytics")
        self.setup_analytics_tab()
        
        # Knowledge Graph Tab
        self.graph_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.graph_frame, text="Knowledge Graph")
        self.setup_graph_tab()
        
        # Learning Control Tab
        self.learning_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.learning_frame, text="Learning Controls")
        self.setup_learning_tab()
        
    def setup_overview_tab(self):
        """Setup overview tab with key metrics"""
        # Statistics Section
        stats_frame = ttk.LabelFrame(self.overview_frame, text="Knowledge Base Statistics")
        stats_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Knowledge Base Stats
        stats_content = ttk.Frame(stats_frame)
        stats_content.pack(fill=tk.X, padx=10, pady=10)
        
        # Get database stats
        data = database.load_data()
        question_count = len(data.keys()) if data else 0
        node_count = self.knowledge_graph.number_of_nodes()
        edge_count = self.knowledge_graph.number_of_edges()
        
        # Create stat cards
        self.create_stat_card(stats_content, "Questions", str(question_count), 0, 0)
        self.create_stat_card(stats_content, "Knowledge Graph Nodes", str(node_count), 0, 1)
        self.create_stat_card(stats_content, "Knowledge Graph Connections", str(edge_count), 0, 2)
        
        # Recent Activity Section
        activity_frame = ttk.LabelFrame(self.overview_frame, text="Recent Activity")
        activity_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Activity content
        self.activity_text = tk.Text(activity_frame, height=8, wrap=tk.WORD)
        self.activity_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Load recent activities
        self.update_recent_activity()
        
        # Action buttons at the bottom
        btn_frame = ttk.Frame(self.overview_frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Refresh Dashboard", command=self.refresh_dashboard).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Generate Report", command=self.generate_report).pack(side=tk.LEFT, padx=5)
        
    def create_stat_card(self, parent, title, value, row, column):
        """Create a statistics card"""
        card = ttk.Frame(parent, relief=tk.RIDGE, borderwidth=2)
        card.grid(row=row, column=column, padx=10, pady=10, sticky="nsew")
        
        ttk.Label(card, text=title, font=("Arial", 12)).pack(pady=(10, 5))
        ttk.Label(card, text=value, font=("Arial", 16, "bold")).pack(pady=(5, 10))
        
        # Ensure columns are evenly sized
        parent.columnconfigure(column, weight=1)
        
    def update_recent_activity(self):
        """Update recent activity list from logs"""
        self.activity_text.delete(1.0, tk.END)
        
        try:
            # Load activity log
            with open('user_actions.json', 'r') as f:
                activity_log = json.load(f)
                
            # Get recent actions (last 10)
            recent_actions = activity_log.get("actions", [])[-10:]
            
            for action in reversed(recent_actions):
                timestamp = action.get("timestamp", "").split("T")[0]
                time = action.get("timestamp", "").split("T")[1][:8]
                user = action.get("user", "unknown")
                action_type = action.get("action", "unknown")
                description = action.get("description", "")
                
                entry = f"[{timestamp} {time}] {user}: {action_type} - {description}\n"
                self.activity_text.insert(tk.END, entry)
                
            if not recent_actions:
                self.activity_text.insert(tk.END, "No activity recorded yet.")
        except Exception as e:
            self.activity_text.insert(tk.END, f"Error loading activity log: {e}")
            
    def setup_analytics_tab(self):
        """Setup analytics tab with charts"""
        # Activity Chart Section
        activity_frame = ttk.LabelFrame(self.analytics_frame, text="User Activity")
        activity_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create chart
        try:
            with open('user_actions.json', 'r') as f:
                activity_log = json.load(f)
                
            fig = visualization.create_activity_chart(activity_log)
            if fig:
                canvas = FigureCanvasTkAgg(fig, master=activity_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            else:
                ttk.Label(activity_frame, text="No activity data available").pack(pady=20)
        except Exception as e:
            ttk.Label(activity_frame, text=f"Error creating activity chart: {e}").pack(pady=20)
        
        # Knowledge Sources Chart
        sources_frame = ttk.LabelFrame(self.analytics_frame, text="Knowledge Sources")
        sources_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        try:
            fig = visualization.create_knowledge_source_chart()
            if fig:
                canvas = FigureCanvasTkAgg(fig, master=sources_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            else:
                ttk.Label(sources_frame, text="No knowledge source data available").pack(pady=20)
        except Exception as e:
            ttk.Label(sources_frame, text=f"Error creating knowledge source chart: {e}").pack(pady=20)
        
    def setup_graph_tab(self):
        """Setup knowledge graph visualization tab"""
        control_frame = ttk.Frame(self.graph_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(control_frame, text="Max Nodes:").pack(side=tk.LEFT, padx=(0, 5))
        self.max_nodes_var = tk.StringVar(value="50")
        max_nodes_entry = ttk.Spinbox(control_frame, from_=10, to=200, textvariable=self.max_nodes_var, width=5)
        max_nodes_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Refresh Graph", command=self.refresh_graph).pack(side=tk.LEFT, padx=5)
        
        # Graph visualization container
        self.graph_container = ttk.Frame(self.graph_frame)
        self.graph_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Initial graph rendering
        self.render_knowledge_graph()
        
    def render_knowledge_graph(self):
        """Render the knowledge graph visualization"""
        # Clear previous graph
        for widget in self.graph_container.winfo_children():
            widget.destroy()
            
        try:
            max_nodes = int(self.max_nodes_var.get())
            fig = visualization.create_knowledge_graph_viz(self.knowledge_graph, max_nodes)
            
            if fig:
                canvas = FigureCanvasTkAgg(fig, master=self.graph_container)
                canvas.draw()
                canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            else:
                ttk.Label(self.graph_container, text="Knowledge graph visualization not available").pack(pady=20)
        except Exception as e:
            ttk.Label(self.graph_container, text=f"Error rendering knowledge graph: {e}").pack(pady=20)
            
    def refresh_graph(self):
        """Refresh the knowledge graph visualization"""
        self.render_knowledge_graph()
        
    def setup_learning_tab(self):
        """Setup learning controls tab"""
        # Learning status
        status_frame = ttk.LabelFrame(self.learning_frame, text="Learning Status")
        status_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.learning_status_var = tk.StringVar(value="Inactive")
        status_label = ttk.Label(status_frame, textvariable=self.learning_status_var, font=("Arial", 12, "bold"))
        status_label.pack(pady=10)
        
        # Learning controls
        controls_frame = ttk.LabelFrame(self.learning_frame, text="Learning Controls")
        controls_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(controls_frame, text="Start Learning", command=self.start_learning).pack(side=tk.LEFT, padx=5, pady=10)
        ttk.Button(controls_frame, text="Stop Learning", command=self.stop_learning).pack(side=tk.LEFT, padx=5, pady=10)
        
        # Batch Learning Section
        batch_frame = ttk.LabelFrame(self.learning_frame, text="Batch Learning")
        batch_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Topics list
        topics_frame = ttk.Frame(batch_frame)
        topics_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(topics_frame, text="Enter topics to learn about (one per line):").pack(anchor=tk.W)
        
        self.topics_text = tk.Text(topics_frame, height=8, width=40)
        self.topics_text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.topics_text.insert(tk.END, "Artificial_intelligence\nMachine_learning\nQuantum_computing\nBlockchain\nNeuroscience")
        
        actions_frame = ttk.Frame(batch_frame)
        actions_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(actions_frame, text="Generate Topic Suggestions", command=self.generate_topics).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="Start Batch Learning", command=self.start_batch_learning).pack(side=tk.LEFT, padx=5)
        
    def start_learning(self):
        """Start continuous learning"""
        try:
            from learning_manager import learning_manager
            learning_manager.start_learning()
            self.learning_status_var.set("Active")
            messagebox.showinfo("Learning Started", "Continuous learning process has started")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start learning: {e}")
            
    def stop_learning(self):
        """Stop continuous learning"""
        try:
            from learning_manager import learning_manager
            learning_manager.stop_learning()
            self.learning_status_var.set("Inactive")
            messagebox.showinfo("Learning Stopped", "Continuous learning process has been stopped")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop learning: {e}")
            
    def generate_topics(self):
        """Generate topic suggestions based on existing topics"""
        current_topics = self.topics_text.get(1.0, tk.END).strip().split('\n')
        
        try:
            from celery_tasks import generate_topic_suggestions
            result = generate_topic_suggestions.delay(current_topics)
            
            # Show loading message
            self.topics_text.delete(1.0, tk.END)
            self.topics_text.insert(tk.END, "Generating topic suggestions...")
            
            # Check result after a delay
            self.parent_frame.after(2000, lambda: self.check_topic_suggestions(result.id))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate topic suggestions: {e}")
            
    def check_topic_suggestions(self, task_id):
        """Check if topic suggestions are ready"""
        try:
            # In a real app, you'd use Celery's AsyncResult to check the task status
            # For this example, we'll simulate getting the result
            
            # Simulated topics
            new_topics = [
                "Neural_networks", 
                "Reinforcement_learning", 
                "Natural_language_processing",
                "Computer_vision",
                "Robotics"
            ]
            
            self.topics_text.delete(1.0, tk.END)
            self.topics_text.insert(tk.END, "\n".join(new_topics))
        except Exception as e:
            self.topics_text.delete(1.0, tk.END)
            self.topics_text.insert(tk.END, f"Error: {e}\n\nPlease try again.")
            
    def start_batch_learning(self):
        """Start batch learning with the specified topics"""
        topics = self.topics_text.get(1.0, tk.END).strip().split('\n')
        
        if not topics or topics[0] == "":
            messagebox.showwarning("No Topics", "Please enter at least one topic to learn about")
            return
            
        try:
            result = batch_wikipedia_learning.delay(topics)
            messagebox.showinfo("Batch Learning", f"Started learning about {len(topics)} topics\nTask ID: {result.id}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start batch learning: {e}")
            
    def generate_report(self):
        """Generate and save a knowledge base report"""
        try:
            report_path = "knowledge_report.txt"
            
            # Collect data
            data = database.load_data()
            question_count = len(data.keys()) if data else 0
            node_count = self.knowledge_graph.number_of_nodes()
            edge_count = self.knowledge_graph.number_of_edges()
            
            # Get source counts
            conn, is_postgres = database.get_connection()
            cursor = conn.cursor()
            
            if is_postgres:
                cursor.execute("SELECT source, COUNT(*) FROM knowledge GROUP BY source")
            else:
                cursor.execute("SELECT source, COUNT(*) FROM knowledge GROUP BY source")
                
            source_data = cursor.fetchall()
            database.release_connection(conn, is_postgres)
            
            # Write report
            with open(report_path, 'w') as f:
                f.write("Protype.AI Knowledge Base Report\n")
                f.write("=" * 40 + "\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                f.write("Knowledge Base Stats:\n")
                f.write(f"- Total questions: {question_count}\n")
                f.write(f"- Knowledge graph nodes: {node_count}\n")
                f.write(f"- Knowledge graph connections: {edge_count}\n\n")
                
                f.write("Knowledge Sources:\n")
                for source, count in source_data:
                    f.write(f"- {source}: {count} items\n")
                    
                f.write("\nRecent Knowledge:\n")
                items_shown = 0
                for question, answers in data.items():
                    if items_shown >= 10:
                        break
                    f.write(f"Q: {question}\n")
                    f.write(f"A: {answers[0]['answer'][:100]}...\n")
                    f.write(f"Source: {answers[0]['source']}\n\n")
                    items_shown += 1
                    
            messagebox.showinfo("Report Generated", f"Knowledge base report saved to {report_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate report: {e}")
            
    def refresh_dashboard(self):
        """Refresh all dashboard elements"""
        self.update_recent_activity()
        self.setup_overview_tab()
        self.notebook.select(0)  # Switch to overview tab
        messagebox.showinfo("Dashboard Refreshed", "Dashboard data has been refreshed")
