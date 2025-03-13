
import React, { useState } from 'react';
import './Sidebar.css';

function Sidebar({ activeTab, setActiveTab, toggleTheme, darkMode }) {
  const [expanded, setExpanded] = useState(false);
  
  const toggleSidebar = () => {
    setExpanded(!expanded);
  };

  return (
    <div className={`sidebar ${expanded ? 'expanded' : 'collapsed'} ${darkMode ? 'dark-theme' : 'light-theme'}`}>
      <button className="toggle-btn" onClick={toggleSidebar}>
        {expanded ? '×' : '☰'}
      </button>
      
      {expanded && (
        <nav className="sidebar-nav">
          <button 
            className={activeTab === 'chat' ? 'active' : ''} 
            onClick={() => setActiveTab('chat')}
          >
            💬 Chat
          </button>
          
          <button 
            className={activeTab === 'teach' ? 'active' : ''} 
            onClick={() => setActiveTab('teach')}
          >
            🧠 Teach
          </button>
          
          <button 
            className={activeTab === 'search' ? 'active' : ''} 
            onClick={() => setActiveTab('search')}
          >
            🔍 Search
          </button>
          
          <button onClick={toggleTheme}>
            {darkMode ? '☀️ Light Mode' : '🌙 Dark Mode'}
          </button>
        </nav>
      )}
    </div>
  );
}

export default Sidebar;
