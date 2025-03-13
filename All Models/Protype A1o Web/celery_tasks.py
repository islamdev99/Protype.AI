
import os
import time
from celery import Celery
import requests
from bs4 import BeautifulSoup
import random
import re
import database

# Configure Celery with Redis (if available) or use local memory broker
if 'REDIS_URL' in os.environ:
    broker_url = os.environ['REDIS_URL']
else:
    broker_url = 'memory://'

celery_app = Celery('protype_tasks', broker=broker_url)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    worker_concurrency=2
)

@celery_app.task
def learn_from_wikipedia(topic):
    """Task to learn from Wikipedia in the background"""
    try:
        content = get_wikipedia_content(topic)
        if not content:
            print(f"No content found for topic: {topic}")
            return {"status": "error", "topic": topic, "reason": "No content found"}
            
        # Generate multiple questions about this topic
        questions = []
        for _ in range(2):  # Generate 2 different questions
            question = generate_question(topic)
            if question not in questions:
                questions.append(question)
        
        # Save each question with the same content
        results = []
        for question in questions:
            answer = f"According to Wikipedia under CC BY-SA 3.0:\n{content}"
            success = database.save_data(question, answer, 0.6, "wikipedia", "celery_worker")
            results.append({"question": question, "success": success})
            
        print(f"Successfully learned {len(results)} questions about {topic}")
        return {
            "status": "success", 
            "topic": topic, 
            "results": results
        }
    except Exception as e:
        print(f"Error learning from Wikipedia about {topic}: {e}")
        return {"status": "error", "topic": topic, "reason": str(e)}

@celery_app.task
def batch_wikipedia_learning(topics):
    """Process multiple Wikipedia topics in a batch"""
    results = []
    for topic in topics:
        result = learn_from_wikipedia.delay(topic)
        results.append(result.id)
    return results

@celery_app.task
def learn_from_external_ai(question):
    """Task to get answer from external AI API"""
    try:
        from protype_s import query_external_ai
        ai_response = query_external_ai(question)
        if database.save_data(question, ai_response, 0.6, "external_ai", "celery_worker"):
            return {"status": "success", "question": question, "answer_snippet": ai_response[:50]}
        return {"status": "error", "question": question, "reason": "Failed to save data"}
    except Exception as e:
        return {"status": "error", "question": question, "reason": str(e)}

@celery_app.task
def learn_from_gemini_flash(question):
    """Task to get answer from Gemini Flash API"""
    try:
        # Import locally to avoid circular imports
        import google.generativeai as genai
        import os
        
        # Configure Gemini API
        GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', "AIzaSyBUDUURqkN5Lvid5P8V0ZXIRpseKC7ffMU")
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Initialize Gemini model
        generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 4096,
            "response_mime_type": "text/plain",
        }
        model = genai.GenerativeModel(
            model_name="learnlm-1.5-pro-experimental",
            generation_config=generation_config,
        )
        
        # Get a detailed response for learning
        prompt = f"Please provide a detailed and educational answer to this question: {question}"
        response = model.generate_content(prompt)
        gemini_response = response.text.strip()
        
        if not gemini_response:
            print(f"Empty response from Gemini for: {question}")
            return {"status": "error", "question": question, "reason": "Empty response"}
            
        if database.save_data(question, gemini_response, 0.7, "gemini_flash_2", "celery_worker"):
            print(f"Successfully learned from Gemini: {question[:50]}...")
            return {
                "status": "success", 
                "question": question, 
                "answer_snippet": gemini_response[:50]
            }
        else:
            print(f"Failed to save Gemini learning data for: {question}")
            return {"status": "error", "question": question, "reason": "Failed to save data"}
            
    except Exception as e:
        print(f"Error learning from Gemini for {question}: {e}")
        return {"status": "error", "question": question, "reason": str(e)}

# Helper functions
def clean_text(text):
    """Clean Wikipedia text"""
    return re.sub(r'\[.*?\]|\{.*?\}|\<.*?\>', '', text).strip()

def get_wikipedia_content(topic):
    """Get content from Wikipedia with error handling and retries"""
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            response = requests.get(
                f"https://en.wikipedia.org/wiki/{topic}",
                headers={'User-Agent': 'ProtypeAI/1.0'},
                timeout=10
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            paragraphs = soup.find_all('p')
            content = ""
            line_count = 0
            
            for p in paragraphs:
                text = clean_text(p.get_text())
                if text and len(text) > 10:
                    content += text + "\n"
                    line_count += text.count('\n') + 1
                    if line_count >= 200:
                        break
                        
            return content if content else None
            
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                raise Exception(f"Failed to fetch Wikipedia content after {max_retries} attempts: {e}")

def generate_question(topic):
    """Generate a question about a topic"""
    question_types = [
        f"What is {topic}?", 
        f"How does {topic} work?",
        f"Why is {topic} important?", 
        f"Who discovered {topic}?",
        f"What are the benefits of {topic}?",
        f"How is {topic} used today?", 
        f"Why did {topic} become popular?",
        f"Who contributed to {topic}?"
    ]
    return random.choice(question_types)
import os
import random
import time
import requests
from bs4 import BeautifulSoup
import re
from celery import Celery
import google.generativeai as genai
import database

# Configure Celery with Redis (if available) or use local memory broker
if 'REDIS_URL' in os.environ:
    broker_url = os.environ['REDIS_URL']
else:
    broker_url = 'memory://'

celery_app = Celery('protype_tasks', broker=broker_url)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    worker_concurrency=2
)

# Configure Gemini API
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', "AIzaSyBUDUURqkN5Lvid5P8V0ZXIRpseKC7ffMU")
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini model
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}
gemini_model = genai.GenerativeModel(
    model_name="learnlm-1.5-pro-experimental",
    generation_config=generation_config,
)
chat_session = gemini_model.start_chat(history=[])

