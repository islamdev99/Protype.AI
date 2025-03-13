import os
import time
import random
import threading
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from datetime import datetime
import json

# استيراد وحدة قاعدة البيانات
from database import save_data, get_connection, release_connection

def log_learning(action, details):
    """تسجيل نشاط التعلم"""
    try:
        # تحميل سجلات التعلم الحالية
        try:
            with open('learning_logs.json', 'r') as f:
                logs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logs = {"logs": []}

        # إضافة سجل جديد
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details
        }

        logs["logs"].append(log_entry)

        # حفظ السجلات
        with open('learning_logs.json', 'w') as f:
            json.dump(logs, f, indent=2)
    except Exception as e:
        print(f"خطأ في تسجيل التعلم: {e}")

def learn_from_wikipedia(topic):
    """مهمة التعلم من ويكيبيديا في الخلفية"""
    try:
        content = get_wikipedia_content(topic)
        if content:
            question = generate_question(topic)
            answer = f"وفقًا لويكيبيديا تحت ترخيص CC BY-SA 3.0:\n{content}"
            if save_data(question, answer, 0.6, "wikipedia", "celery_worker"):
                log_learning("wikipedia_learn", {"topic": topic, "question": question})
                return {"status": "نجاح", "topic": topic, "question": question}
        return {"status": "خطأ", "topic": topic, "reason": "لم يتم العثور على محتوى"}
    except Exception as e:
        return {"status": "خطأ", "topic": topic, "reason": str(e)}

def batch_wikipedia_learning(topics):
    """معالجة مواضيع ويكيبيديا متعددة في دفعة واحدة"""
    results = []
    for topic in topics:
        result = learn_from_wikipedia(topic)
        results.append(result)
    return results

def learn_from_external_ai(question):
    """مهمة الحصول على إجابة من واجهة برمجة تطبيقات الذكاء الاصطناعي الخارجية"""
    try:
        ai_response = query_external_ai(question)
        if save_data(question, ai_response, 0.6, "external_ai", "celery_worker"):
            log_learning("external_ai_learn", {"question": question})
            return {"status": "نجاح", "question": question, "answer_snippet": ai_response[:50]}
        return {"status": "خطأ", "question": question, "reason": "فشل حفظ البيانات"}
    except Exception as e:
        return {"status": "خطأ", "question": question, "reason": str(e)}

def learn_from_gemini_flash(question):
    """مهمة الحصول على إجابة من واجهة برمجة تطبيقات Gemini Flash"""
    try:
        # تكوين Gemini API
        GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', "AIzaSyBUDUURqkN5Lvid5P8V0ZXIRpseKC7ffMU")
        genai.configure(api_key=GEMINI_API_KEY)

        # تهيئة نموذج Gemini
        generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 4096,
        }
        model = genai.GenerativeModel(
            model_name="learnlm-1.5-pro-experimental",
            generation_config=generation_config,
        )

        # الحصول على رد مفصل للتعلم
        prompt = f"يرجى تقديم إجابة مفصلة وتعليمية لهذا السؤال: {question}"
        response = model.generate_content(prompt)
        gemini_response = response.text.strip()

        if not gemini_response:
            print(f"إجابة فارغة من Gemini لـ: {question}")
            return {"status": "خطأ", "question": question, "reason": "إجابة فارغة"}

        if save_data(question, gemini_response, 0.7, "gemini_flash_2", "celery_worker"):
            print(f"تم التعلم بنجاح من Gemini: {question[:50]}...")
            log_learning("gemini_learn", {"question": question})
            return {
                "status": "نجاح", 
                "question": question,
                "answer_snippet": gemini_response[:50]
            }
        else:
            print(f"فشل حفظ بيانات تعلم Gemini لـ: {question}")
            return {"status": "خطأ", "question": question, "reason": "فشل حفظ البيانات"}

    except Exception as e:
        print(f"خطأ في التعلم من Gemini لـ {question}: {e}")
        return {"status": "خطأ", "question": question, "reason": str(e)}

def clean_text(text):
    """تنظيف نص ويكيبيديا"""
    import re
    return re.sub(r'\[.*?\]|\{.*?\}|\<.*?\>', '', text).strip()

def get_wikipedia_content(topic):
    """الحصول على محتوى من ويكيبيديا مع معالجة الأخطاء وإعادة المحاولات"""
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
                retry_delay *= 2  # زيادة أسية
            else:
                raise Exception(f"فشل جلب محتوى ويكيبيديا بعد {max_retries} محاولات: {e}")

def generate_question(topic):
    """توليد سؤال حول موضوع"""
    question_types = [
        f"ما هو {topic}?", 
        f"كيف يعمل {topic}?",
        f"لماذا {topic} مهم؟", 
        f"من اكتشف {topic}?",
        f"ما هي فوائد {topic}?",
        f"كيف يستخدم {topic} اليوم؟", 
        f"لماذا أصبح {topic} شائعًا؟",
        f"من ساهم في {topic}?"
    ]
    return random.choice(question_types)

def query_external_ai(query):
    """استعلام واجهة برمجة التطبيقات الخارجية للذكاء الاصطناعي"""
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
        print(f"خطأ في استعلام الذكاء الاصطناعي الخارجي: {e}")
        return f"فشل الحصول على استجابة من الذكاء الاصطناعي الخارجي: {e}"

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

#These lines are added to initialize the gemini model, as it was initialized in the original code but not in the edited code.
# Configure Gemini API
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', "AIzaSyBUDUURqkN5Lvid5P8V0ZXIRpseKC7ffMU")
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini model
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
}
gemini_model = genai.GenerativeModel(
    model_name="learnlm-1.5-pro-experimental",
    generation_config=generation_config,
)
chat_session = gemini_model.start_chat(history=[])

@celery_app.task
def learn_from_gemini_flash(question):
    """Task to get answer from Gemini Flash API"""
    try:
        # Create a learning-specific prompt to get more detailed information
        learning_prompt = f"""
        I want to learn about the following topic. Please provide a detailed, 
        educational response with key facts, concepts, and explanations:
        
        {question}
        """
        
        # Query Gemini
        gemini_response = query_gemini_flash(learning_prompt)
        
        if gemini_response and not gemini_response.startswith("Failed to get response"):
            # Save the knowledge with a high weight for learning-purpose content
            if database.save_data(question, gemini_response, 0.7, "gemini_flash_2", "celery_worker"):
                print(f"Successfully learned: {question}")
                return {
                    "status": "success", 
                    "question": question, 
                    "answer_snippet": gemini_response[:50] if len(gemini_response) > 50 else gemini_response
                }
            return {"status": "error", "question": question, "reason": "Failed to save data"}
        else:
            print(f"Failed to get proper response from Gemini for: {question}")
            return {"status": "error", "question": question, "reason": "Empty or error response from Gemini"}
    except Exception as e:
        print(f"Error in Gemini learning task: {e}")
        return {"status": "error", "question": question, "reason": str(e)}

def query_gemini_flash(question):
    """Function to query Gemini Flash 2"""
    try:
        response = chat_session.send_message(question)
        return response.text.strip()
    except Exception as e:
        print(f"Error querying Gemini Flash 2: {e}")
        return f"Failed to get response from Gemini Flash 2: {e}"