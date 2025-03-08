
# Protype.AI API Documentation

## Overview
هذا المستند يشرح واجهة برمجة التطبيقات (API) المتاحة في نظام Protype.AI. تم تصميم واجهة برمجة التطبيقات لتسهيل التفاعل مع قدرات الذكاء الاصطناعي للنظام، والتعلم، والبحث، وإدارة المعرفة.

## Base URL
```
https://your-protype-instance.com/
```
أو محليًا:
```
http://localhost:8080/
```

## Authentication
حاليًا، لا تتطلب واجهة برمجة التطبيقات مصادقة. في الإصدارات المستقبلية، قد يتم تنفيذ مصادقة قائمة على الرمز المميز (token).

## API Endpoints

### 1. Chat API
يستخدم للتفاعل مع نظام المحادثة الذكي.

#### POST /chat
**الوصف**: إرسال سؤال والحصول على إجابة ذكية.

**طلب**:
```json
{
  "question": "ما هي الجاذبية؟"
}
```

**استجابة**:
```json
{
  "status": "success",
  "answer": "الجاذبية هي قوة الجذب التي تحدث بين جميع الأجسام التي لها كتلة...",
  "source": "gemini_flash_2",
  "question_type": "definition"
}
```

**رموز الاستجابة**:
- `200 OK`: تمت معالجة الطلب بنجاح
- `400 Bad Request`: تنسيق الطلب غير صالح
- `500 Internal Server Error`: حدث خطأ داخلي

### 2. Teach API
يستخدم لإضافة معرفة جديدة إلى النظام.

#### POST /teach
**الوصف**: تعليم النظام سؤالًا وإجابة جديدين.

**طلب**:
```json
{
  "question": "من هو مؤسس Protype.AI؟",
  "answer": "Islam Ibrahim هو مؤسس Protype.AI، وهو مهندس برمجيات ومطور ذكاء اصطناعي."
}
```

**استجابة**:
```json
{
  "status": "success",
  "message": "تم حفظ المعرفة بنجاح"
}
```

**رموز الاستجابة**:
- `200 OK`: تمت معالجة الطلب بنجاح
- `400 Bad Request`: تنسيق الطلب غير صالح
- `500 Internal Server Error`: حدث خطأ داخلي

### 3. Search API
يستخدم للبحث في قاعدة المعرفة والمصادر الخارجية.

#### POST /search
**الوصف**: البحث عن معلومات.

**طلب**:
```json
{
  "query": "الذكاء الاصطناعي"
}
```

**استجابة**:
```json
{
  "status": "success",
  "results": [
    {
      "question": "ما هو الذكاء الاصطناعي؟",
      "answer": "الذكاء الاصطناعي هو فرع من فروع علوم الكمبيوتر...",
      "source": "gemini_flash_2"
    },
    {
      "question": "تاريخ الذكاء الاصطناعي",
      "answer": "بدأت دراسة الذكاء الاصطناعي في أوائل الخمسينيات...",
      "source": "wikipedia"
    }
  ]
}
```

**رموز الاستجابة**:
- `200 OK`: تمت معالجة الطلب بنجاح
- `400 Bad Request`: تنسيق الطلب غير صالح
- `500 Internal Server Error`: حدث خطأ داخلي

### 4. Text-to-Speech API
يستخدم لتحويل النص إلى كلام مسموع.

#### POST /text-to-speech
**الوصف**: تحويل النص إلى ملف صوتي.

**طلب**:
```json
{
  "text": "مرحبًا، أنا Protype.AI، مساعدك الذكي!",
  "voice_id": "21m00Tcm4TlvDq8ikWAM"
}
```

**استجابة**:
```json
{
  "status": "success",
  "audio_base64": "data:audio/mp3;base64,AABB..."
}
```

**رموز الاستجابة**:
- `200 OK`: تمت معالجة الطلب بنجاح
- `400 Bad Request`: تنسيق الطلب غير صالح
- `500 Internal Server Error`: حدث خطأ داخلي

