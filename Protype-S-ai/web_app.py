
from flask import Flask, render_template, request, jsonify, session
import os
import logging

# Setup logging
logger = logging.getLogger('protype_ai')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Initialize Flask app
app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')

# Set a secret key for session management
app.secret_key = os.environ.get('SECRET_KEY', 'protype-ai-dev-key')

# Root route
@app.route('/')
def index():
    return render_template('index.html')

# API endpoints
@app.route('/api/chat', methods=['POST'])
def chat_endpoint():
    data = request.json
    message = data.get('message', '')
    
    # Process the message and generate a response
    # This is a placeholder - implement actual chat processing here
    response = {"response": f"You said: {message}"}
    
    return jsonify(response)

@app.route('/api/search', methods=['GET'])
def search_endpoint():
    query = request.args.get('q', '')
    
    # Implement search functionality here
    results = [{"title": "Sample result", "content": "This is a sample search result"}]
    
    return jsonify({"results": results})

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {str(e)}")
    return render_template('500.html'), 500

# Make sure this variable is exported
__all__ = ['app']

# For direct execution
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
