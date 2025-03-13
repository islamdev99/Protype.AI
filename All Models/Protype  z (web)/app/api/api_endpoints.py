
# -*- coding: utf-8 -*-
"""
واجهة برمجة التطبيقات (API) للذكاء الاصطناعي
"""

import json
import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from app.core.deep_thinking import apply_deep_thinking
from app.ml.sentiment_analyzer import analyze_sentiment
from app.ml.image_recognition import recognize_image, image_to_description
from app.api.data_analysis import analyze_ai_system, generate_full_report
from app.api.arabic_nlp import process_arabic_query

# إنشاء Blueprint للواجهة البرمجية
api_bp = Blueprint('api', __name__, url_prefix='/api')

# -------------------------
# نقاط اتصال الأساسية
# -------------------------

@api_bp.route('/status', methods=['GET'])
def get_status():
    """الحصول على حالة API"""
    try:
        return jsonify({
            "status": "online",
            "version": "1.0.0",
            "features": [
                "deep_thinking",
                "sentiment_analysis",
                "image_recognition",
                "arabic_processing",
                "data_analysis"
            ]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/chat', methods=['POST'])
def chat_api():
    """واجهة الدردشة المتقدمة"""
    try:
        data = request.json
        if not data or 'message' not in data:
            return jsonify({"error": "يجب توفير رسالة"}), 400
        
        message = data.get('message', '').strip()
        language = data.get('language', 'auto')
        include_thinking = data.get('include_thinking', True)
        
        # فحص اللغة العربية
        if language == 'auto':
            # فحص وجود حروف عربية
            arabic_chars = any('\u0600' <= c <= '\u06FF' for c in message)
            language = 'ar' if arabic_chars else 'en'
        
        # معالجة الاستعلام بالعربية
        if language == 'ar':
            arabic_analysis = process_arabic_query(message)
            
            # استخدام تحليل اللغة العربية لتحسين البحث
            # هنا يمكن استخدام arabic_analysis للحصول على كلمات مفتاحية ومعلومات إضافية
            
        # استدعاء واجهة الدردشة الرئيسية
        # في التطبيق الحقيقي، هنا ستقوم باستدعاء نظام المحادثة الخاص بك
        from web_app import chat_session, save_data
        
        # استخدام Gemini للحصول على إجابة
        response = chat_session.send_message(message)
        answer = response.text.strip()
        
        # حفظ في قاعدة البيانات
        save_data(message, answer, 0.6, "api_request", "api_user")
        
        # تطبيق التفكير العميق إذا كان مطلوباً
        if include_thinking:
            thinking_result = apply_deep_thinking(message, answer)
            final_response = thinking_result["response"]
            follow_up_questions = thinking_result["follow_up_questions"]
        else:
            final_response = answer
            follow_up_questions = []
        
        # تحليل المشاعر في الرسالة
        sentiment_result = analyze_sentiment(message)
        
        # إنشاء الاستجابة النهائية
        response_data = {
            "message": message,
            "response": final_response,
            "language": language,
            "sentiment": sentiment_result,
            "follow_up_questions": follow_up_questions,
            "request_id": str(uuid.uuid4())
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------------------------
# تحليل المشاعر
# -------------------------

@api_bp.route('/sentiment', methods=['POST'])
def sentiment_api():
    """تحليل مشاعر النص"""
    try:
        data = request.json
        if not data or 'text' not in data:
            return jsonify({"error": "يجب توفير نص للتحليل"}), 400
        
        text = data.get('text', '').strip()
        result = analyze_sentiment(text)
        
        return jsonify({
            "text": text,
            "analysis": result,
            "request_id": str(uuid.uuid4())
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------------------------
# التعرف على الصور
# -------------------------

@api_bp.route('/image/recognize', methods=['POST'])
def image_recognition_api():
    """التعرف على محتوى الصورة"""
    try:
        # التحقق من وجود الصورة
        if 'image' not in request.files and 'image_data' not in request.form:
            return jsonify({"error": "يجب توفير صورة للتحليل"}), 400
        
        # الحصول على بيانات الصورة
        if 'image' in request.files:
            image_file = request.files['image']
            image_data = image_file.read()
        else:
            image_data = request.form['image_data']
        
        # التعرف على الصورة
        recognition_result = recognize_image(image_data)
        
        # إنشاء وصف للصورة
        description = image_to_description(image_data)
        
        return jsonify({
            "recognition_result": recognition_result,
            "description": description,
            "request_id": str(uuid.uuid4())
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------------------------
# تحليل النص العربي
# -------------------------

@api_bp.route('/arabic/analyze', methods=['POST'])
def arabic_analysis_api():
    """تحليل النص العربي"""
    try:
        data = request.json
        if not data or 'text' not in data:
            return jsonify({"error": "يجب توفير نص عربي للتحليل"}), 400
        
        text = data.get('text', '').strip()
        result = process_arabic_query(text)
        
        return jsonify({
            "text": text,
            "analysis": result,
            "request_id": str(uuid.uuid4())
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------------------------
# تحليل النظام
# -------------------------

@api_bp.route('/analysis', methods=['GET'])
def system_analysis_api():
    """تحليل نظام الذكاء الاصطناعي"""
    try:
        result = analyze_ai_system()
        
        return jsonify({
            "analysis_result": result,
            "request_id": str(uuid.uuid4()),
            "timestamp": __import__('datetime').datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/report', methods=['GET'])
def generate_report_api():
    """إنشاء تقرير شامل"""
    try:
        report_type = request.args.get('type', 'comprehensive')
        result = generate_full_report()
        
        return jsonify({
            "report_result": result,
            "request_id": str(uuid.uuid4()),
            "timestamp": __import__('datetime').datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------------------------
# تسجيل API
# -------------------------

def register_api(app):
    """تسجيل مسارات API مع تطبيق Flask"""
    app.register_blueprint(api_bp)
    
    # إضافة قواعد الـ CORS
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
        return response
    
    # تسجيل الأحداث
    @api_bp.before_request
    def log_request():
        # تسجيل طلب API
        request_info = {
            'endpoint': request.endpoint,
            'method': request.method,
            'ip': request.remote_addr,
            'user_agent': request.user_agent.string,
            'timestamp': __import__('datetime').datetime.now().isoformat()
        }
        
        # إنشاء ملف السجل إذا لم يكن موجوداً
        log_dir = 'logs/api'
        os.makedirs(log_dir, exist_ok=True)
        
        # كتابة السجل
        log_file = f"{log_dir}/api_log_{__import__('datetime').datetime.now().strftime('%Y-%m-%d')}.json"
        
        try:
            # تحميل الملف الحالي إذا كان موجوداً
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            else:
                logs = {'requests': []}
            
            # إضافة السجل الجديد
            logs['requests'].append(request_info)
            
            # حفظ الملف
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=4)
                
        except Exception as e:
            print(f"خطأ في تسجيل طلب API: {e}")
