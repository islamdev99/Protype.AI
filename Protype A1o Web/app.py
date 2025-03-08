from flask import Flask, request, jsonify, render_template_string, send_from_directory
from flask_cors import CORS
import os
import json
import time
import database
import search_engine
from datetime import datetime
import sys
sys.path.append('.')
# Import functions from protype_s.py and main.py
try:
    from protype_s import query_external_ai, query_gemini_flash
    print("Successfully imported functions from protype_s")
except ImportError as e:
    print(f"Error importing from protype_s: {e}")
    raise

app = Flask(__name__, static_folder='frontend/build')
CORS(app)  # Enable CORS for all routes

# Initialize database
database.init_db()
print("Database initialized successfully")

# Initialize Elasticsearch if available
if hasattr(search_engine, 'HAS_ELASTICSEARCH') and search_engine.HAS_ELASTICSEARCH:
    search_engine.init_elasticsearch()
    search_engine.sync_database_to_elasticsearch()
    print("Search engine initialized successfully")

# HTML template for a simple chat interface
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Protype.AI - Developed by Islam Ibrahim</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #F7F7F8;
        }
        .container {
            display: flex;
            flex-direction: column;
            height: 100vh;
        }
        .header {
            background-color: #4a69bd;
            color: white;
            padding: 10px 20px;
            text-align: center;
            font-size: 1.5rem;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .search-area {
            display: flex;
            justify-content: center;
            gap: 5px;
            padding: 5px 0;
        }

        .search-area input {
            width: 70%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }

        .search-area button {
            padding: 8px 15px;
            background-color: #2d3e6d;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }

        .search-area button:hover {
            background-color: #1e2b4d;
        }
        .chat-area {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
        }
        .message {
            max-width: 70%;
            margin-bottom: 15px;
            padding: 10px 15px;
            border-radius: 10px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }
        .user-message {
            background-color: #DCF8C6;
            align-self: flex-end;
            border-radius: 10px 0 10px 10px;
        }
        .ai-message {
            background-color: #FFFFFF;
            align-self: flex-start;
            border-radius: 0 10px 10px 10px;
        }
        .input-area {
            display: flex;
            padding: 10px 20px;
            background-color: white;
            border-top: 1px solid #e0e0e0;
        }
        .input-area input {
            flex: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin-right: 10px;
        }
        .input-area button {
            padding: 10px 20px;
            background-color: #4a69bd;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        .typing {
            align-self: flex-start;
            background-color: #e0e0e0;
            padding: 5px 10px;
            border-radius: 10px;
            margin-bottom: 10px;
            display: none;
        }
        .message-time {
            font-size: 0.7rem;
            color: #777;
            margin-top: 5px;
            text-align: right;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            Protype.AI
            <div class="search-area">
                <input type="text" id="searchInput" placeholder="Search for knowledge...">
                <button id="searchButton">Search</button>
            </div>
        </div>
        <div class="chat-area" id="chatArea">
            <div class="message ai-message">
                Hello! I'm Protype.AI. How can I help you today? You can also use the search bar above to search my knowledge base.
                <div class="message-time">{{ current_time }}</div>
            </div>
            <div class="typing" id="typing">Protype is thinking...</div>
        </div>
        <div class="input-area">
            <input type="text" id="messageInput" placeholder="Type your message here...">
            <button id="sendButton">Send</button>
            <button id="ttsButton" title="استمع للرد" style="background-color: #7158e2; margin-left: 5px; padding: 10px 15px; border-radius: 4px; cursor: pointer; border: none; color: white; font-size: 16px;">🔊</button>
        </div>
        <div style="text-align: center; padding: 5px; font-size: 0.8rem; color: #888;">
            © 2024 Protype.AI - Developed by Islam Ibrahim - Carrot Studio
        </div>
    </div>

    <audio id="ttsAudio" style="display: none"></audio>

    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const chatArea = document.getElementById('chatArea');
            const messageInput = document.getElementById('messageInput');
            const sendButton = document.getElementById('sendButton');
            const searchInput = document.getElementById('searchInput');
            const searchButton = document.getElementById('searchButton');
            const typingIndicator = document.getElementById('typing');

            // Scroll to bottom of chat
            function scrollToBottom() {
                chatArea.scrollTop = chatArea.scrollHeight;
            }

            scrollToBottom();

            // Add a message to the chat
            function addMessage(content, isUser = false, source = null) {
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${isUser ? 'user-message' : 'ai-message'}`;

                const now = new Date();
                const timeString = now.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});

                let contentHtml = content;
                if (source) {
                    contentHtml += `<div style="font-size: 0.8rem; color: #777; margin-top: 5px;">Source: ${source}</div>`;
                }

                messageDiv.innerHTML = `
                    ${contentHtml}
                    <div class="message-time">${timeString}</div>
                `;

                chatArea.appendChild(messageDiv);
                scrollToBottom();
            }

            // Show/hide typing indicator
            function setTyping(isTyping, message = 'Protype is thinking...') {
                typingIndicator.textContent = message;
                typingIndicator.style.display = isTyping ? 'block' : 'none';
                scrollToBottom();
            }

            // Send message to backend
            async function sendMessage(message) {
                if (!message.trim()) return;

                // Add user message to chat
                addMessage(message, true);
                messageInput.value = '';

                // Show typing indicator
                setTyping(true);

                try {
                    const response = await fetch('/api/chat', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ message }),
                    });

                    const data = await response.json();

                    // Hide typing indicator
                    setTyping(false);

                    // Add AI response to chat
                    if (data.message) {
                        addMessage(data.message, false, data.source);
                    } else {
                        addMessage('Sorry, I encountered an error. Please try again.');
                    }
                } catch (error) {
                    console.error('Error:', error);
                    setTyping(false);
                    addMessage('Sorry, I encountered an error. Please try again.');
                }
            }

            // Search the knowledge base
            async function searchKnowledge(query) {
                if (!query.trim()) return;

                // Add user search message to chat
                addMessage(`Searching for: ${query}`, true);
                searchInput.value = '';

                // Show typing indicator
                setTyping(true, 'Searching knowledge base...');

                try {
                    const response = await fetch('/api/search', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ query }),
                    });

                    const data = await response.json();

                    // Hide typing indicator
                    setTyping(false);

                    // Display search results
                    if (Array.isArray(data) && data.length > 0) {
                        // Multiple results
                        addMessage(`I found ${data.length} results for "${query}":`, false, 'search');

                        // Display first result in detail
                        const firstResult = data[0];
                        addMessage(`Q: ${firstResult.question}<br>A: ${firstResult.answer}`, false, firstResult.source);

                        // Mention other results if present
                        if (data.length > 1) {
                            let otherQuestions = data.slice(1, 4).map(item => item.question).join('<br>• ');
                            addMessage(`Related questions:<br>• ${otherQuestions}`, false, 'search');
                        }
                    } else if (data.answer || data.message) {
                        // Single result
                        const answer = data.answer || data.message;
                        const question = data.question || query;
                        addMessage(`Q: ${question}<br>A: ${answer}`, false, data.source);
                    } else {
                        addMessage(`I couldn't find any information about "${query}". I'll learn about it for next time.`, false, 'system');
                    }
                } catch (error) {
                    console.error('Search error:', error);
                    setTyping(false);
                    addMessage(`Sorry, I encountered an error while searching for "${query}".`);
                }
            }

            // Text-to-speech functionality
            const ttsButton = document.getElementById('ttsButton');
            const ttsAudio = document.getElementById('ttsAudio');
            let lastAiMessage = '';

            // Update addMessage to store the last AI message
            const originalAddMessage = addMessage;
            addMessage = function(content, isUser = false, source = null) {
                if (!isUser) {
                    lastAiMessage = content;
                }
                originalAddMessage(content, isUser, source);
            };

            // TTS button click handler
            ttsButton.addEventListener('click', async () => {
                if (!lastAiMessage) return;

                ttsButton.disabled = true;
                ttsButton.innerHTML = '⏳';
                
                // Remove HTML tags from message for speech
                const textToSpeak = lastAiMessage.replace(/<[^>]*>/g, '');

                try {
                    const response = await fetch('/api/text-to-speech', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ text: textToSpeak }),
                    });

                    if (response.ok) {
                        const data = await response.json();
                        if (data.audio) {
                            ttsAudio.src = 'data:audio/mpeg;base64,' + data.audio;
                            await ttsAudio.play();
                            console.log("Playing audio response");
                        } else if (data.error) {
                            console.error('TTS Error:', data.error);
                        }
                    } else {
                        console.error('TTS Error: Failed to convert text to speech');
                    }
                } catch (error) {
                    console.error('TTS Error:', error);
                } finally {
                    ttsButton.disabled = false;
                    ttsButton.innerHTML = '🔊';
                }
            });
            
            // Add ended event to audio element
            ttsAudio.addEventListener('ended', () => {
                console.log("Audio playback completed");
                ttsButton.disabled = false;
                ttsButton.innerHTML = '🔊';
            });

            // Event listeners
            sendButton.addEventListener('click', () => {
                sendMessage(messageInput.value);
            });

            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    sendMessage(messageInput.value);
                }
            });

            // Search event listeners
            searchButton.addEventListener('click', () => {
                searchKnowledge(searchInput.value);
            });

            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    searchKnowledge(searchInput.value);
                }
            });
        });
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    current_time = datetime.now().strftime('%H:%M')
    return render_template_string(HTML_TEMPLATE, current_time=current_time)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '')

    if not message:
        return jsonify({'error': 'Message is required'}), 400

    # Log the chat action
    log_action("user", "chat", f"Asked: {message}")

    # If it's a command
    if message.startswith('/'):
        return handle_command(message)

    # First try to search for answer in knowledge base
    results = []
    if hasattr(search_engine, 'HAS_ELASTICSEARCH') and search_engine.HAS_ELASTICSEARCH:
        results = search_engine.search(message, limit=3)

    if results:
        if isinstance(results[0], dict):  # Elasticsearch result format
            return jsonify({
                'message': results[0]['answer'],
                'source': results[0]['source']
            })
        else:  # Database result format
            return jsonify({
                'message': results[0][1],
                'source': results[0][3]
            })

    # If not found, query database directly
    data = database.load_data()
    for question in data:
        if message.lower() in question.lower():
            return jsonify({
                'message': data[question][0]['answer'],
                'source': data[question][0]['source']
            })

    # If still no answers, try direct Gemini API from protype_s.py
    try:
        print(f"Trying direct Gemini response for: {message}")
        from protype_s import query_gemini_flash

        # Get direct response
        gemini_response = query_gemini_flash(message)
        if gemini_response:
            # Save to database for future reference
            database.save_data(message, gemini_response, 0.7, "gemini_flash_direct", "user")

            print(f"Got direct Gemini response: {gemini_response[:50]}...")
            return jsonify({
                'message': gemini_response,
                'source': 'gemini_direct'
            })
    except Exception as direct_e:
        print(f"Error getting direct response from Gemini: {direct_e}")

        # Fall back to Celery task
        try:
            from celery_tasks import learn_from_gemini_flash
            # Immediately get response from Gemini for the user
            gemini_response = learn_from_gemini_flash.apply(args=[message]).get(timeout=10)
            if gemini_response and 'status' in gemini_response and gemini_response['status'] == 'success':
                return jsonify({
                    'message': gemini_response.get('answer_full', gemini_response.get('answer_snippet', 'I found an answer but had trouble retrieving it fully.')),
                    'source': 'gemini'
                })
        except Exception as e:
            print(f"Error getting immediate response from Gemini: {e}")
            # Still trigger background learning for next time
            try:
                # Import again in the except block to ensure it's defined
                from celery_tasks import learn_from_gemini_flash
                learn_from_gemini_flash.delay(message)
            except Exception as inner_e:
                print(f"Error triggering background learning: {inner_e}")

    # Create a more intelligent fallback response
    return jsonify({
        'message': "I'm searching for information about this topic. I don't have a complete answer yet, but I'm learning about it. Feel free to check back soon or rephrase your question!",
        'source': 'system'
    })

@app.route('/api/teach', methods=['POST'])
def teach():
    data = request.json
    question = data.get('question', '')
    answer = data.get('answer', '')

    if not question or not answer:
        return jsonify({'error': 'Question and answer are required'}), 400

    # Save to database
    success = database.save_data(question, answer, 0.5, "user", "user")

    if success:
        # Log the action
        log_action("user", "teach", f"Added new knowledge: {question}")

        # Index in Elasticsearch if available
        if hasattr(search_engine, 'HAS_ELASTICSEARCH') and search_engine.HAS_ELASTICSEARCH:
            search_engine.index_document(question, answer, 0.5, "user")

        return jsonify({'success': True, 'message': 'Knowledge saved successfully'})

    return jsonify({'success': False, 'message': 'Failed to save knowledge'})

def handle_command(command):
    """Handle special commands starting with /"""
    cmd = command.lower().strip()

    if cmd.startswith('/learn '):
        topic = cmd[7:].strip()
        if topic:
            # Simulate learning process
            return jsonify({
                'message': f"I've started learning about '{topic}'. Ask me about it soon!",
                'source': 'system'
            })

    elif cmd == '/stats':
        # Get knowledge base stats
        data = database.load_data()
        question_count = len(data.keys()) if data else 0

        message = f"I currently know {question_count} questions and answers."
        return jsonify({'message': message, 'source': 'system'})

    # Default response for unknown commands
    return jsonify({
        'message': "Unknown command. Try /learn [topic] or /stats",
        'source': 'system'
    })

def log_action(user, action_type, description, details=None):
    """Log user actions for analytics"""
    import datetime

    try:
        # Read existing log
        try:
            with open('user_actions.json', 'r') as f:
                action_log = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            action_log = {
                "version": "1.0",
                "actions": []
            }

        # Add new action
        action = {
            "timestamp": datetime.datetime.now().isoformat(),
            "user": user,
            "action": action_type,
            "description": description
        }

        if details:
            action["details"] = details

        action_log["actions"].append(action)

        # Save log
        with open('user_actions.json', 'w') as f:
            json.dump(action_log, f, indent=2)

        return True
    except Exception as e:
        print(f"Error logging action: {e}")
        return False

# API endpoints for React frontend
@app.route('/api/knowledge', methods=['GET'])
def get_knowledge():
    """Get all knowledge items for the frontend"""
    data = database.load_data()
    result = []
    for question, answers in data.items():
        result.append({
            "question": question,
            "answer": answers[0]["answer"],
            "source": answers[0]["source"],
            "weight": answers[0]["weight"]
        })
    return jsonify(result)

@app.route('/api/learn', methods=['POST'])
def learn():
    """Learn from user input"""
    data = request.json
    question = data.get('question', '')
    answer = data.get('answer', '')

    if not question or not answer:
        return jsonify({'error': 'Question and answer are required'}), 400

    # Save to database
    success = database.save_data(question, answer, 0.6, "user", "frontend")

    if success:
        # Log the action
        log_action("user", "teach", f"Added knowledge via frontend: {question}")

        # Index in Elasticsearch if available
        if hasattr(search_engine, 'HAS_ELASTICSEARCH') and search_engine.HAS_ELASTICSEARCH:
            search_engine.index_document(question, answer, 0.6, "user")

        return jsonify({'success': True, 'message': 'Knowledge saved successfully'})

    return jsonify({'success': False, 'message': 'Failed to save knowledge'})

@app.route('/api/search', methods=['POST'])
def api_search():
    """Search API endpoint for the frontend"""
    data = request.json
    query = data.get('query', '')

    if not query:
        return jsonify({'error': 'Search query is required'}), 400

    # Log the search action
    log_action("user", "search", f"Searched via frontend: {query}")
    print(f"Searching for: {query}")

    # First try to search for answer in knowledge base
    results = []
    try:
        if hasattr(search_engine, 'HAS_ELASTICSEARCH') and search_engine.HAS_ELASTICSEARCH:
            results = search_engine.search(query, limit=5)
            print(f"Elasticsearch results: {len(results) if results else 0}")

            if results:
                return jsonify(results)
    except Exception as es_error:
        print(f"Elasticsearch search error: {es_error}")

    # If no Elasticsearch results, query database directly
    try:
        print("Searching in database...")
        data = database.load_data()
        for question in data:
            if query.lower() in question.lower():
                print(f"Found match in database: {question}")
                return jsonify({
                    'question': question,
                    'answer': data[question][0]['answer'],
                    'source': data[question][0]['source']
                })
    except Exception as db_error:
        print(f"Database search error: {db_error}")

    # If still no results, try direct Gemini Flash query
    try:
        print("Querying Gemini Flash directly...")
        from protype_s import query_gemini_flash
        gemini_response = query_gemini_flash(query)

        # Save the response for future reference
        database.save_data(query, gemini_response, 0.7, "gemini_flash_direct", "search_api")

        # Also trigger background learning
        try:
            from celery_tasks import learn_from_gemini_flash
            learn_from_gemini_flash.delay(query)
        except Exception as celery_error:
            print(f"Celery task error: {celery_error}")

        return jsonify({
            'question': query,
            'answer': gemini_response,
            'source': 'gemini_flash_direct'
        })
    except Exception as gemini_error:
        print(f"Gemini Flash query error: {gemini_error}")

        # Last resort: perform background learning and return generic message
        try:
            from celery_tasks import learn_from_gemini_flash
            learn_from_gemini_flash.delay(query)
        except:
            pass

        return jsonify({
            'question': query,
            'answer': "I'm searching for information about this topic. I don't have a complete answer yet, but I'm learning about it. Feel free to check back soon or rephrase your question!",
            'source': 'system'
        })

# Serve React app
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

# Add a new route for text-to-speech
@app.route('/api/text-to-speech', methods=['POST'])
def text_to_speech():
    try:
        data = request.json
        text = data.get('text', '')
        if not text:
            return jsonify({'error': 'Text is required'}), 400

        # Use our text_to_speech module to convert text to speech
        from text_to_speech import text_to_speech as tts
        
        # Default voice ID for Adam voice
        voice_id = "pNInz6obpgDQGcFmaJgB"  # Adam voice
        
        # If text is in Arabic, use Arabic voice
        if any('\u0600' <= c <= '\u06FF' for c in text):
            voice_id = "21m00Tcm4TlvDq8ikWAM"  # Arabic-compatible voice
            
        audio_base64 = tts(text, voice_id=voice_id)
        
        if audio_base64:
            return jsonify({'audio': audio_base64})
        else:
            return jsonify({'error': 'Failed to generate speech'}), 500

    except Exception as e:
        print(f"Text-to-speech error: {e}")
        return jsonify({'error': f'Text-to-speech failed: {str(e)}'}), 500



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)