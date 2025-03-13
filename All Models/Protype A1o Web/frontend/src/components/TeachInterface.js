
import React, { useState } from 'react';
import './TeachInterface.css';

function TeachInterface({ darkMode }) {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [status, setStatus] = useState({ message: '', type: '' });
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!question.trim() || !answer.trim()) {
      setStatus({
        message: 'Please fill in both question and answer fields.',
        type: 'error'
      });
      return;
    }
    
    setIsLoading(true);
    
    try {
      const response = await fetch('/api/teach', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question, answer }),
      });
      
      const data = await response.json();
      
      if (data.success) {
        setStatus({
          message: 'Thank you! I\'ve learned something new!',
          type: 'success'
        });
        setQuestion('');
        setAnswer('');
      } else {
        setStatus({
          message: data.message || 'Failed to save knowledge. Please try again.',
          type: 'error'
        });
      }
    } catch (error) {
      console.error('Error teaching:', error);
      setStatus({
        message: 'An error occurred. Please try again later.',
        type: 'error'
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`teach-container ${darkMode ? 'dark-theme' : 'light-theme'}`}>
      <div className="teach-header">
        <h2>Teach Protype.AI</h2>
        <p>Share your knowledge with me! I'll remember what you teach me.</p>
      </div>
      
      <form onSubmit={handleSubmit} className="teach-form">
        <div className="form-group">
          <label htmlFor="question">Question</label>
          <input
            id="question"
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Enter a question..."
            disabled={isLoading}
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="answer">Answer</label>
          <textarea
            id="answer"
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            placeholder="Enter the answer..."
            rows={5}
            disabled={isLoading}
          />
        </div>
        
        {status.message && (
          <div className={`status-message ${status.type}`}>
            {status.message}
          </div>
        )}
        
        <button type="submit" disabled={isLoading}>
          {isLoading ? 'Saving...' : 'Teach Me'}
        </button>
      </form>
    </div>
  );
}

export default TeachInterface;
