
import matplotlib.pyplot as plt
import numpy as np
import json
import os
import io
from datetime import datetime, timedelta
import base64
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import database
import networkx as nx

def count_daily_actions(action_data, days=7):
    """Count actions per day for the last N days"""
    # Get current date and calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Initialize counters
    date_counts = {}
    for i in range(days):
        date = (end_date - timedelta(days=i)).strftime('%Y-%m-%d')
        date_counts[date] = {"chat": 0, "search": 0, "teach": 0, "other": 0}
    
    # Count actions
    for action in action_data.get("actions", []):
        try:
            timestamp = action.get("timestamp", "")
            if not timestamp:
                continue
                
            action_date = timestamp.split("T")[0]
            action_type = action.get("action", "other")
            
            # Only count actions within our date range
            action_datetime = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            if action_datetime >= start_date and action_datetime <= end_date:
                if action_date in date_counts:
                    if action_type == "chat":
                        date_counts[action_date]["chat"] += 1
                    elif action_type == "search":
                        date_counts[action_date]["search"] += 1
                    elif action_type == "teach":
                        date_counts[action_date]["teach"] += 1
                    else:
                        date_counts[action_date]["other"] += 1
        except Exception as e:
            print(f"Error processing action: {e}")
            continue
    
    # Sort by date
    sorted_dates = sorted(date_counts.keys())
    
    return sorted_dates, date_counts

def create_activity_chart(action_data, days=7):
    """Create activity chart showing user interactions over time"""
    # Get data
    dates, date_counts = count_daily_actions(action_data, days)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(8, 4))
    
    # Prepare data for plotting
    chat_counts = [date_counts[date]["chat"] for date in dates]
    search_counts = [date_counts[date]["search"] for date in dates]
    teach_counts = [date_counts[date]["teach"] for date in dates]
    
    # Create stacked bar chart
    bar_width = 0.6
    ax.bar(dates, chat_counts, bar_width, label='Chat', color='#3498db')
    ax.bar(dates, search_counts, bar_width, bottom=chat_counts, label='Search', color='#2ecc71')
    
    # Calculate the sum of chat_counts and search_counts for each date
    combined_counts = [a + b for a, b in zip(chat_counts, search_counts)]
    ax.bar(dates, teach_counts, bar_width, bottom=combined_counts, label='Teach', color='#e74c3c')
    
    # Format chart
    ax.set_title('User Activity (Last 7 Days)')
    ax.set_xlabel('Date')
    ax.set_ylabel('Number of Interactions')
    ax.legend()
    
    # Rotate date labels for better readability
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    return fig

def create_knowledge_source_chart(db_path='protype_e0.db'):
    """Create pie chart showing knowledge sources"""
    # Connect to database
    conn = database.get_connection()[0]
    cursor = conn.cursor()
    
    try:
        # Get counts by source
        cursor.execute("SELECT source, COUNT(*) FROM knowledge GROUP BY source")
        source_data = cursor.fetchall()
        
        # Close connection
        conn.close()
        
        if not source_data:
            return None
            
        # Extract data
        sources = [row[0] for row in source_data]
        counts = [row[1] for row in source_data]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(6, 6))
        
        # Create pie chart
        ax.pie(counts, labels=sources, autopct='%1.1f%%', shadow=True, startangle=90)
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
        
        plt.title('Knowledge Sources')
        plt.tight_layout()
        
        return fig
    except Exception as e:
        print(f"Error creating knowledge source chart: {e}")
        if conn:
            conn.close()
        return None

def create_knowledge_graph_viz(knowledge_graph, max_nodes=50):
    """Create visualization of the knowledge graph"""
    if not knowledge_graph or knowledge_graph.number_of_nodes() == 0:
        return None
    
    # Create a smaller subgraph for visualization
    if knowledge_graph.number_of_nodes() > max_nodes:
        # Get nodes with highest degree
        node_degrees = dict(knowledge_graph.degree())
        top_nodes = sorted(node_degrees.items(), key=lambda x: x[1], reverse=True)[:max_nodes]
        nodes_to_include = [node for node, _ in top_nodes]
        subgraph = knowledge_graph.subgraph(nodes_to_include)
    else:
        subgraph = knowledge_graph.copy()
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Define node colors by type
    node_colors = []
    for node in subgraph.nodes():
        node_type = subgraph.nodes[node].get('type', 'unknown')
        if node_type == 'question':
            node_colors.append('#3498db')  # Blue
        elif node_type == 'answer':
            node_colors.append('#2ecc71')  # Green
        elif node_type == 'entity':
            node_colors.append('#e74c3c')  # Red
        else:
            node_colors.append('#95a5a6')  # Gray
    
    # Set node sizes based on degree
    node_sizes = [100 + 10 * subgraph.degree(node) for node in subgraph.nodes()]
    
    # Create layout
    pos = nx.spring_layout(subgraph, seed=42)
    
    # Draw graph
    nx.draw_networkx(
        subgraph, 
        pos=pos, 
        with_labels=True,
        node_color=node_colors,
        node_size=node_sizes,
        font_size=8,
        width=0.5,
        edge_color='#95a5a6',
        alpha=0.8,
        ax=ax
    )
    
    # Add legend
    ax.plot([0], [0], 'o', color='#3498db', label='Question')
    ax.plot([0], [0], 'o', color='#2ecc71', label='Answer')
    ax.plot([0], [0], 'o', color='#e74c3c', label='Entity')
    ax.legend()
    
    ax.set_title('Knowledge Graph Visualization')
    ax.axis('off')
    plt.tight_layout()
    
    return fig

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
