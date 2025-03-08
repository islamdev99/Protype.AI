
# -*- coding: utf-8 -*-
"""
وحدة تحويل النص إلى كلام والكلام إلى نص
"""

import os
import base64
import json
import requests
import tempfile
from io import BytesIO
import speech_recognition as sr
import ffmpeg

# تكوين API ElevenLabs
ELEVENLABS_API_KEY = os.environ.get('ELEVENLABS_API_KEY', '5f0c5c5b24f36f95c51e34f9db4ba73e')
ELEVENLABS_URL = "https://api.elevenlabs.io/v1/text-to-speech"

# الأصوات الافتراضية
DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # صوت مخصص
DEFAULT_VOICE_ID_AR = "z5fXpQynYE32RbGMSjY8"  # صوت عربي مخصص

# تكوين أداة التعرف على الكلام
recognizer = sr.Recognizer()

def init_speech_engine():
    """تهيئة محرك تحويل النص إلى كلام"""
    # ضبط خصائص المعرف
    recognizer.pause_threshold = 0.8
    recognizer.energy_threshold = 400
    
    # تحقق من وجود مفتاح API
    if not ELEVENLABS_API_KEY:
        print("تحذير: مفتاح API الخاص بـ ElevenLabs غير متوفر. سيتم استخدام وظائف محدودة.")
    
    return True

def text_to_speech(text, voice_id=None, output_format="base64"):
    """تحويل النص إلى كلام باستخدام ElevenLabs API"""
    if not text:
        return None
    
    # التحقق من اللغة وتعيين الصوت المناسب
    if voice_id is None:
        # فحص وجود حروف عربية
        has_arabic = any('\u0600' <= c <= '\u06FF' for c in text)
        voice_id = DEFAULT_VOICE_ID_AR if has_arabic else DEFAULT_VOICE_ID
    
    # إعداد الطلب
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.5,
            "use_speaker_boost": True
        }
    }
    
    try:
        # إرسال الطلب إلى ElevenLabs API
        response = requests.post(
            f"{ELEVENLABS_URL}/{voice_id}",
            json=data,
            headers=headers,
            timeout=30
        )
        
        # التحقق من نجاح الطلب
        if response.status_code == 200:
            if output_format == "base64":
                # تحويل الصوت إلى صيغة base64
                audio_base64 = base64.b64encode(response.content).decode('utf-8')
                return audio_base64
            else:
                # إرجاع محتوى الصوت مباشرة
                return response.content
        else:
            error_msg = f"فشل في تحويل النص إلى كلام: {response.status_code} - {response.text}"
            print(error_msg)
            return None
            
    except Exception as e:
        print(f"خطأ في تحويل النص إلى كلام: {e}")
        return None

def get_available_voices():
    """الحصول على قائمة الأصوات المتاحة من ElevenLabs"""
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    try:
        response = requests.get(
            "https://api.elevenlabs.io/v1/voices",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            voices_data = response.json()
            
            # تحسين البيانات المرجعة للاستخدام في واجهة المستخدم
            voices = []
            for voice in voices_data.get("voices", []):
                voices.append({
                    "id": voice.get("voice_id"),
                    "name": voice.get("name"),
                    "description": voice.get("description", ""),
                    "preview_url": voice.get("preview_url", ""),
                    "labels": voice.get("labels", {})
                })
            
            return {"voices": voices}
        else:
            error_msg = f"فشل في الحصول على الأصوات: {response.status_code} - {response.text}"
            print(error_msg)
            return {"voices": [], "error": error_msg}
            
    except Exception as e:
        print(f"خطأ في الحصول على الأصوات: {e}")
        return {"voices": [], "error": str(e)}

def speech_to_text(audio_data=None, audio_file=None, language="ar-AR"):
    """تحويل الكلام إلى نص باستخدام SpeechRecognition"""
    try:
        audio = None
        
        # التعامل مع البيانات الصوتية المختلفة
        if audio_data is not None:
            # إذا كانت البيانات بصيغة base64
            if isinstance(audio_data, str) and audio_data.startswith("data:audio"):
                # استخراج البيانات من سلسلة base64
                audio_data = audio_data.split(",")[1]
                audio_bytes = base64.b64decode(audio_data)
                
                # حفظ في ملف مؤقت
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    temp_file.write(audio_bytes)
                    temp_filename = temp_file.name
                
                # فتح الملف الصوتي
                with sr.AudioFile(temp_filename) as source:
                    audio = recognizer.record(source)
                
                # حذف الملف المؤقت
                os.unlink(temp_filename)
                
            # إذا كانت البيانات ثنائية مباشرة
            elif isinstance(audio_data, bytes):
                # حفظ في ملف مؤقت
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                    temp_file.write(audio_data)
                    temp_filename = temp_file.name
                
                # فتح الملف الصوتي
                with sr.AudioFile(temp_filename) as source:
                    audio = recognizer.record(source)
                
                # حذف الملف المؤقت
                os.unlink(temp_filename)
        
        # استخدام ملف صوتي إذا تم تحديده
        elif audio_file is not None:
            with sr.AudioFile(audio_file) as source:
                audio = recognizer.record(source)
        
        if audio is None:
            return {"error": "لم يتم توفير بيانات صوتية صالحة"}
        
        # التعرف على النص باستخدام Google Web API
        text = recognizer.recognize_google(audio, language=language)
        
        return {
            "text": text,
            "language": language,
            "confidence": 0.9  # قيمة افتراضية حيث أن recognize_google لا تعود بالثقة
        }
        
    except sr.UnknownValueError:
        return {"error": "لم يتمكن النظام من فهم الصوت"}
    except sr.RequestError as e:
        return {"error": f"خطأ في طلب خدمة التعرف على الكلام: {e}"}
    except Exception as e:
        return {"error": f"خطأ غير متوقع: {e}"}

def convert_audio_format(input_data, input_format="webm", output_format="wav"):
    """تحويل صيغة الملف الصوتي"""
    try:
        # إذا كانت البيانات بصيغة base64
        if isinstance(input_data, str) and input_data.startswith("data:audio"):
            # استخراج البيانات من سلسلة base64
            input_data = input_data.split(",")[1]
            input_bytes = base64.b64decode(input_data)
        else:
            input_bytes = input_data
        
        # إنشاء ملفات مؤقتة
        input_file = tempfile.NamedTemporaryFile(suffix=f".{input_format}", delete=False)
        output_file = tempfile.NamedTemporaryFile(suffix=f".{output_format}", delete=False)
        
        # كتابة البيانات الصوتية إلى الملف المؤقت
        input_file.write(input_bytes)
        input_file.close()
        output_file.close()
        
        # تحويل الصيغة باستخدام ffmpeg
        ffmpeg.input(input_file.name).output(output_file.name).run(overwrite_output=True, quiet=True)
        
        # قراءة الملف المحول
        with open(output_file.name, "rb") as f:
            output_bytes = f.read()
        
        # حذف الملفات المؤقتة
        os.unlink(input_file.name)
        os.unlink(output_file.name)
        
        # تحويل إلى base64 إذا لزم الأمر
        output_base64 = base64.b64encode(output_bytes).decode('utf-8')
        
        return {
            "data": output_base64,
            "format": output_format,
            "data_url": f"data:audio/{output_format};base64,{output_base64}"
        }
        
    except Exception as e:
        print(f"خطأ في تحويل صيغة الصوت: {e}")
        return {"error": str(e)}
