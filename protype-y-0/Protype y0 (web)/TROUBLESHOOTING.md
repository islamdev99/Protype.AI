
# دليل استكشاف الأخطاء وإصلاحها لـ Protype.AI

## المشكلات الشائعة والحلول

### 1. مشكلات Gemini API

#### الخطأ: "Unknown field for GenerationConfig: response_mime_type"
**المشكلة**: إصدار واجهة برمجة تطبيقات Gemini المستخدم لا يدعم معلمة `response_mime_type` في تكوين التوليد.

**الحل**:
1. إزالة معلمة `response_mime_type` من قاموس `generation_config`
2. تحديث مكتبة `google-generativeai` إلى أحدث إصدار

```python
# الإعداد الصحيح لـ Gemini
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
}
```

#### الخطأ: "Failed to get response from Gemini Flash 2"
**المشكلة**: مشكلة في الاتصال أو في مفتاح API.

**الحل**:
1. تأكد من صحة مفتاح API
2. تحقق من الاتصال بالإنترنت
3. تحقق من سجلات النظام لمعرفة رسالة الخطأ الدقيقة

### 2. مشكلات قاعدة البيانات

#### الخطأ: "database is locked"
**المشكلة**: محاولة الوصول المتزامن لعمليات الكتابة في قاعدة بيانات SQLite.

**الحل**:
1. تنفيذ آلية إعادة المحاولة البسيطة
2. التأكد من إغلاق الاتصالات بشكل صحيح
3. زيادة مهلة الانتظار لقاعدة البيانات

```python
def retry_on_locked(func, max_attempts=3, delay=0.1):
    """وظيفة لإعادة المحاولة عند قفل قاعدة البيانات"""
    for attempt in range(max_attempts):
        try:
            return func()
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < max_attempts - 1:
                time.sleep(delay * (2 ** attempt))  # تأخير تصاعدي
                continue
            raise
```

#### الخطأ: "no such table: knowledge"
**المشكلة**: لم يتم إنشاء جدول المعرفة.

**الحل**:
1. التأكد من تشغيل `init_db()` قبل استخدام قاعدة البيانات
2. التحقق من مسار ملف قاعدة البيانات
3. التأكد من وجود أذونات كتابة للملف

### 3. مشكلات التعلم المستمر

#### الخطأ: "ImportError: No module named 'learning_manager'"
**المشكلة**: مسار الاستيراد غير صحيح أو الملف غير موجود.

**الحل**:
1. التأكد من وجود الملف في المسار الصحيح
2. تصحيح مسار الاستيراد

```python
# الاستيراد الصحيح
try:
    from .learning_manager import learning_manager
except ImportError:
    try:
        from learning_manager import learning_manager
    except ImportError:
        print("Warning: learning_manager module not found")
        learning_manager = None
```

#### الخطأ: "Thread is already running"
**المشكلة**: محاولة بدء خيط التعلم وهو يعمل بالفعل.

**الحل**:
1. التحقق من حالة التعلم قبل بدء خيط جديد
2. إضافة آلية إيقاف آمنة للخيط الحالي

```python
def start_learning(self):
    """بدء التعلم المستمر بأمان"""
    if self.is_learning and self.learning_thread and self.learning_thread.is_alive():
        print("Thread is already running")
        return False
    
    # إعادة تعيين العلم في حالة عدم تزامن الحالة مع الخيط
    self.is_learning = False
    if self.learning_thread:
        self.learning_thread.join(timeout=5)
    
    # بدء خيط جديد
    self.is_learning = True
    self.learning_thread = threading.Thread(target=self._learn_continuously)
    self.learning_thread.daemon = True
    self.learning_thread.start()
    return True
```

### 4. مشكلات المتطلبات والمكتبات

#### الخطأ: "ModuleNotFoundError: No module named 'waitress'"
**المشكلة**: لم يتم تثبيت مكتبة waitress المطلوبة.

**الحل**:
1. تثبيت المكتبة باستخدام pip:
```bash
pip install waitress==3.0.2
```

#### الخطأ: "No module named 'spacy'"
**المشكلة**: لم يتم تثبيت مكتبة spaCy أو نموذج اللغة المطلوب.

**الحل**:
1. تثبيت spaCy:
```bash
pip install spacy
```
2. تنزيل نموذج اللغة:
```bash
python -m spacy download en_core_web_sm
```

### 5. مشكلات خادم الويب

#### الخطأ: "Address already in use"
**المشكلة**: المنفذ الذي يحاول الخادم الاستماع عليه قيد الاستخدام بالفعل.

**الحل**:
1. تغيير رقم المنفذ
2. إنهاء العملية التي تستخدم المنفذ
3. إضافة منطق للبحث عن منفذ متاح

```python
def find_available_port(start_port=8080, max_attempts=10):
    """العثور على منفذ متاح"""
    import socket
    for port in range(start_port, start_port + max_attempts):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(('0.0.0.0', port))
            s.close()
            return port
        except OSError:
            continue
    raise RuntimeError(f"لم يتم العثور على منفذ متاح بعد {max_attempts} محاولات")
```

## خطوات استكشاف الأخطاء العامة

1. **تحقق من سجلات النظام**:
   - موقع السجلات: الإخراج القياسي للتطبيق
   - ابحث عن رسائل الخطأ وتتبع المكدس

2. **تحقق من حالة قاعدة البيانات**:
   - افحص ملف قاعدة البيانات: `protype_e0.db`
   - استخدم أداة مثل `sqlite3` للتحقق من البنية والمحتوى

3. **تحقق من حالة التعلم**:
   - راجع `learning_logs.json` للتحقق من نشاط التعلم
   - تحقق من حالة خيط التعلم في لوحة التحكم

4. **تحقق من اتصال API**:
   - تأكد من صحة مفاتيح API في المتغيرات البيئية
   - اختبر الاتصال بواجهات API مباشرة

5. **أعد تشغيل المكونات**:
   - أعد تشغيل خادم الويب
   - أعد تشغيل عملية التعلم المستمر

## نصائح للإصلاح السريع

1. **إعادة التشغيل الطارئة**:
   ```bash
   # أعد تشغيل خادم الويب
   kill $(ps aux | grep 'web_app.py' | grep -v grep | awk '{print $2}')
   python web_app.py
   ```

2. **إعادة تهيئة قاعدة البيانات** (استخدم بحذر، سيتم فقدان البيانات):
   ```python
   import os
   # حذف ملف قاعدة البيانات
   if os.path.exists('protype_e0.db'):
       os.rename('protype_e0.db', 'protype_e0.db.backup')
   # إعادة تهيئة قاعدة البيانات
   from database import init_db
   init_db()
   ```

3. **تنظيف ملفات السجل**:
   ```python
   import json
   # إعادة تعيين سجلات التعلم
   with open('learning_logs.json', 'w') as f:
       json.dump({"logs": []}, f)
   ```

4. **فحص توصيل API**:
   ```python
   import google.generativeai as genai
   import os

   # اختبار اتصال Gemini
   genai.configure(api_key=os.environ.get('GEMINI_API_KEY', "YOUR_API_KEY"))
   model = genai.GenerativeModel(model_name="learnlm-1.5-pro-experimental")
   response = model.generate_content("Hello")
   print(response.text)
   ```
