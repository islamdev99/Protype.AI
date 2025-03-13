
# -*- coding: utf-8 -*-
"""
وحدة تحليل البيانات المتقدمة للذكاء الاصطناعي
"""

import os
import json
import re
import numpy as np
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt
from io import BytesIO
import base64

class DataAnalyzer:
    """محلل البيانات المتقدم للذكاء الاصطناعي"""
    
    def __init__(self, db_path="protype_e0.db"):
        """تهيئة محلل البيانات"""
        self.db_path = db_path
    
    def analyze_knowledge_base(self):
        """تحليل قاعدة المعرفة وإنتاج إحصائيات وتقارير"""
        try:
            # اتصال بقاعدة البيانات
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # استخراج إحصائيات عامة
            cursor.execute("SELECT COUNT(*) FROM knowledge")
            total_questions = cursor.fetchone()[0]
            
            cursor.execute("SELECT AVG(LENGTH(answer)) FROM knowledge")
            avg_answer_length = cursor.fetchone()[0]
            
            cursor.execute("SELECT source, COUNT(*) FROM knowledge GROUP BY source")
            source_stats = cursor.fetchall()
            
            cursor.execute("SELECT created_at, COUNT(*) FROM knowledge GROUP BY DATE(created_at)")
            time_stats = cursor.fetchall()
            
            # تحليل أنواع الأسئلة
            question_types = {}
            cursor.execute("SELECT question FROM knowledge")
            questions = [q[0] for q in cursor.fetchall()]
            
            for question in questions:
                q_type = self._classify_question(question)
                question_types[q_type] = question_types.get(q_type, 0) + 1
            
            # تحليل محتوى الإجابات
            cursor.execute("SELECT answer FROM knowledge")
            answers = [a[0] for a in cursor.fetchall()]
            
            answer_length_distribution = self._analyze_text_length(answers)
            
            # تحليل الكلمات المفتاحية
            keywords_data = self._extract_common_keywords(questions + answers)
            
            # إغلاق الاتصال
            conn.close()
            
            # تجميع النتائج
            results = {
                "general_stats": {
                    "total_questions": total_questions,
                    "avg_answer_length": avg_answer_length
                },
                "source_stats": {src: count for src, count in source_stats},
                "time_stats": {str(date): count for date, count in time_stats},
                "question_types": question_types,
                "answer_length_distribution": answer_length_distribution,
                "keywords": keywords_data
            }
            
            return results
        except Exception as e:
            print(f"خطأ في تحليل قاعدة المعرفة: {e}")
            return {"error": str(e)}
    
    def _classify_question(self, question):
        """تصنيف نوع السؤال"""
        question = question.lower()
        
        if question.startswith('search:'):
            return "search"
        elif any(q in question for q in ['ما هو', 'ما هي', 'عرف']):
            return "definition"
        elif any(q in question for q in ['كيف', 'طريقة']):
            return "how_to"
        elif any(q in question for q in ['لماذا', 'سبب']):
            return "why"
        elif any(q in question for q in ['متى', 'تاريخ']):
            return "when"
        elif any(q in question for q in ['أين', 'مكان']):
            return "where"
        elif any(q in question for q in ['من هو', 'من هي']):
            return "who"
        elif any(q in question for q in ['مقارنة', 'أفضل']):
            return "comparison"
        else:
            return "other"
    
    def _analyze_text_length(self, texts):
        """تحليل طول النصوص وتوزيعها"""
        lengths = [len(text) for text in texts]
        
        return {
            "min": min(lengths) if lengths else 0,
            "max": max(lengths) if lengths else 0,
            "avg": sum(lengths) / len(lengths) if lengths else 0,
            "distribution": {
                "short (0-100)": sum(1 for l in lengths if l <= 100),
                "medium (101-500)": sum(1 for l in lengths if 100 < l <= 500),
                "long (501-1000)": sum(1 for l in lengths if 500 < l <= 1000),
                "very_long (1000+)": sum(1 for l in lengths if l > 1000)
            }
        }
    
    def _extract_common_keywords(self, texts, n=20):
        """استخراج الكلمات الأكثر شيوعاً"""
        # قائمة كلمات التوقف (stop words) العربية الشائعة
        stop_words = [
            "من", "إلى", "عن", "على", "في", "مع", "هذا", "هذه", "ذلك", "تلك",
            "هناك", "هنا", "أنا", "أنت", "هو", "هي", "نحن", "هم", "كان", "كانت",
            "يكون", "أن", "إن", "لا", "ما", "لم", "لن", "و", "أو", "ثم", "بل",
            "كما", "حتى", "إذا", "لو", "لكن", "مثل", "مثلما", "منذ", "عندما",
            "قد", "ليس", "كل", "بعض", "غير", "بين", "فوق", "تحت", "أمام", "خلف"
        ]
        
        # تجميع كل النصوص وتقسيمها إلى كلمات
        all_words = []
        for text in texts:
            if text:
                # تنظيف النص وتقسيمه إلى كلمات
                words = re.findall(r'\w+', text.lower())
                all_words.extend(words)
        
        # تصفية كلمات التوقف والكلمات القصيرة
        filtered_words = [word for word in all_words if word not in stop_words and len(word) > 2]
        
        # حساب تكرار الكلمات
        word_counts = {}
        for word in filtered_words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        # ترتيب الكلمات حسب التكرار
        sorted_keywords = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        
        # إرجاع أكثر n كلمة شيوعاً
        return {word: count for word, count in sorted_keywords[:n]}
    
    def analyze_learning_trends(self):
        """تحليل اتجاهات التعلم من سجلات التعلم"""
        try:
            # تحميل سجلات التعلم
            log_file = "learning_logs.json"
            if not os.path.exists(log_file):
                return {"error": "ملف سجلات التعلم غير موجود"}
            
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            
            # استخراج سجلات التعلم
            entries = logs.get("logs", [])
            
            if not entries:
                return {"error": "لا توجد سجلات تعلم"}
            
            # تحليل مصادر التعلم
            sources = {}
            for entry in entries:
                source = entry.get("source", "unknown")
                sources[source] = sources.get(source, 0) + 1
            
            # تحليل توزيع التعلم عبر الزمن
            time_distribution = {}
            for entry in entries:
                timestamp = entry.get("timestamp", "")
                if timestamp:
                    date = timestamp.split("T")[0]
                    time_distribution[date] = time_distribution.get(date, 0) + 1
            
            # تحليل أنواع الإجراءات
            actions = {}
            for entry in entries:
                action = entry.get("action", "unknown")
                actions[action] = actions.get(action, 0) + 1
            
            # تحليل المواضيع المتعلمة
            topics = []
            for entry in entries:
                topic = entry.get("topic", "")
                if topic:
                    topics.append(topic)
            
            topic_analysis = self._analyze_topics(topics)
            
            return {
                "total_entries": len(entries),
                "sources": sources,
                "time_distribution": time_distribution,
                "actions": actions,
                "topic_analysis": topic_analysis
            }
        
        except Exception as e:
            print(f"خطأ في تحليل اتجاهات التعلم: {e}")
            return {"error": str(e)}
    
    def _analyze_topics(self, topics):
        """تحليل المواضيع التي تم تعلمها"""
        if not topics:
            return {}
        
        # تصنيف المواضيع
        categories = {
            "technology": ["ai", "web", "computer", "programming", "software", "hardware", "internet", "technology", "digital"],
            "science": ["physics", "chemistry", "biology", "science", "scientific", "research", "experiment"],
            "arts": ["art", "music", "painting", "literature", "poetry", "novel", "dance", "theater"],
            "history": ["history", "historical", "ancient", "medieval", "century", "civilization", "empire"],
            "sports": ["sport", "football", "soccer", "basketball", "tennis", "olympics", "athlete"],
            "health": ["health", "medical", "medicine", "disease", "treatment", "doctor", "hospital"],
            "business": ["business", "economy", "finance", "market", "company", "entrepreneurship"],
            "politics": ["politics", "government", "policy", "law", "president", "minister", "election"],
            "education": ["education", "university", "school", "student", "teacher", "learning", "academic"]
        }
        
        topic_categories = {}
        uncategorized = []
        
        for topic in topics:
            topic_lower = topic.lower()
            categorized = False
            
            for category, keywords in categories.items():
                if any(keyword in topic_lower for keyword in keywords):
                    topic_categories[category] = topic_categories.get(category, 0) + 1
                    categorized = True
                    break
            
            if not categorized:
                uncategorized.append(topic)
        
        if uncategorized:
            topic_categories["other"] = len(uncategorized)
        
        return {
            "categories": topic_categories,
            "unique_topics": len(set(topics)),
            "uncategorized_sample": uncategorized[:10]  # عينة من المواضيع غير المصنفة
        }
    
    def generate_visualization(self, data_type="knowledge_sources"):
        """إنشاء تصور بياني لمجموعة بيانات"""
        plt.figure(figsize=(10, 6))
        
        if data_type == "knowledge_sources":
            # تحليل مصادر المعرفة
            kb_analysis = self.analyze_knowledge_base()
            if "error" in kb_analysis:
                return {"error": kb_analysis["error"]}
            
            source_stats = kb_analysis.get("source_stats", {})
            sources = list(source_stats.keys())
            counts = list(source_stats.values())
            
            plt.bar(sources, counts, color='skyblue')
            plt.xlabel('مصادر المعرفة')
            plt.ylabel('عدد العناصر')
            plt.title('توزيع عناصر المعرفة حسب المصدر')
            plt.xticks(rotation=45, ha='right')
            
        elif data_type == "question_types":
            # تحليل أنواع الأسئلة
            kb_analysis = self.analyze_knowledge_base()
            if "error" in kb_analysis:
                return {"error": kb_analysis["error"]}
            
            question_types = kb_analysis.get("question_types", {})
            types = list(question_types.keys())
            counts = list(question_types.values())
            
            plt.pie(counts, labels=types, autopct='%1.1f%%', startangle=90, shadow=True)
            plt.title('توزيع أنواع الأسئلة')
            
        elif data_type == "learning_timeline":
            # تحليل خط زمني للتعلم
            learning_analysis = self.analyze_learning_trends()
            if "error" in learning_analysis:
                return {"error": learning_analysis["error"]}
            
            time_distribution = learning_analysis.get("time_distribution", {})
            dates = list(time_distribution.keys())
            counts = list(time_distribution.values())
            
            # ترتيب التواريخ
            sorted_data = sorted(zip(dates, counts))
            sorted_dates, sorted_counts = zip(*sorted_data) if sorted_data else ([], [])
            
            plt.plot(sorted_dates, sorted_counts, marker='o', linestyle='-', color='green')
            plt.xlabel('التاريخ')
            plt.ylabel('عدد عمليات التعلم')
            plt.title('اتجاهات التعلم المستمر عبر الزمن')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
        elif data_type == "learning_sources":
            # تحليل مصادر التعلم
            learning_analysis = self.analyze_learning_trends()
            if "error" in learning_analysis:
                return {"error": learning_analysis["error"]}
            
            sources = learning_analysis.get("sources", {})
            source_names = list(sources.keys())
            counts = list(sources.values())
            
            plt.bar(source_names, counts, color='lightgreen')
            plt.xlabel('مصادر التعلم')
            plt.ylabel('عدد العناصر')
            plt.title('توزيع التعلم حسب المصدر')
            plt.xticks(rotation=45, ha='right')
            
        else:
            return {"error": "نوع التصور البياني غير مدعوم"}
        
        # حفظ الرسم البياني كصورة في الذاكرة
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        
        # تحويل الصورة إلى سلسلة Base64
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        # إغلاق الرسم البياني لتجنب تسرب الذاكرة
        plt.close()
        
        return {
            "image_data": f"data:image/png;base64,{image_base64}",
            "visualization_type": data_type
        }
    
    def generate_report(self, report_type="comprehensive"):
        """إنشاء تقرير شامل أو مختصر"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if report_type == "comprehensive":
            # تحليل قاعدة المعرفة
            kb_analysis = self.analyze_knowledge_base()
            
            # تحليل اتجاهات التعلم
            learning_analysis = self.analyze_learning_trends()
            
            # إنشاء التصور البياني
            visualizations = {
                "knowledge_sources": self.generate_visualization("knowledge_sources"),
                "question_types": self.generate_visualization("question_types"),
                "learning_timeline": self.generate_visualization("learning_timeline")
            }
            
            # تجميع التقرير
            report = {
                "timestamp": timestamp,
                "report_type": "تقرير شامل",
                "knowledge_base_analysis": kb_analysis,
                "learning_trends_analysis": learning_analysis,
                "visualizations": visualizations
            }
        else:  # summary
            # تحليل مختصر لقاعدة المعرفة
            kb_analysis = self.analyze_knowledge_base()
            kb_summary = {
                "total_questions": kb_analysis.get("general_stats", {}).get("total_questions", 0),
                "source_distribution": kb_analysis.get("source_stats", {})
            }
            
            # تحليل مختصر لاتجاهات التعلم
            learning_analysis = self.analyze_learning_trends()
            learning_summary = {
                "total_entries": learning_analysis.get("total_entries", 0),
                "source_distribution": learning_analysis.get("sources", {})
            }
            
            # تجميع التقرير
            report = {
                "timestamp": timestamp,
                "report_type": "تقرير مختصر",
                "knowledge_base_summary": kb_summary,
                "learning_trends_summary": learning_summary
            }
        
        # حفظ التقرير في ملف JSON
        report_file = f"reports/ai_analysis_report_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=4)
        
        return {
            "message": f"تم إنشاء التقرير بنجاح",
            "report_file": report_file,
            "report_summary": {
                "timestamp": timestamp,
                "report_type": report_type,
                "kb_questions": kb_analysis.get("general_stats", {}).get("total_questions", 0),
                "learning_entries": learning_analysis.get("total_entries", 0) if "error" not in learning_analysis else 0
            }
        }

# وظيفة مساعدة للاستخدام في الواجهة الرئيسية
def analyze_ai_system():
    """تحليل شامل لنظام الذكاء الاصطناعي"""
    analyzer = DataAnalyzer()
    
    # تحليل قاعدة المعرفة
    kb_analysis = analyzer.analyze_knowledge_base()
    
    # تحليل اتجاهات التعلم
    learning_analysis = analyzer.analyze_learning_trends()
    
    # إنشاء التصور البياني للمصادر
    visualization = analyzer.generate_visualization("knowledge_sources")
    
    return {
        "kb_analysis": kb_analysis,
        "learning_analysis": learning_analysis,
        "visualization": visualization
    }

# وظيفة لإنشاء تقرير شامل
def generate_full_report():
    """إنشاء تقرير شامل عن نظام الذكاء الاصطناعي"""
    analyzer = DataAnalyzer()
    report_result = analyzer.generate_report("comprehensive")
    return report_result
