
# مخطط قاعدة بيانات Protype.AI

## نظرة عامة
يستخدم Protype.AI قاعدة بيانات SQLite لتخزين المعرفة والبيانات التشغيلية. يعرض هذا المستند بنية قاعدة البيانات والعلاقات بين الجداول.

## جدول: knowledge

هذا هو الجدول الرئيسي لتخزين عناصر المعرفة (الأسئلة والإجابات).

| اسم العمود | النوع | الوصف | الخصائص |
|------------|------|-------------|------------|
| id | INTEGER | المعرف الفريد | PRIMARY KEY, AUTOINCREMENT |
| question | TEXT | نص السؤال | UNIQUE |
| answer | TEXT | نص الإجابة | - |
| weight | REAL | وزن/موثوقية الإجابة (0-1) | - |
| source | TEXT | مصدر المعرفة | - |
| created_at | TIMESTAMP | وقت الإنشاء | DEFAULT CURRENT_TIMESTAMP |
| created_by | TEXT | من أنشأ السجل | DEFAULT 'system' |
| modified_at | TIMESTAMP | وقت آخر تعديل | DEFAULT CURRENT_TIMESTAMP |
| modified_by | TEXT | من قام بآخر تعديل | DEFAULT 'system' |

### الفهارس
| اسم الفهرس | الأعمدة | النوع | الوصف |
|------------|---------|------|-------------|
| idx_knowledge_question | question | BTREE | تسريع البحث عن الأسئلة |

### مخطط SQL للإنشاء
```sql
CREATE TABLE IF NOT EXISTS knowledge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT UNIQUE,
    answer TEXT,
    weight REAL,
    source TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT DEFAULT 'system',
    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_by TEXT DEFAULT 'system'
);

CREATE INDEX IF NOT EXISTS idx_knowledge_question ON knowledge (question);
```

## ملفات البيانات الإضافية

بالإضافة إلى قاعدة البيانات الرئيسية، يستخدم النظام ملفات JSON لتخزين معلومات إضافية:

### 1. learning_logs.json
يحتفظ بسجلات نشاط التعلم المستمر.

```json
{
  "logs": [
    {
      "timestamp": "2023-06-01T12:34:56.789Z",
      "action": "wikipedia_learning",
      "details": {
        "topic": "Artificial_intelligence",
        "question": "ما هو الذكاء الاصطناعي؟"
      }
    }
  ]
}
```

### 2. user_actions.json
يتتبع إجراءات المستخدم والنظام.

```json
{
  "version": "1.0",
  "actions": [
    {
      "timestamp": "2023-06-01T12:34:56.789Z",
      "user": "web_user",
      "action": "chat",
      "description": "سأل: ما هي الجاذبية؟"
    }
  ]
}
```

## العلاقات والمخطط

```
knowledge
  ├── question (المفتاح الأساسي الوظيفي)
  ├── answer
  ├── weight
  ├── source ─┐
  └── ...     │
              ▼
         مصادر المعرفة
        (wikipedia, gemini, user, ...)
```

## نمو قاعدة البيانات

مع استخدام التعلم المستمر، تنمو قاعدة البيانات تلقائيًا. فيما يلي معدلات النمو المتوقعة:

| نشاط التعلم | معدل النمو التقريبي |
|-------------|----------------------|
| منخفض | ~10-20 عنصر معرفة / يوم |
| متوسط | ~50-100 عنصر معرفة / يوم |
| مرتفع | ~200-500 عنصر معرفة / يوم |

## نصائح تحسين الأداء

1. **فهرسة إضافية**: إذا كنت تبحث كثيرًا عن المصدر، أضف فهرسًا على عمود `source`
2. **تنظيف البيانات**: نفذ مهمة دورية لإزالة المعرفة منخفضة الجودة (الوزن < 0.3)
3. **النسخ الاحتياطي**: قم بعمل نسخة احتياطية لملف قاعدة البيانات بانتظام
4. **تحسين الاستعلامات**: استخدم معلمات محددة في وظائف البحث
