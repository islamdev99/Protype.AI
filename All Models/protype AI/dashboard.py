import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import time
import os
from datetime import datetime

import database
import visualization
from celery_tasks import batch_wikipedia_learning, generate_topic_suggestions

class Dashboard:
    def __init__(self, knowledge_graph):
        self.knowledge_graph = knowledge_graph

    def get_dashboard_data(self):
        """Get dashboard data for web display"""
        try:
            # Get database stats
            data = database.load_data()
            stats = {
                "question_count": len(data.keys()) if data else 0,
                "node_count": self.knowledge_graph.number_of_nodes(),
                "edge_count": self.knowledge_graph.number_of_edges()
            }

            # Get recent activities
            activities = self.get_recent_activities()

            # Get source data
            source_data = self.get_knowledge_sources()

            # Create charts (base64 encoded)
            charts = {}

            try:
                # Activity chart
                with open('user_actions.json', 'r') as f:
                    activity_log = json.load(f)

                fig = visualization.create_activity_chart(activity_log)
                if fig:
                    charts["activity"] = visualization.get_image_from_fig(fig)
                    plt.close(fig)
            except Exception as e:
                print(f"Error creating activity chart: {e}")

            try:
                # Knowledge sources chart
                fig = visualization.create_knowledge_source_chart()
                if fig:
                    charts["sources"] = visualization.get_image_from_fig(fig)
                    plt.close(fig)
            except Exception as e:
                print(f"Error creating sources chart: {e}")

            try:
                # Knowledge graph visualization (limited)
                fig = visualization.create_knowledge_graph_viz(self.knowledge_graph, max_nodes=50)
                if fig:
                    charts["graph"] = visualization.get_image_from_fig(fig)
                    plt.close(fig)
            except Exception as e:
                print(f"Error creating graph visualization: {e}")

            return {
                "stats": stats,
                "activities": activities,
                "sources": source_data,
                "charts": charts
            }
        except Exception as e:
            print(f"Error getting dashboard data: {e}")
            return {
                "stats": {"question_count": 0, "node_count": 0, "edge_count": 0},
                "activities": [],
                "sources": [],
                "charts": {}
            }

    def get_recent_activities(self, limit=10):
        """Get recent activities from log"""
        try:
            with open('user_actions.json', 'r') as f:
                activity_log = json.load(f)

            # Get recent actions (last 10)
            recent_actions = activity_log.get("actions", [])[-limit:]

            activities = []
            for action in reversed(recent_actions):
                timestamp = action.get("timestamp", "").split("T")[0] + " " + action.get("timestamp", "").split("T")[1][:8]
                user = action.get("user", "unknown")
                action_type = action.get("action", "unknown")
                description = action.get("description", "")

                activities.append({
                    "timestamp": timestamp,
                    "user": user,
                    "action": action_type,
                    "description": description
                })

            return activities
        except Exception as e:
            print(f"Error loading activities: {e}")
            return []

    def get_knowledge_sources(self):
        """Get knowledge source data"""
        try:
            # Get connection to database
            conn, is_postgres = database.get_connection()
            cursor = conn.cursor()

            # Query data
            cursor.execute("SELECT source, COUNT(*) FROM knowledge GROUP BY source")
            data = cursor.fetchall()

            # Release connection
            database.release_connection(conn, is_postgres)

            return [{"source": row[0], "count": row[1]} for row in data]
        except Exception as e:
            print(f"Error getting knowledge sources: {e}")
            return []

    def generate_kb_report(self):
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

            return {"status": "success", "path": report_path}
        except Exception as e:
            print(f"Error generating report: {e}")
            return {"status": "error", "message": str(e)}

    #The rest of the methods are removed because they are using tkinter