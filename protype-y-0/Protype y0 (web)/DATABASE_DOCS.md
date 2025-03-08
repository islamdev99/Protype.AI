
# توثيق قاعدة بيانات Protype.AI

## نظرة عامة

يستخدم Protype.AI نظام قاعدة بيانات مرن يدعم كلاً من SQLite وPostgreSQL. تم تصميم هذه الهندسة لتوفير تخزين فعال وموثوق للمعرفة مع إمكانية التوسع لأحجام البيانات الكبيرة.

## هيكل قاعدة البيانات

### جدول: knowledge

هذا هو الجدول الرئيسي لتخزين المعرفة في النظام.

| اسم العمود | النوع | الوصف | ملاحظات |
|------------|------|-------------|---------|
| id | INTEGER/SERIAL | المفتاح الأساسي | يزيد تلقائيًا |
| question | TEXT | السؤال | UNIQUE، مفهرس للبحث |
| answer | TEXT | الإجابة المقابلة | |
| weight | REAL | وزن/موثوقية الإجابة | قيمة بين 0 و 1 |
| source | TEXT | مصدر المعلومات | مثال: "gemini_flash_2", "wikipedia", "user" |
| created_at | TIMESTAMP | وقت الإنشاء | القيمة الافتراضية: CURRENT_TIMESTAMP |
| created_by | TEXT | من أنشأ السجل | القيمة الافتراضية: "system" |
| modified_at | TIMESTAMP | وقت آخر تعديل | القيمة الافتراضية: CURRENT_TIMESTAMP |
| modified_by | TEXT | من قام بآخر تعديل | القيمة الافتراضية: "system" |

### الفهارس

| اسم الفهرس | الأعمدة | الوصف |
|------------|---------|-------------|
| idx_knowledge_question | question | تحسين البحث عن الأسئلة |

### المشغلات (للنمط PostgreSQL)

| اسم المشغل | وقت التنشيط | وظيفة |
|------------|-----------|-------------|
| update_knowledge_modtime | BEFORE UPDATE | تحديث حقل modified_at تلقائيًا |

## تصميم قاعدة البيانات

### مخطط نسق قاعدة البيانات SQLite

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

### مخطط نسق قاعدة البيانات PostgreSQL

```sql
CREATE TABLE IF NOT EXISTS knowledge (
    id SERIAL PRIMARY KEY,
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

CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.modified_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_knowledge_modtime
BEFORE UPDATE ON knowledge
FOR EACH ROW
EXECUTE FUNCTION update_modified_column();
```

## الوظائف الرئيسية للتعامل مع قاعدة البيانات

### init_db()
تهيئة قاعدة البيانات وإنشاء الجداول والفهارس وغيرها إذا لم تكن موجودة.

### get_connection()
إنشاء اتصال بقاعدة البيانات استنادًا إلى التكوين المتاح (SQLite أو PostgreSQL).

### release_connection(conn, is_postgres)
إغلاق اتصال قاعدة البيانات أو إعادته إلى تجمع الاتصالات.

### save_data(question, answer, weight, source, user="system")
حفظ أو تحديث سؤال وإجابة في قاعدة البيانات.

### load_data()
تحميل كل المعرفة المخزنة في قاعدة البيانات.

### search_knowledge(query, limit=10)
البحث في قاعدة البيانات باستخدام استعلام.

### get_knowledge_history(question)
استرداد تاريخ التعديلات لسؤال معين.

## ترحيل البيانات

### migrate_sqlite_to_postgres()
ترحيل البيانات من SQLite إلى PostgreSQL عندما يكون متاحًا. مفيد للترقية من نشر محلي إلى نشر مستضاف.

## تحسين الأداء

1. **تجمع الاتصال**: يتم استخدام تجمع الاتصال `ThreadedConnectionPool` لـ PostgreSQL لتحسين الأداء.
2. **الاسترداد بذاكرة التخزين المؤقت**: يمكن تنفيذ تخزين مؤقت لاستعلامات متكررة.
3. **الفهرسة**: تم فهرسة عمود `question` للبحث السريع.
4. **استعلامات البحث المتقدمة**: استخدام ميزات البحث النصي الكامل في PostgreSQL عند توفرها.

## مزامنة Elasticsearch (اختياري)

عند تكوين Elasticsearch، يوفر النظام الوظائف التالية:

### init_elasticsearch()
تهيئة فهرس Elasticsearch وتعيين التعيينات.

### sync_database_to_elasticsearch()
مزامنة جميع بيانات قاعدة البيانات مع Elasticsearch.

### index_document(question, answer, weight, source, ...)
فهرسة وثيقة واحدة في Elasticsearch.

## ملاحظات الاستخدام

1. **تخزين المعرفة**: استخدم `save_data()` للمعرفة الجديدة مع ضبط الوزن استنادًا إلى مصدر المعلومات.
2. **تحميل البيانات**: استخدم `load_data()` في بداية التطبيق لتجنب الاستعلامات المتكررة.
3. **البحث**: يؤدي `search_knowledge()` بحثًا أساسيًا، بينما يوفر الدمج مع Elasticsearch قدرات بحث أكثر تقدمًا.
4. **أمان البيانات**: تنفذ قاعدة البيانات التحقق من سلامة SQLite لتجنب تلف قاعدة البيانات.

## تخزين مستند JSON

بالإضافة إلى قاعدة البيانات الرئيسية، يستخدم النظام ملفات JSON للتخزين الإضافي:

### user_actions.json
يتتبع إجراءات المستخدم في تنسيق:
```json
{
  "version": "1.0",
  "actions": [
    {
      "timestamp": "2023-06-01T12:34:56.789Z",
      "user": "web_user",
      "action": "chat",
      "description": "سأل: ما هي الجاذبية؟"
    },
    ...
  ]
}
```

### learning_logs.json
يسجل أنشطة التعلم المستمر:
```json
{
  "logs": [
    {
      "timestamp": "2023-06-01T12:30:45.123Z",
      "action": "wikipedia_learning",
      "details": {
        "topic": "Artificial_intelligence",
        "question": "ما هو الذكاء الاصطناعي؟"
      }
    },
    ...
  ]
}
```

## استراتيجيات التطوير المستقبلي

1. **توزيع قاعدة البيانات**: تقسيم البيانات إلى جداول متعددة لتنظيم أفضل
2. **تدقيق متقدم**: تتبع جميع التغييرات في المحتوى للتحكم الكامل في الإصدار
3. **إدارة الأدوار**: تنفيذ أذونات وأدوار المستخدم
4. **التعافي من الكوارث**: تحسين آليات النسخ الاحتياطي واستعادة البيانات
