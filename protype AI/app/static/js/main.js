
/**
 * Main JavaScript for Protype.AI
 * Handles initialization and common functionality
 */

// DOM elements
const learningStatusDot = document.getElementById('learning-status-dot');
const learningStatusText = document.getElementById('learning-status-text');
const toggleLearningBtn = document.getElementById('toggle-learning-btn');
const toggleLearningText = document.getElementById('toggle-learning-text');

// Application state
let isLearningActive = true;

// Initialize application
function initApp() {
    // Check learning status
    checkLearningStatus();
    
    // Set up learning toggle
    toggleLearningBtn.addEventListener('click', toggleLearning);
    
    // Setup teach functionality
    setupTeachFunctionality();
    
    // Setup search functionality
    setupSearchFunctionality();
    
    // Setup dashboard
    setupDashboard();
    
    // Setup interval control
    const learningInterval = document.getElementById('learning-interval');
    const intervalDisplay = document.getElementById('interval-display');
    
    learningInterval.addEventListener('input', function() {
        intervalDisplay.textContent = `${this.value}s`;
    });
}

// Check learning status
function checkLearningStatus() {
    fetch('/learning-logs')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success' && data.logs.length > 0) {
                // Get most recent log
                const recentLog = data.logs[data.logs.length - 1];
                
                // Check if learning is active
                if (recentLog.action === 'stopped') {
                    setLearningInactive();
                } else {
                    setLearningActive();
                }
            }
        })
        .catch(error => {
            console.error('Error checking learning status:', error);
        });
}

// Set learning status active
function setLearningActive() {
    learningStatusDot.classList.add('active');
    learningStatusText.textContent = 'Learning Active';
    toggleLearningText.textContent = 'Stop Learning';
    isLearningActive = true;
}

// Set learning status inactive
function setLearningInactive() {
    learningStatusDot.classList.remove('active');
    learningStatusText.textContent = 'Learning Inactive';
    toggleLearningText.textContent = 'Start Learning';
    isLearningActive = false;
}

// Toggle learning status
function toggleLearning() {
    if (isLearningActive) {
        // Stop learning
        fetch('/stop-learning', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                setLearningInactive();
            }
        })
        .catch(error => {
            console.error('Error stopping learning:', error);
        });
    } else {
        // Start learning
        fetch('/start-learning', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                setLearningActive();
            }
        })
        .catch(error => {
            console.error('Error starting learning:', error);
        });
    }
}

// Setup teach functionality
function setupTeachFunctionality() {
    const teachButton = document.getElementById('teach-btn');
    const teachQuestion = document.getElementById('teach-question');
    const teachAnswer = document.getElementById('teach-answer');
    const teachResult = document.getElementById('teach-result');
    
    teachButton.addEventListener('click', function() {
        const question = teachQuestion.value.trim();
        const answer = teachAnswer.value.trim();
        
        if (question === '' || answer === '') {
            alert('Please enter both a question and an answer.');
            return;
        }
        
        // Disable button
        teachButton.setAttribute('disabled', 'disabled');
        teachButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...';
        
        // Send to server
        fetch('/teach', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question, answer })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Show success message
                teachResult.textContent = 'Knowledge saved successfully!';
                teachResult.style.display = 'block';
                
                // Clear inputs
                teachQuestion.value = '';
                teachAnswer.value = '';
                
                // Hide message after 3 seconds
                setTimeout(() => {
                    teachResult.style.display = 'none';
                }, 3000);
            } else {
                alert('Error: ' + data.message);
            }
            
            // Enable button
            teachButton.removeAttribute('disabled');
            teachButton.textContent = 'Submit';
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error submitting knowledge. Please try again.');
            
            // Enable button
            teachButton.removeAttribute('disabled');
            teachButton.textContent = 'Submit';
        });
    });
}

// Setup search functionality
function setupSearchFunctionality() {
    const searchButton = document.getElementById('search-btn');
    const searchQuery = document.getElementById('search-query');
    const searchResults = document.getElementById('search-results');
    
    searchButton.addEventListener('click', function() {
        const query = searchQuery.value.trim();
        
        if (query === '') {
            alert('Please enter a search query.');
            return;
        }
        
        // Show loading
        searchResults.innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin"></i> Searching...</div>';
        
        // Send to server
        fetch('/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Clear results
                searchResults.innerHTML = '';
                
                if (data.results.length === 0) {
                    searchResults.innerHTML = '<div class="alert alert-info">No results found.</div>';
                    return;
                }
                
                // Add results
                data.results.forEach(result => {
                    const resultDiv = document.createElement('div');
                    resultDiv.className = 'card mb-3';
                    
                    const cardBody = document.createElement('div');
                    cardBody.className = 'card-body';
                    
                    const title = document.createElement('h5');
                    title.className = 'card-title';
                    title.textContent = result.question;
                    
                    const content = document.createElement('p');
                    content.className = 'card-text';
                    content.textContent = result.answer;
                    
                    const source = document.createElement('small');
                    source.className = 'text-muted';
                    source.textContent = `Source: ${result.source}`;
                    
                    cardBody.appendChild(title);
                    cardBody.appendChild(content);
                    cardBody.appendChild(source);
                    resultDiv.appendChild(cardBody);
                    searchResults.appendChild(resultDiv);
                });
            } else {
                searchResults.innerHTML = `<div class="alert alert-danger">${data.message}</div>`;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            searchResults.innerHTML = '<div class="alert alert-danger">Error performing search. Please try again.</div>';
        });
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initApp);