def clean_text(text):
    """Clean Wikipedia text"""
    return re.sub(r'\[.*?\]|\{.*?\}|\<.*?\>', '', text).strip()

def get_wikipedia_content(topic):
    """Get content from Wikipedia with error handling and retries"""
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            response = requests.get(
                f"https://en.wikipedia.org/wiki/{topic}",
                headers={'User-Agent': 'ProtypeAI/1.0'},
                timeout=10
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            paragraphs = soup.find_all('p')
            content = ""
            line_count = 0
            
            for p in paragraphs:
                text = clean_text(p.get_text())
                if text and len(text) > 10:
                    content += text + "\n"
                    line_count += text.count('\n') + 1
                    if line_count >= 200:
                        break
                        
            return content if content else None
            
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                raise Exception(f"Failed to fetch Wikipedia content after {max_retries} attempts: {e}")

def generate_question(topic):
    """Generate a question about a topic"""
    question_types = [
        f"What is {topic}?", 
        f"How does {topic} work?",
        f"Why is {topic} important?", 
        f"Who discovered {topic}?",
        f"What are the benefits of {topic}?",
        f"How is {topic} used today?", 
        f"Why did {topic} become popular?",
        f"Who contributed to {topic}?"
    ]
    return random.choice(question_types)

@celery_app.task
def learn_from_wikipedia(topic):
    """Task to learn from Wikipedia in the background"""
    try:
        content = get_wikipedia_content(topic)
        if content:
            question = generate_question(topic)
            answer = f"According to Wikipedia under CC BY-SA 3.0:\n{content}"
            database.save_data(question, answer, 0.6, "wikipedia", "celery_worker")
            return {"status": "success", "topic": topic, "question": question}
        return {"status": "error", "topic": topic, "reason": "No content found"}
    except Exception as e:
        return {"status": "error", "topic": topic, "reason": str(e)}

@celery_app.task
def batch_wikipedia_learning(topics):
    """Process multiple Wikipedia topics in a batch"""
    results = []
    for topic in topics:
        result = learn_from_wikipedia.delay(topic)
        results.append(result.id)
    return results

@celery_app.task
def learn_from_external_ai(question):
    """Task to get answer from external AI API"""
    try:
        ai_response = query_external_ai(question)
        if database.save_data(question, ai_response, 0.6, "external_ai", "celery_worker"):
            return {"status": "success", "question": question, "answer_snippet": ai_response[:50]}
        return {"status": "error", "question": question, "reason": "Failed to save data"}
    except Exception as e:
        return {"status": "error", "question": question, "reason": str(e)}

@celery_app.task(priority=9)  # Higher priority task (default is 0)
def learn_from_gemini_flash(question):
    """Task to get answer from Gemini Flash API with improved results"""
    try:
        # First check if we've already answered this before
        conn, is_postgres = database.get_connection()
        cursor = conn.cursor()
        
        if is_postgres:
            cursor.execute("SELECT answer FROM knowledge WHERE question = %s AND source = 'gemini_flash_2'", (question,))
        else:
            cursor.execute("SELECT answer FROM knowledge WHERE question = ? AND source = 'gemini_flash_2'", (question,))
            
        existing = cursor.fetchone()
        database.release_connection(conn, is_postgres)
        
        # If we already have an answer, return it
        if existing:
            return {
                "status": "success", 
                "question": question, 
                "answer_snippet": existing[0][:50],
                "answer_full": existing[0],
                "source": "gemini_flash_2",
                "cache_hit": True
            }
        
        # Otherwise query Gemini
        gemini_response = query_gemini_flash(question)
        if database.save_data(question, gemini_response, 0.7, "gemini_flash_2", "celery_worker"):
            # If available, also index in Elasticsearch
            if hasattr(search_engine, 'HAS_ELASTICSEARCH') and search_engine.HAS_ELASTICSEARCH:
                search_engine.index_document(question, gemini_response, 0.7, "gemini_flash_2")
                
            return {
                "status": "success", 
                "question": question, 
                "answer_snippet": gemini_response[:50],
                "answer_full": gemini_response,
                "source": "gemini_flash_2"
            }
        return {"status": "error", "question": question, "reason": "Failed to save data"}
    except Exception as e:
        print(f"Error in learn_from_gemini_flash: {e}")
        return {"status": "error", "question": question, "reason": str(e)}

def query_external_ai(query):
    """Function to query external AI API"""
    try:
        url = "https://api.aimlapi.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {os.environ.get('AIMLAPI_KEY', '753aa08c2b8344f38ff8bce052c0bec3')}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [{
                "role": "user",
                "content": query
            }],
            "max_tokens": 150
        }
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"Error querying external AI: {e}")
        return f"Failed to get response from external AI: {e}"

def query_gemini_flash(question):
    """Function to query Gemini Flash 2"""
    try:
        response = chat_session.send_message(question)
        return response.text.strip()
    except Exception as e:
        print(f"Error querying Gemini Flash 2: {e}")
        return f"Failed to get response from Gemini Flash 2: {e}"

@celery_app.task
def generate_topic_suggestions(existing_topics, count=5):
    """Generate new topic suggestions based on existing topics"""
    try:
        prompt = f"""
        Based on these existing topics:
        {', '.join(existing_topics[:10])}
        
        Generate {count} new, related academic or educational topics that might be interesting to learn about.
        Return only the topic names, separated by commas.
        """
        
        response = gemini_model.generate_content(prompt)
        
        if response.text:
            new_topics = [topic.strip() for topic in response.text.split(',')]
            return {"status": "success", "topics": new_topics}
        
        return {"status": "error", "reason": "Failed to generate topics"}
    except Exception as e:
        return {"status": "error", "reason": str(e)}
