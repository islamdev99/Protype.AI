
# Protype.AI - Official Documentation
*Developed by Islam Ibrahim, Director of Carrot Studio*

## Overview

Protype.AI is an advanced conversational AI platform built with a hybrid architecture that combines local intelligence with external AI capabilities. The system features both a desktop application built with Tkinter and a web interface built with Flask and React, allowing for flexible deployment options.

## Core Components

### 1. Knowledge Management System
- **SQLite/PostgreSQL Database**: Stores structured knowledge as question-answer pairs
- **Elasticsearch Integration**: Provides advanced search capabilities (when available)
- **Knowledge Graph**: Visualizes relationships between concepts using NetworkX

### 2. AI Integration
- **Gemini Flash Integration**: Connects to Google's Generative AI for advanced responses
- **Custom NLP Pipeline**: Uses spaCy for natural language understanding
- **Question Classification**: ML-based system for tailoring responses by question type

### 3. Learning Systems
- **Continuous Learning**: Background processes autonomously gather knowledge
- **User-Directed Learning**: Interface for users to directly teach the system
- **Wikipedia Integration**: Automatically harvests knowledge from Wikipedia

### 4. User Interfaces
- **Desktop Application**: Built with Python Tkinter for local deployment
- **Web Interface**: Modern React frontend with Flask backend
- **Chat Dashboard**: Analytics and management interface for system administrators

## Technical Architecture

### Backend Services
- **Flask Web Server**: Core API endpoints and web service
- **Celery Tasks**: Background processing for continuous learning
- **Search Engine**: Elasticsearch-based knowledge retrieval
- **Database Module**: Persistence layer with both SQLite and PostgreSQL support
- **Learning Manager**: Controls the continuous learning processes

### Frontend Components
- **React Application**: Modern, responsive web interface
- **Tkinter Desktop UI**: Standalone desktop application
- **Analytics Dashboard**: System monitoring and performance metrics

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/chat` | POST | Process user message and return AI response |
| `/api/teach` | POST | Add new knowledge to the system |
| `/api/search` | POST | Search knowledge base for specific information |
| `/api/knowledge` | GET | Retrieve all knowledge items |
| `/api/text-to-speech` | POST | Convert text response to speech |

## Operation Modes

### Chat Mode
Interactive dialogue with the AI, leveraging both stored knowledge and external intelligence when needed.

### Teach Mode
Allows users to directly contribute knowledge by providing question-answer pairs.

### Search Mode
Targeted information retrieval using both internal knowledge and external search capabilities.

## System Requirements

### Minimum Requirements
- Python 3.7+ 
- 4GB RAM
- 2GB available disk space

### Recommended Requirements
- Python 3.9+
- 8GB RAM
- 4GB available disk space
- Internet connection for external AI capabilities

## Installation Guide

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-repo/Protype.AI.git
   cd Protype.AI
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Download Required Models**
   ```bash
   python -m spacy download en_core_web_sm
   ```

4. **Initialize Database**
   ```bash
   python setup_db.py
   ```

5. **Start the Application**
   
   For Desktop Application:
   ```bash
   python main.py
   ```
   
   For Web Interface:
   ```bash
   python app.py
   ```

## Configuration

The system can be configured using environment variables:

- `GEMINI_API_KEY`: API key for Google Generative AI
- `SERPAPI_KEY`: API key for SerpAPI (Google Search integration)
- `ELASTICSEARCH_URL`: Connection URL for Elasticsearch
- `DATABASE_URL`: PostgreSQL connection URL
- `REDIS_URL`: Redis connection URL for Celery

## Deployment

### Desktop Deployment
The desktop application can be packaged into an executable using PyInstaller:

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole main.py
```

### Web Deployment
The web application can be deployed to any Python-compatible web hosting service:

1. Build the React frontend:
   ```bash
   cd frontend
   npm install
   npm run build
   ```

2. Start the Flask server:
   ```bash
   python app.py
   ```

## License
Proprietary software developed by Carrot Studio. All rights reserved.

---

© 2024 Carrot Studio - Developed by Islam Ibrahim
