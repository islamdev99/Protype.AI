
import React, { useState } from 'react';
import './SearchInterface.css';

function SearchInterface({ darkMode }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSearch = async (e) => {
    e.preventDefault();
    
    if (!query.trim()) {
      setError('Please enter a search query');
      return;
    }
    
    setIsLoading(true);
    setError('');
    
    try {
      const response = await fetch('/api/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      });
      
      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error('Error searching:', error);
      setError('An error occurred while searching. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`search-container ${darkMode ? 'dark-theme' : 'light-theme'}`}>
      <div className="search-header">
        <h2>Search & Learn</h2>
        <p>Search for information or ask me to learn about a topic!</p>
      </div>
      
      <form onSubmit={handleSearch} className="search-form">
        <div className="search-input-container">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search for something..."
            disabled={isLoading}
          />
          <button type="submit" disabled={isLoading}>
            {isLoading ? 'Searching...' : 'Search'}
          </button>
        </div>
        
        {error && <div className="search-error">{error}</div>}
      </form>
      
      {results && (
        <div className="search-results">
          <h3>Results</h3>
          
          {results.message && (
            <div className="search-result-item">
              <p className="search-result-content">{results.message}</p>
              {results.source && <p className="search-result-source">Source: {results.source}</p>}
            </div>
          )}
          
          {results.length > 0 && results.map((result, index) => (
            <div key={index} className="search-result-item">
              <h4>{result.question || 'Result'}</h4>
              <p className="search-result-content">{result.answer || result.snippet}</p>
              {result.source && <p className="search-result-source">Source: {result.source}</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default SearchInterface;
