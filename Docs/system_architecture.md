
# Protype.AI System Architecture
*Developed by Islam Ibrahim, Director of Carrot Studio*

## Overview

Protype.AI employs a modular architecture designed for flexibility, performance, and continuous learning. The system combines local intelligence with external AI capabilities to provide comprehensive responses.

## Architecture Diagram

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                             PROTYPE.AI SYSTEM                              ║
╠═══════════════╦═══════════════════════════════╦═══════════════════════════╣
║               ║                               ║                           ║
║  User         ║        Core Engine            ║     External Services     ║
║  Interfaces   ║                               ║                           ║
║               ║                               ║                           ║
║  ┌─────────┐  ║  ┌─────────────────────────┐  ║  ┌─────────────────────┐  ║
║  │ Desktop │  ║  │ Knowledge Management    │  ║  │ Google Generative   │  ║
║  │   UI    │◄─╬─►│  - Database Module      │◄─╬─►│ AI (Gemini)         │  ║
║  └─────────┘  ║  │  - Knowledge Graph      │  ║  └─────────────────────┘  ║
║               ║  │  - Version Control      │  ║                           ║
║  ┌─────────┐  ║  └─────────────────────────┘  ║  ┌─────────────────────┐  ║
║  │   Web   │  ║                               ║  │ SerpAPI             │  ║
║  │Interface│◄─╬─►┌─────────────────────────┐◄─╬─►│ (Google Search)     │  ║
║  └─────────┘  ║  │ AI Processing Pipeline  │  ║  └─────────────────────┘  ║
║               ║  │  - NLP Engine (spaCy)   │  ║                           ║
║  ┌─────────┐  ║  │  - Question Classifier  │  ║  ┌─────────────────────┐  ║
║  │ REST API│◄─╬─►│  - Response Generator   │◄─╬─►│ Wikipedia API        │  ║
║  └─────────┘  ║  └─────────────────────────┘  ║  └─────────────────────┘  ║
║               ║                               ║                           ║
╠═══════════════╬═══════════════════════════════╬═══════════════════════════╣
║               ║                               ║                           ║
║  Background   ║        Data Storage           ║   Integration Services    ║
║  Services     ║                               ║                           ║
║               ║                               ║                           ║
║  ┌─────────┐  ║  ┌─────────────────────────┐  ║  ┌─────────────────────┐  ║
║  │ Celery  │  ║  │ SQLite / PostgreSQL     │  ║  │ Elasticsearch       │  ║
║  │ Workers │◄─╬─►│  - Knowledge Database   │◄─╬─►│  - Advanced Search  │  ║
║  └─────────┘  ║  │  - User Data            │  ║  └─────────────────────┘  ║
║               ║  └─────────────────────────┘  ║                           ║
║  ┌─────────┐  ║                               ║  ┌─────────────────────┐  ║
║  │Learning │  ║  ┌─────────────────────────┐  ║  │ Text-to-Speech      │  ║
║  │ Manager │◄─╬─►│ JSON Files              │◄─╬─►│  - ElevenLabs       │  ║
║  └─────────┘  ║  │  - User Actions Log     │  ║  └─────────────────────┘  ║
║               ║  │  - System Configuration │  ║                           ║
╚═══════════════╩═══════════════════════════════╩═══════════════════════════╝
```

## Component Descriptions

### Core Engine

1. **Knowledge Management**
   - **Database Module**: Primary storage for Q&A pairs
   - **Knowledge Graph**: Relationship visualization and query enhancement
   - **Version Control**: Tracks changes to knowledge items

2. **AI Processing Pipeline**
   - **NLP Engine**: Natural language understanding using spaCy
   - **Question Classifier**: ML model to categorize question types
   - **Response Generator**: Creates contextual, intelligent responses

### User Interfaces

1. **Desktop UI**: Built with Tkinter for standalone operation
2. **Web Interface**: Flask backend serving a React frontend
3. **REST API**: Programmatic access to all system capabilities

### Background Services

1. **Celery Workers**: Distributed task processing for:
   - Background learning tasks
   - External API requests
   - Resource-intensive operations
   
2. **Learning Manager**: Coordinates the continuous learning process:
   - Schedules learning tasks
   - Monitors learning progress
   - Prioritizes learning topics

### Data Storage

1. **Relational Database**:
   - SQLite (development and small deployments)
   - PostgreSQL (production and large deployments)
   
2. **JSON Files**:
   - User action logs
   - Configuration settings
   - System state preservation

### External Services

1. **Google Generative AI**: Advanced LLM capabilities via Gemini API
2. **SerpAPI**: Real-time information retrieval from Google Search
3. **Wikipedia API**: Source for continuous learning

### Integration Services

1. **Elasticsearch**: Advanced search and knowledge indexing
2. **Text-to-Speech**: Voice response capabilities

## Data Flow

1. **User Query Processing**:
   ```
   User Input → NLP Processing → Question Classification 
   → Knowledge Lookup → (Optional External AI) → Response Generation → User Output
   ```

2. **Learning Process**:
   ```
   Topic Selection → Wikipedia Fetch → Content Processing 
   → Question Generation → Knowledge Storage → Elasticsearch Indexing
   ```

3. **Search Process**:
   ```
   Search Query → Elasticsearch Search → Database Fallback 
   → (Optional External Search) → Result Processing → User Display
   ```

## Scalability Considerations

1. **Vertical Scaling**: The system can utilize additional CPU cores and memory
2. **Horizontal Scaling**: Celery workers can be distributed across multiple machines
3. **Database Scaling**: Migration path from SQLite to PostgreSQL for larger installations
4. **Caching Layer**: Can be added between components to improve response time

## Security Architecture

1. **API Key Management**: External service credentials stored as environment variables
2. **Input Validation**: All user inputs sanitized before processing
3. **Rate Limiting**: Prevents abuse of external API services
4. **Access Control**: (Optional) User authentication for deployment scenarios

---

© 2024 Carrot Studio - Developed by Islam Ibrahim
