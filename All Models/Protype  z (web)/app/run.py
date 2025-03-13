
# -*- coding: utf-8 -*-
"""
ملف التشغيل الرئيسي للذكاء الاصطناعي
"""

import os
import logging
import sys
import time
from flask import Flask
from waitress import serve

# إضافة المسار الجذر إلى مسار النظام للتمكن من استيراد الوحدات
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# استيراد وحدات التطبيق
from app.web.web_app import app as web_app
from app.api.api_endpoints import register_api
from app.core.learning_manager import start_learning, stop_learning
from app.database.database import init_db, sync_database_to_elasticsearch
from app.utils.speech import init_speech_engine

# إعداد التسجيل
def setup_logging():
    """إعداد نظام تسجيل الأحداث"""
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f"{log_dir}/app.log"),
            logging.StreamHandler()
        ]
    )
    
    # إعداد مسجل خاص بالتطبيق
    logger = logging.getLogger('protype_ai')
    logger.setLevel(logging.INFO)
    
    return logger

# إعداد التطبيق
def create_app():
    """إنشاء وإعداد تطبيق Flask"""
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    
    # تكوين التطبيق
    app.config.update(
        SECRET_KEY=os.environ.get('SECRET_KEY', os.urandom(24)),
        DEBUG=os.environ.get('DEBUG', 'False').lower() == 'true',
        JSON_AS_ASCII=False,  # لدعم الأحرف العربية في JSON
        TEMPLATES_AUTO_RELOAD=True
    )
    
    # تسجيل واجهة برمجة التطبيقات
    register_api(app)
    
    # تسجيل مسارات الويب من web_app
    app.register_blueprint(web_app)
    
    return app

# تهيئة النظام
def initialize_system(logger):
    """تهيئة النظام وإعداد المكونات الأساسية"""
    logger.info("بدء تهيئة نظام الذكاء الاصطناعي Protype.AI")
    
    # تهيئة قاعدة البيانات
    logger.info("تهيئة قاعدة البيانات...")
    init_db()
    
    # محاولة تهيئة Elasticsearch إذا كان متاحاً
    try:
        logger.info("محاولة مزامنة Elasticsearch...")
        if sync_database_to_elasticsearch():
            logger.info("تمت مزامنة Elasticsearch بنجاح")
        else:
            logger.warning("تخطي مزامنة Elasticsearch - غير متاح")
    except Exception as e:
        logger.error(f"فشل في مزامنة Elasticsearch: {e}")
    
    # تهيئة محرك تحويل النص إلى كلام
    logger.info("تهيئة محرك تحويل النص إلى كلام...")
    init_speech_engine()
    
    # إنشاء المجلدات المطلوبة إذا لم تكن موجودة
    required_dirs = [
        'logs', 'logs/api', 'reports', 'models', 'data', 
        'app/static/uploads', 'app/static/generated'
    ]
    
    for directory in required_dirs:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"تم التأكد من وجود المجلد: {directory}")
    
    logger.info("اكتملت تهيئة النظام بنجاح")

# وظيفة التشغيل الرئيسية
def run_app(host='0.0.0.0', port=8080, use_waitress=True):
    """تشغيل التطبيق الرئيسي"""
    # إعداد التسجيل
    logger = setup_logging()
    
    # تهيئة النظام
    initialize_system(logger)
    
    # إنشاء التطبيق
    app = create_app()
    
    # بدء خدمة التعلم المستمر
    try:
        logger.info("بدء خدمة التعلم المستمر...")
        start_learning()
        logger.info("بدأت خدمة التعلم المستمر بنجاح")
    except Exception as e:
        logger.error(f"فشل في بدء خدمة التعلم المستمر: {e}")
    
    # طباعة رسالة الترحيب
    logger.info(f"بدء تشغيل Protype.AI على http://{host}:{port}")
    print("\n" + "=" * 60)
    print(f"  Protype.AI - نظام الذكاء الاصطناعي المتقدم  ")
    print(f"  يعمل على: http://{host}:{port}  ")
    print("=" * 60 + "\n")
    
    # استخدام Waitress كخادم إنتاج أو خادم Flask للتطوير
    if use_waitress:
        logger.info("استخدام Waitress كخادم إنتاج")
        serve(app, host=host, port=port, threads=8, connection_limit=1000, channel_timeout=30)
    else:
        logger.info("استخدام خادم Flask للتطوير")
        app.run(host=host, port=port, debug=app.config['DEBUG'])

# وظيفة الإغلاق الآمن
def shutdown():
    """إغلاق التطبيق بشكل آمن"""
    logger = logging.getLogger('protype_ai')
    logger.info("بدء إغلاق التطبيق...")
    
    # إيقاف خدمة التعلم المستمر
    try:
        logger.info("إيقاف خدمة التعلم المستمر...")
        stop_learning()
        logger.info("توقفت خدمة التعلم المستمر بنجاح")
    except Exception as e:
        logger.error(f"فشل في إيقاف خدمة التعلم المستمر: {e}")
    
    # إجراءات إضافية للإغلاق الآمن هنا
    
    logger.info("تم إغلاق التطبيق بنجاح")
    
    # تأخير قصير لضمان إكمال تسجيل الرسائل
    time.sleep(1)

# نقطة الدخول الرئيسية
if __name__ == "__main__":
    try:
        # تحديد منفذ من متغير البيئة أو استخدام الافتراضي
        port = int(os.environ.get('PORT', 8080))
        
        # تحديد وضع التطوير من متغير البيئة
        debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
        
        # تشغيل التطبيق
        run_app(port=port, use_waitress=not debug_mode)
    except KeyboardInterrupt:
        # التعامل مع انقطاع لوحة المفاتيح (Ctrl+C)
        print("\nتم اكتشاف انقطاع المستخدم. جاري الإغلاق...")
        shutdown()
    except Exception as e:
        # التعامل مع الأخطاء غير المتوقعة
        logging.error(f"حدث خطأ غير متوقع: {e}")
        shutdown()