#### GET /voices
**الوصف**: الحصول على قائمة الأصوات المتاحة.

**استجابة**:
```json
{
  "status": "success",
  "voices": [
    {
      "voice_id": "21m00Tcm4TlvDq8ikWAM",
      "name": "Rachel",
      "preview_url": "https://example.com/voice-preview.mp3"
    },
    ...
  ]
}
```

### 5. Learning Management API
يستخدم لإدارة عمليات التعلم المستمر.

#### POST /start-learning
**الوصف**: بدء عملية التعلم المستمر.

**استجابة**:
```json
{
  "status": "success",
  "message": "تم بدء عملية التعلم المستمر"
}
```

#### POST /stop-learning
**الوصف**: إيقاف عملية التعلم المستمر.

**استجابة**:
```json
{
  "status": "success",
  "message": "تم إيقاف عملية التعلم المستمر"
}
```

#### GET /learning-logs
**الوصف**: الحصول على سجلات التعلم الأخيرة.

**استجابة**:
```json
{
  "status": "success",
  "logs": [
    {
      "timestamp": "2023-06-01T12:30:45",
      "action": "wikipedia_learning",
      "details": {
        "topic": "Machine_learning",
        "question": "ما هو التعلم الآلي؟"
      }
    },
    ...
  ]
}
```

### 6. Dashboard API
يستخدم للحصول على إحصائيات ومعلومات لوحة التحكم.

#### GET /dashboard-stats
**الوصف**: الحصول على إحصائيات لوحة التحكم.

**استجابة**:
```json
{
  "status": "success",
  "question_count": 1250,
  "node_count": 4320,
  "edge_count": 8750,
  "activities": [
    {
      "timestamp": "2023-06-01T14:25:10",
      "user": "web_user",
      "action": "chat",
      "description": "سأل: ما هي النسبية العامة؟"
    },
    ...
  ]
}
```

#### POST /generate-report
**الوصف**: إنشاء تقرير عن قاعدة المعرفة.

**استجابة**:
```json
{
  "status": "success",
  "message": "تم إنشاء تقرير قاعدة المعرفة",
  "report_path": "knowledge_report.txt"
}
```

## أنواع البيانات

### Question
| حقل | نوع | وصف |
|------|------|-------------|
| question | string | نص السؤال |
| answer | string | نص الإجابة |
| weight | float | وزن/ثقة الإجابة (0.0-1.0) |
| source | string | مصدر المعرفة (مثل "gemini_flash_2", "wikipedia", "user") |

### LearningLog
| حقل | نوع | وصف |
|------|------|-------------|
| timestamp | string | طابع زمني بتنسيق ISO 8601 |
| action | string | نوع إجراء التعلم |
| details | object | تفاصيل إضافية خاصة بالإجراء |

### ActivityLog
| حقل | نوع | وصف |
|------|------|-------------|
| timestamp | string | طابع زمني بتنسيق ISO 8601 |
| user | string | معرف المستخدم |
| action | string | نوع الإجراء |
| description | string | وصف الإجراء |

## رموز الخطأ
| رمز | وصف |
|------|-------------|
| 400 | طلب غير صالح |
| 401 | غير مصرح |
| 404 | لم يتم العثور على المورد |
| 429 | طلبات كثيرة جدًا |
| 500 | خطأ داخلي في الخادم |

## أمثلة

### مثال طلب Python
```python
import requests

url = "https://your-protype-instance.com/chat"
data = {
    "question": "ما هي النظرية النسبية؟"
}

response = requests.post(url, json=data)
print(response.json())
```

### مثال طلب JavaScript
```javascript
fetch('https://your-protype-instance.com/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    question: 'ما هي النظرية النسبية؟'
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

## قيود

- معدل الحد: 60 طلبًا في الدقيقة
- حجم الطلب الأقصى: 16KB
- الحد الأقصى لطول السؤال: 1000 حرف
- الحد الأقصى لطول الإجابة: 16000 حرف
