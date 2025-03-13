
import React, { useState, useEffect, useRef } from 'react';
import './ChatInterface.css';

function ChatInterface({ darkMode }) {
  const [messages, setMessages] = useState([
    { sender: 'ai', content: "Hello! I'm Protype.AI. How can I help you today?" }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(scrollToBottom, [messages]);

  const sendMessage = async (e) => {
    e.preventDefault();
    
    if (!input.trim()) return;
    
    // Add user message
    setMessages([...messages, { sender: 'user', content: input }]);
    setIsLoading(true);
    
    // Call the API
    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: input }),
      });
      
      const data = await response.json();
      
      // Add AI response
      setMessages(msgs => [...msgs, { 
        sender: 'ai', 
        content: data.message || "Sorry, I couldn't process that request."
      }]);
      
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(msgs => [...msgs, { 
        sender: 'ai', 
        content: "Sorry, an error occurred while processing your request."
      }]);
    } finally {
      setIsLoading(false);
      setInput('');
    }
  };

  return (
    <div className={`chat-container ${darkMode ? 'dark-theme' : 'light-theme'}`}>
      <div className="chat-header">
        <h2>Chat with Protype.AI</h2>
      </div>
      
      <div className="messages-container">
        {messages.map((message, index) => (
          <div key={index} className={`message ${message.sender}`}>
            <div className="message-content">{message.content}</div>
          </div>
        ))}
        
        {isLoading && (
          <div className="message ai">
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      <form className="input-area" onSubmit={sendMessage}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message here..."
          disabled={isLoading}
        />
        <button type="submit" disabled={isLoading}>Send</button>
      </form>
    </div>
  );
}

export default ChatInterface;
