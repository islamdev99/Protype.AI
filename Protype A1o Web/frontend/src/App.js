import React, { useState, useEffect } from 'react';
import './App.css';

// Components
import ChatInterface from './components/ChatInterface';
import Sidebar from './components/Sidebar';
import TeachInterface from './components/TeachInterface';
import SearchInterface from './components/SearchInterface';

function App() {
  const [activeTab, setActiveTab] = useState('chat');
  const [darkMode, setDarkMode] = useState(true);
  const [knowledge, setKnowledge] = useState([]);

  // Fetch knowledge from backend
  useEffect(() => {
    const fetchKnowledge = async () => {
      try {
        const response = await fetch('/api/knowledge');
        const data = await response.json();
        setKnowledge(data);
      } catch (error) {
        console.error('Error fetching knowledge:', error);
      }
    };

    fetchKnowledge();
  }, []);

  // Toggle dark/light mode
  const toggleTheme = () => {
    setDarkMode(!darkMode);
    document.body.classList.toggle('dark-mode', !darkMode);
  };

  return (
    <div className={`app-container ${darkMode ? 'dark-theme' : 'light-theme'}`}>
      <Sidebar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        toggleTheme={toggleTheme} 
        darkMode={darkMode} 
        knowledge={knowledge} // Pass knowledge to Sidebar for stats display
      />

      <main className="main-content">
        {activeTab === 'chat' && <ChatInterface darkMode={darkMode} />}
        {activeTab === 'teach' && <TeachInterface darkMode={darkMode} />}
        {activeTab === 'search' && <SearchInterface darkMode={darkMode} />}
      </main>
    </div>
  );
}

export default App;