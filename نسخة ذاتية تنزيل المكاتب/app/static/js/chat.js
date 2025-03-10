
/**
 * Chat Functionality for Protype.AI
 * Handles all chat interactions, message sending, and responses
 */

// DOM elements
const chatInput = document.getElementById('chat-input');
const sendButton = document.getElementById('send-btn');
const chatMessages = document.getElementById('chat-messages');
const voiceInputButton = document.getElementById('voice-input-btn');
const audioFeedback = document.getElementById('audio-feedback');

// Chat state
let isAwaitingResponse = false;
let chatHistory = [];

// Initialize chat functionality
function initChat() {
    // Set up event listeners
    sendButton.addEventListener('click', sendMessage);
    chatInput.addEventListener('keydown', e => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    // Set up audio buttons in chat
    setupAudioButtons();
    
    // Load chat history from localStorage if available
    loadChatHistory();
}

// Send a message to the AI
function sendMessage() {
    const message = chatInput.value.trim();
    
    if (message === '' || isAwaitingResponse) return;
    
    // Add user message to chat
    addMessageToChat('user', message);
    
    // Clear input
    chatInput.value = '';
    
    // Set awaiting response state
    isAwaitingResponse = true;
    
    // Send message to server
    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ question: message })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Add AI response to chat
            addMessageToChat('bot', data.answer, data.source);
            
            // Auto-play TTS if enabled
            if (document.getElementById('auto-tts-switch').checked) {
                playTextToSpeech(data.answer);
            }
        } else {
            // Handle error
            addMessageToChat('bot', 'Sorry, I encountered an error. Please try again.');
        }
        isAwaitingResponse = false;
    })
    .catch(error => {
        console.error('Error:', error);
        addMessageToChat('bot', 'Sorry, there was a network error. Please try again.');
        isAwaitingResponse = false;
    });
}

// Add a message to the chat window
function addMessageToChat(type, message, source = null) {
    // Create message elements
    const messageElement = document.createElement('div');
    messageElement.className = `message ${type} slide-in`;
    
    const contentElement = document.createElement('div');
    contentElement.className = 'message-content';
    
    // Set message content
    const messageText = document.createElement('p');
    messageText.textContent = message;
    contentElement.appendChild(messageText);
    
    // Add source if provided
    if (source && type === 'bot') {
        const sourceEl = document.createElement('small');
        sourceEl.className = 'text-muted';
        sourceEl.textContent = `Source: ${source}`;
        contentElement.appendChild(sourceEl);
    }
    
    messageElement.appendChild(contentElement);
    
    // Add TTS button for bot messages
    if (type === 'bot') {
        const actionsElement = document.createElement('div');
        actionsElement.className = 'message-actions';
        
        const audioButton = document.createElement('button');
        audioButton.className = 'btn btn-sm btn-audio';
        audioButton.innerHTML = '<i class="fas fa-volume-up"></i>';
        audioButton.dataset.text = message;
        
        actionsElement.appendChild(audioButton);
        messageElement.appendChild(actionsElement);
    }
    
    // Add message to chat and scroll to bottom
    chatMessages.appendChild(messageElement);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Add to chat history
    chatHistory.push({
        type: type,
        message: message,
        source: source,
        timestamp: new Date().toISOString()
    });
    
    // Save chat history to localStorage
    saveChatHistory();
}

// Save chat history to localStorage
function saveChatHistory() {
    // Keep only the last 50 messages
    if (chatHistory.length > 50) {
        chatHistory = chatHistory.slice(-50);
    }
    
    localStorage.setItem('protype_chat_history', JSON.stringify(chatHistory));
}

// Load chat history from localStorage
function loadChatHistory() {
    const savedHistory = localStorage.getItem('protype_chat_history');
    
    if (savedHistory) {
        try {
            const history = JSON.parse(savedHistory);
            
            // Clear current chat
            chatMessages.innerHTML = '';
            
            // Add messages from history
            for (const item of history) {
                addMessageToChat(item.type, item.message, item.source);
            }
            
            // Set chat history
            chatHistory = history;
        } catch (error) {
            console.error('Error loading chat history:', error);
        }
    }
}

// Setup audio buttons in chat
function setupAudioButtons() {
    // Use event delegation for dynamically added buttons
    chatMessages.addEventListener('click', function(event) {
        const audioButton = event.target.closest('.btn-audio');
        
        if (audioButton) {
            const text = audioButton.dataset.text;
            playTextToSpeech(text);
        }
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initChat);
