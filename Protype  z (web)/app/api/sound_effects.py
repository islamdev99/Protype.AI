"""
واجهة برمجة مولد المؤثرات الصوتية باستخدام ElevenLabs API
"""

import os
import base64
import requests
from flask import Blueprint, request, jsonify
import json
import datetime

# استخدام المفتاح من المتغيرات البيئية أو تعيين قيمة افتراضية
ELEVEN_LABS_API_KEY = os.environ.get('ELEVEN_LABS_API_KEY', '')

# إنشاء blueprint لواجهة المؤثرات الصوتية
sound_effects_bp = Blueprint('sound_effects', __name__)

def log_generation(text, duration, prompt_influence):
    """تسجيل عمليات توليد المؤثرات الصوتية"""
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "text": text,
        "duration": duration,
        "prompt_influence": prompt_influence
    }

    try:
        # إنشاء مجلد السجلات إذا لم يكن موجوداً
        os.makedirs('logs/sound_effects', exist_ok=True)

        log_file = f"logs/sound_effects/log_{datetime.datetime.now().strftime('%Y-%m-%d')}.json"

        # تحميل السجل الحالي إذا كان موجوداً
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        else:
            logs = {"generations": []}

        # إضافة العملية الجديدة
        logs["generations"].append(log_entry)

        # حفظ السجل
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)

    except Exception as e:
        print(f"خطأ في تسجيل عملية توليد المؤثر الصوتي: {e}")

@sound_effects_bp.route('/generate', methods=['POST'])
def generate_sound_effect():
    """توليد مؤثر صوتي باستخدام ElevenLabs API"""
    try:
        # الحصول على البيانات من الطلب
        data = request.json
        text = data.get('text', '').strip()
        duration_seconds = data.get('duration_seconds', None)
        prompt_influence = data.get('prompt_influence', 0.3)

        if not text:
            return jsonify({"error": "يجب توفير نص لتوليد المؤثر الصوتي"}), 400

        # التحقق من المفتاح
        if not ELEVEN_LABS_API_KEY:
            return jsonify({"error": "لم يتم تكوين مفتاح API للمؤثرات الصوتية"}), 500

        # إعداد البيانات للطلب
        request_data = {
            "text": text
        }

        # إضافة مدة الصوت إذا تم تحديدها
        if duration_seconds is not None:
            request_data["duration_seconds"] = duration_seconds

        # إضافة تأثير النص
        request_data["prompt_influence"] = prompt_influence

        # إرسال الطلب إلى ElevenLabs API
        response = requests.post(
            "https://api.elevenlabs.io/v1/sound-generation",
            headers={
                "xi-api-key": ELEVEN_LABS_API_KEY,
                "Content-Type": "application/json"
            },
            json=request_data
        )

        # التحقق من نجاح الطلب
        if response.status_code != 200:
            error_message = "فشل في توليد المؤثر الصوتي"
            try:
                error_data = response.json()
                if 'detail' in error_data:
                    error_message = error_data['detail']
            except:
                pass
            return jsonify({"error": error_message, "status_code": response.status_code}), 400

        # تحويل البيانات الثنائية إلى base64
        audio_base64 = base64.b64encode(response.content).decode('utf-8')

        # تسجيل العملية
        log_generation(text, duration_seconds, prompt_influence)

        return jsonify({
            "status": "success",
            "audio_base64": audio_base64
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@sound_effects_bp.route('/presets', methods=['GET'])
def get_sound_presets():
    """الحصول على قائمة بالمؤثرات الصوتية المُعدة مسبقًا"""
    presets = [
        {"name": "انفجار", "text": "انفجار قوي وصاخب", "icon": "💥"},
        {"name": "مطر", "text": "صوت المطر الناعم على النافذة", "icon": "🌧️"},
        {"name": "رياح", "text": "أصوات الرياح عبر الأشجار والمباني", "icon": "🌬️"},
        {"name": "قطار", "text": "صوت قطار يمر بسرعة عالية", "icon": "🚄"},
        {"name": "طيور", "text": "أصوات عصافير تغرد في الصباح الباكر", "icon": "🐦"},
        {"name": "محيط", "text": "أمواج المحيط تتلاطم على الشاطئ", "icon": "🌊"},
        {"name": "تصفيق", "text": "تصفيق حار من جمهور كبير", "icon": "👏"},
        {"name": "ضحك", "text": "ضحك مجموعة من الناس", "icon": "😂"},
        {"name": "قلب", "text": "دقات قلب منتظمة", "icon": "❤️"},
        {"name": "سيارة", "text": "صوت محرك سيارة قوية", "icon": "🚗"}
    ]
    
    return jsonify({
        "status": "success",
        "presets": presets
    })


def register_sound_api(app):
    """تسجيل واجهة برمجة المؤثرات الصوتية مع تطبيق Flask"""
    app.register_blueprint(sound_effects_bp, url_prefix='/api/sound-effects')