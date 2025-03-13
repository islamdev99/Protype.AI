import os
import random
import re
import time
import requests
import json
from celery import Celery
from bs4 import BeautifulSoup
import google.generativeai as genai

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
    model_name="gemini-1.5-pro",
    generation_config=generation_config,
)
chat_session = gemini_model.start_chat(history=[])

# Database functions (imported to avoid circular imports)
from database import save_data

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
            save_data(question, answer, 0.6, "wikipedia", "celery_worker")
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
        if save_data(question, ai_response, 0.6, "external_ai", "celery_worker"):
            return {"status": "success", "question": question, "answer_snippet": ai_response[:50]}
        return {"status": "error", "question": question, "reason": "Failed to save data"}
    except Exception as e:
        return {"status": "error", "question": question, "reason": str(e)}

@celery_app.task
def learn_from_gemini_flash(question):
    """Task to get answer from Gemini Flash API"""
    try:
        gemini_response = query_gemini_flash(question)
        if save_data(question, gemini_response, 0.6, "gemini_flash_2", "celery_worker"):
            return {"status": "success", "question": question, "answer_snippet": gemini_response[:50]}
        return {"status": "error", "question": question, "reason": "Failed to save data"}
    except Exception as e:
        return {"status": "error", "question": question, "reason": str(e)}

@celery_app.task
def generate_topic_suggestions(current_topics):
    """Generate suggested topics for learning based on current topics"""
    try:
        # Prepare a prompt that asks for related topics
        prompt = f"""
        Based on the following topics, suggest 5 more related topics that would be interesting to learn about:
        {', '.join(current_topics)}
        
        Format your response as a comma-separated list only. No additional text.
        """
        
        # Use Gemini to generate suggestions
        response = chat_session.send_message(prompt)
        
        # Process the response - expecting a comma-separated list
        suggested_topics = [topic.strip() for topic in response.text.split(',')]
        
        # Format for Wikipedia - replace spaces with underscores
        formatted_topics = [topic.replace(' ', '_') for topic in suggested_topics]
        
        return formatted_topics[:5]  # Limit to 5 topics
    except Exception as e:
        print(f"Error generating topic suggestions: {e}")
        # Provide fallback topics in case of API error
        return [
            "Computer_science", 
            "Data_mining", 
            "Internet_of_things", 
            "Cybersecurity",
            "Virtual_reality"
        ]

# Function to query external AI API
def query_external_ai(query):
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

# Function to query Gemini Flash 2
def query_gemini_flash(question):
    try:
        response = chat_session.send_message(question)
        return response.text.strip()
    except Exception as e:
        print(f"Error querying Gemini Flash 2: {e}")
        return f"Failed to get response from Gemini Flash 2: {e}"