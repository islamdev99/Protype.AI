import matplotlib.pyplot as plt
import networkx as nx
import io
import base64
import database
from collections import Counter
import json
from datetime import datetime, timedelta

def create_activity_chart(activity_log):
    """Create activity chart from log data"""
    try:
        # Count activities by date
        activities = activity_log.get("actions", [])

        if not activities:
            return None

        # Group by date and action type
        date_counts = {}

        for activity in activities:
            date = activity.get("timestamp", "").split("T")[0]
            action_type = activity.get("action", "unknown")

            if date not in date_counts:
                date_counts[date] = {}

            if action_type not in date_counts[date]:
                date_counts[date][action_type] = 0

            date_counts[date][action_type] += 1

        # Sort dates
        dates = sorted(date_counts.keys())

        if not dates:
            return None

        # Get action types
        action_types = set()
        for date_data in date_counts.values():
            action_types.update(date_data.keys())

        action_types = sorted(action_types)

        # Prepare data for stacked bar chart
        data = []
        for action_type in action_types:
            values = []
            for date in dates:
                values.append(date_counts[date].get(action_type, 0))
            data.append(values)

        # Create chart
        fig, ax = plt.subplots(figsize=(10, 6))

        bottom = [0] * len(dates)
        for i, action_type in enumerate(action_types):
            ax.bar(dates, data[i], bottom=bottom, label=action_type)
            bottom = [bottom[j] + data[i][j] for j in range(len(dates))]

        ax.set_title("User Activity Over Time")
        ax.set_xlabel("Date")
        ax.set_ylabel("Number of Activities")
        ax.legend()

        # Rotate date labels for better visibility
        plt.xticks(rotation=45)
        plt.tight_layout()

        return fig
    except Exception as e:
        print(f"Error creating activity chart: {e}")
        return None

def create_knowledge_source_chart():
    """Create pie chart of knowledge sources"""
    try:
        # Get connection to database
        conn, is_postgres = database.get_connection()
        cursor = conn.cursor()

        # Query data
        cursor.execute("SELECT source, COUNT(*) FROM knowledge GROUP BY source")
        data = cursor.fetchall()

        # Release connection
        database.release_connection(conn, is_postgres)

        if not data:
            return None

        # Extract labels and values
        labels = [row[0] for row in data]
        values = [row[1] for row in data]

        # Create pie chart
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
        ax.set_title("Knowledge Sources")
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle

        return fig
    except Exception as e:
        print(f"Error creating knowledge source chart: {e}")
        return None

def create_knowledge_graph_viz(knowledge_graph, max_nodes=50):
    """Create visualization of knowledge graph"""
    try:
        if not knowledge_graph.nodes:
            return None

        # Limit to max_nodes
        if len(knowledge_graph.nodes) > max_nodes:
            # Create a subgraph with important nodes
            # Use degree centrality to determine importance
            centrality = nx.degree_centrality(knowledge_graph)
            top_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:max_nodes]
            top_node_ids = [node[0] for node in top_nodes]

            # Create subgraph
            graph = knowledge_graph.subgraph(top_node_ids)
        else:
            graph = knowledge_graph

        # Create figure
        fig, ax = plt.subplots(figsize=(12, 10))

        # Get node types for coloring
        node_colors = []
        for node in graph.nodes:
            node_type = graph.nodes[node].get("type", "unknown")
            if node_type == "question":
                node_colors.append("blue")
            elif node_type == "answer":
                node_colors.append("green")
            elif node_type == "entity":
                node_colors.append("red")
            else:
                node_colors.append("gray")

        # Create layout
        pos = nx.spring_layout(graph, seed=42)

        # Draw nodes
        nx.draw_networkx_nodes(graph, pos, node_color=node_colors, alpha=0.7, node_size=100)

        # Draw edges
        nx.draw_networkx_edges(graph, pos, alpha=0.5, arrows=True)

        # Add labels to some important nodes
        # Limit to top 20 nodes by centrality to avoid clutter
        centrality = nx.degree_centrality(graph)
        top_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:20]
        top_node_ids = [node[0] for node in top_nodes]

        # Create labels dictionary with only important nodes
        labels = {node: str(node)[:20] + "..." if len(str(node)) > 20 else str(node) 
                  for node in graph.nodes if node in top_node_ids}

        nx.draw_networkx_labels(graph, pos, labels=labels, font_size=8)

        ax.set_title(f"Knowledge Graph (showing {len(graph.nodes)} of {len(knowledge_graph.nodes)} nodes)")
        ax.axis('off')

        return fig
    except Exception as e:
        print(f"Error creating knowledge graph visualization: {e}")
        return None

def get_image_from_fig(fig):
    """Convert a matplotlib figure to a base64 encoded image"""
    buffer = io.BytesIO()
    fig.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()

    # Encode to base64
    graphic = base64.b64encode(image_png).decode('utf-8')

    return graphic

def embed_chart_in_tkinter(parent_frame, figure):
    """Embed a matplotlib figure in a tkinter frame"""
    # Create a new frame inside the parent
    frame = ttk.Frame(parent_frame)
    frame.pack(fill=tk.BOTH, expand=True)
    
    # Create canvas
    canvas = FigureCanvasTkAgg(figure, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    return frame