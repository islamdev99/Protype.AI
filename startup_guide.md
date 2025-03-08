
# Protype.AI Startup Guide
*Developed by Islam Ibrahim, Director of Carrot Studio*

This guide provides detailed instructions for starting and operating Protype.AI in different modes.

## Starting the Web Application

1. **Install dependencies first:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the Flask web server:**
   ```bash
   python app.py
   ```
   
   The web application will be available at `http://localhost:3000` (or the configured port)

3. **Access the interface** through your web browser.

## Starting the Desktop Application

1. **Install dependencies if not already installed:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Launch the desktop interface:**
   ```bash
   python main.py
   ```

3. **Use the tabbed interface** to interact with the system:
   - **Teach Tab**: Add new knowledge
   - **Search Tab**: Perform searches
   - **Chat Tab**: Interact conversationally
   - **Dashboard Tab**: View system analytics

## Using the System

### Teaching New Information
1. Navigate to the Teach tab
2. Enter a question in the question field
3. Enter the corresponding answer in the answer field
4. Click "Teach Me" to save the knowledge

### Searching for Information
1. Navigate to the Search tab
2. Enter your search query
3. Click "Search" to retrieve information

### Chatting with the AI
1. Navigate to the Chat tab
2. Type your question or message
3. Click "Ask Me" or press Enter to send

### Managing the Knowledge Base
1. Use the dashboard to view system statistics
2. Monitor the knowledge growth over time
3. Analyze the most frequently accessed information

## Advanced Operations

### Starting Continuous Learning
1. From the dashboard, click "Start Learning"
2. The system will begin gathering information in the background
3. Monitor the learning progress in the Activity Log

### Syncing with Elasticsearch
1. Ensure Elasticsearch is configured
2. From the dashboard, click "Sync Elasticsearch"
3. Wait for confirmation that synchronization is complete

### Batch Learning Process
1. From the dashboard, click "Batch Learning"
2. The system will initiate learning on predefined topics
3. Progress will be tracked in the Activity Log

---

For technical support, please contact support@carrotstudio.com

© 2024 Carrot Studio - Developed by Islam Ibrahim
