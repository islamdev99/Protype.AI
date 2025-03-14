# Protype.AI

**Developed by Islam Ibrahim, Director of Carrot Studio**

![Protype.AI Logo](https://via.placeholder.com/150) <!-- Replace with actual logo URL -->

Protype.AI is an advanced conversational AI platform integrating cutting-edge technologies such as Graph Neural Networks (GNN), multimodal intelligence, self-reflection, and autonomous learning. Designed by Carrot Studio, it offers robust knowledge management, continuous learning from diverse sources, and natural user interaction through desktop and web interfaces.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Technical Architecture](#technical-architecture)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Desktop Application](#desktop-application)
  - [Web Interface](#web-interface)
  - [Dashboard](#dashboard)
  - [Teaching the System](#teaching-the-system)
  - [Continuous Learning](#continuous-learning)
- [API Endpoints](#api-endpoints)
- [Database Structure](#database-structure)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [Future Enhancements](#future-enhancements)
- [License](#license)
- [Contact](#contact)

---

## Overview

Protype.AI transcends traditional AI systems by combining symbolic reasoning, advanced memory, and multimodal capabilities. It supports continuous learning from sources like Wikipedia and Google Gemini, while allowing users to contribute custom knowledge. The system is modular, scalable, and deployable as a desktop app (Tkinter) or a web app (Flask + React).

### System Diagram (ASCII)
+----------------+       +----------------+       +----------------+
| User Interface |<----->| Learning Agent |<----->| Knowledge Graph|
+----------------+       +----------------+       +----------------+
|                        |                        |
v                        v                        v
+----------------+       +----------------+       +----------------+
| Multimodal AI  |<----->| Self-Reflection|<----->| Advanced Memory|
+----------------+       +----------------+       +----------------+

---

## Key Features

1. **Self-Reflection**
   - Critically evaluates inferences and answers using Chain of Thought (CoT).
   - Generates critical thinking questions to deepen understanding.

2. **Advanced Memory**
   - Uses FAISS and RAG for semantic search and knowledge retrieval.
   - Stores vast amounts of data efficiently.

3. **Multimodal Intelligence**
   - Processes text, images (via Gemini Vision/CLIP), and audio (text-to-speech/speech-to-text).
   - Enables natural, multi-format interaction.

4. **Autonomous Agent**
   - Sets and pursues learning goals independently.
   - Expands knowledge base without human intervention.

5. **Knowledge Graph**
   - Leverages GNNs to infer complex relationships between concepts.
   - Visualizes knowledge connections.

![Feature Icons](https://via.placeholder.com/300x100) <!-- Replace with feature icons graphic -->

---

## Technical Architecture

### Core Modules

1. **Learning Manager** (`learning_manager.py`)
   - Coordinates continuous learning from external sources.
   - Trains GNN models and manages reinforcement learning.

2. **Autonomous Agent** (`autonomous_agent.py`)
   - Manages self-directed learning goals and web research.

3. **Symbolic Reasoning** (`symbolic_reasoning.py`)
   - Solves problems using symbolic math (SymPy) and logical deduction.

4. **Self-Reflection** (`self_reflection.py`)
   - Validates inferences and answers for accuracy.

5. **Multimodal Intelligence** (`multimodal_intelligence.py`)
   - Integrates text, image, and audio processing.

6. **Temporal Awareness** (`temporal_awareness.py`)
   - Handles time-sensitive data and expressions.

7. **Knowledge Graph** (`knowledge_graph.py` + `graph_neural_network.py`)
   - Builds and manages concept relationships with NetworkX and GNNs.

8. **Search Engine** (`search_engine.py`)
   - Enhances retrieval with Elasticsearch (optional).

9. **Web App** (`web_app.py`)
   - Provides Flask-based API and React frontend.

### Data Flow (ASCII)
+----------------+    +----------------+    +----------------+
| User Input     |--> | NLP (spaCy/    |--> | Knowledge      |
| (Text/Image/   |    | Gemini)        |    | Retrieval      |
| Audio)         |    +----------------+    +----------------+
+----------------+           |                   |
|                   v                   v
+----------------+    +----------------+    +----------------+
| Reasoning      |<-->| Self-Reflection|--> | Response       |
| (Symbolic/GNN) |    +----------------+    | Generation     |
+----------------+                          +----------------+
|                                  |
v                                  v
+----------------+                   +----------------+
| Knowledge      |------------------>| Learning       |
| Storage        |                   | Updates        |
+----------------+                   +----------------+


### Key Libraries
- **AI**: `torch`, `transformers`, `torch_geometric`, `google.generativeai`, `spacy`, `sympy`
- **Data**: `networkx`, `numpy`, `elasticsearch`, `bs4`
- **Web**: `flask`, `celery`
- **Media**: `PIL`
- **Utilities**: `requests`, `json`, `datetime`, `pytz`, `dateutil`, `threading`

---

## System Requirements

### Minimum
- Python 3.7+
- 4GB RAM
- 2GB disk space

### Recommended
- Python 3.9+
- 8GB RAM
- 4GB disk space
- Internet connection
- CUDA-enabled GPU (optional)

---

## Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/Carrot-Studio/Protype.AI.git
   cd Protype.AI
pip install -r requirements.txt
# Required
GEMINI_API_KEY="your_gemini_api_key"

# Optional
SERPAPI_KEY="your_serpapi_key"
ELASTICSEARCH_URL="http://localhost:9200"
DATABASE_URL="postgresql://user:password@localhost:5432/protypeai"
REDIS_URL="redis://localhost:6379/0"
ELEVENLABS_API_KEY="your_elevenlabs_api_key"
Dashboard
Navigate to http://localhost:5000/dashboard to:

View system stats (knowledge base size, learning status).
Manage knowledge (add/edit/delete entries).
Control learning processes.
Teaching the System
Add custom knowledge programmatically:



Copy
from learning_manager import learning_manager
learning_manager.add_custom_knowledge(
    question="What is Protype.AI?",
    answer="An advanced AI system by Carrot Studio.",
    source="user"
)
Or use the dashboard:

Go to "Knowledge Management."
Click "Add New Knowledge."
Enter question, answer, and source.
Save.
Continuous Learning
Start/stop learning:



Copy
from learning_manager import learning_manager
learning_manager.start_learning()  # Start
learning_manager.stop_learning()   # Stop
Add topics:

learning_manager.add_topic("Quantum Computing")
API Endpoints
Endpoint	Method	Purpose	Example Payload
/api/chat	POST	Process user message	{"message": "What is AI?"}
/api/teach	POST	Add new knowledge	{"question": "X", "answer": "Y"}
/api/search	POST	Search knowledge base	{"query": "AI concepts"}
/api/knowledge	GET	Retrieve all knowledge	N/A
/api/text-to-speech	POST	Convert text to speech	{"text": "Hello world"}
Database Structure
Table: knowledge
Column	Type	Description	Notes
id	INTEGER	Primary key	Auto-increment
question	TEXT	Question text	Unique, indexed
answer	TEXT	Answer text	
weight	REAL	Confidence (0-1)	
source	TEXT	Source (e.g., "wikipedia")	
created_at	TIMESTAMP	Creation time	Default: CURRENT_TIMESTAMP
created_by	TEXT	Creator	Default: "system"
modified_at	TIMESTAMP	Last modified time	Default: CURRENT_TIMESTAMP
modified_by	TEXT	Last modifier	Default: "system
Developer: Islam Ibrahim
