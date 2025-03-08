
# -*- coding: utf-8 -*-
"""
وحدة تحليل المشاعر للنصوص العربية والإنجليزية
"""
import re
import json
import os
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
import joblib

# قواميس الكلمات العاطفية
ARABIC_POSITIVE_WORDS = [
    "جميل", "رائع", "ممتاز", "جيد", "عظيم", "محترم", "مذهل", "سعيد", "فرح",
    "مبهج", "ناجح", "موفق", "متفوق", "مبدع", "مثالي", "مفيد", "ممتع", "محبوب",
    "ودود", "لطيف", "كريم", "مساعد", "متعاون", "مخلص", "صادق", "أمين", "وفي"
]

ARABIC_NEGATIVE_WORDS = [
    "سيء", "رديء", "قبيح", "سخيف", "تافه", "مزعج", "مقرف", "بشع", "مخيف",
    "مرعب", "فاشل", "محبط", "مؤلم", "متعب", "صعب", "معقد", "غاضب", "حزين",
    "مكتئب", "خائف", "متوتر", "قلق", "مرهق", "مريض", "مؤذي", "كاذب", "خائن"
]

ENGLISH_POSITIVE_WORDS = [
    "good", "great", "excellent", "amazing", "wonderful", "fantastic", "brilliant",
    "happy", "joyful", "pleased", "satisfied", "delighted", "successful", "perfect",
    "beautiful", "lovely", "helpful", "useful", "interesting", "outstanding", "awesome"
]

ENGLISH_NEGATIVE_WORDS = [
    "bad", "terrible", "awful", "horrible", "disappointing", "poor", "sad", "angry",
    "upset", "annoying", "irritating", "depressing", "frustrating", "boring", "disgusting",
    "ugly", "useless", "stupid", "difficult", "painful", "failure", "hate", "worst"
]

class SentimentAnalyzer:
    """محلل المشاعر للنصوص العربية والإنجليزية"""
    
    def __init__(self, language="both"):
        """تهيئة المحلل العاطفي"""
        self.language = language
        self.model_path = {
            "ar": "models/arabic_sentiment_model.pkl",
            "en": "models/english_sentiment_model.pkl"
        }
        self.vectorizers = {}
        self.models = {}
        
        # تحميل النماذج إذا كانت موجودة
        self._load_models()
    
    def _load_models(self):
        """محاولة تحميل النماذج المدربة مسبقاً"""
        for lang in ["ar", "en"]:
            try:
                model = joblib.load(self.model_path[lang])
                self.models[lang] = model
                print(f"تم تحميل نموذج {lang} بنجاح")
            except:
                print(f"لم يتم العثور على نموذج {lang}، سيتم إنشاء نموذج افتراضي")
                # إنشاء نموذج افتراضي باستخدام قواميس المشاعر
                self._create_default_model(lang)
    
    def _create_default_model(self, lang):
        """إنشاء نموذج افتراضي باستخدام قواميس المشاعر"""
        # إنشاء مصدر بيانات بسيط
        if lang == "ar":
            pos_words = ARABIC_POSITIVE_WORDS
            neg_words = ARABIC_NEGATIVE_WORDS
        else:  # en
            pos_words = ENGLISH_POSITIVE_WORDS
            neg_words = ENGLISH_NEGATIVE_WORDS
        
        # إنشاء جمل بسيطة للتدريب
        training_data = []
        labels = []
        
        # البيانات الإيجابية
        for word in pos_words:
            training_data.append(f"هذا {word}")
            labels.append(1)
            training_data.append(f"{word} جداً")
            labels.append(1)
        
        # البيانات السلبية
        for word in neg_words:
            training_data.append(f"هذا {word}")
            labels.append(0)
            training_data.append(f"{word} جداً")
            labels.append(0)
        
        # إنشاء النموذج
        vectorizer = TfidfVectorizer()
        X = vectorizer.fit_transform(training_data)
        model = LogisticRegression()
        model.fit(X, labels)
        
        # حفظ الموارد
        self.vectorizers[lang] = vectorizer
        self.models[lang] = model
    
    def _detect_language(self, text):
        """تحديد لغة النص"""
        arabic_pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+')
        if arabic_pattern.search(text):
            return "ar"
        return "en"  # افتراضي هو الإنجليزية
    
    def analyze_text(self, text):
        """تحليل عاطفة النص"""
        if not text or not isinstance(text, str):
            return {"sentiment": "neutral", "score": 0.5, "confidence": 0}
        
        # تحديد لغة النص
        lang = self._detect_language(text)
        
        # تحليل المشاعر بالاعتماد على القواميس (طريقة بسيطة)
        if lang == "ar":
            pos_dict = ARABIC_POSITIVE_WORDS
            neg_dict = ARABIC_NEGATIVE_WORDS
        else:  # en
            pos_dict = ENGLISH_POSITIVE_WORDS
            neg_dict = ENGLISH_NEGATIVE_WORDS
        
        # تنظيف النص
        text = text.lower()
        
        # عد الكلمات الإيجابية والسلبية
        positive_count = sum(1 for word in pos_dict if word in text)
        negative_count = sum(1 for word in neg_dict if word in text)
        
        # حساب النتيجة
        total = positive_count + negative_count
        if total == 0:
            sentiment = "neutral"
            score = 0.5
            confidence = 0
        else:
            score = positive_count / total
            if score > 0.6:
                sentiment = "positive"
            elif score < 0.4:
                sentiment = "negative"
            else:
                sentiment = "neutral"
            confidence = abs(score - 0.5) * 2  # 0 to 1
        
        # استخدام النموذج المتقدم إذا كان متاحاً
        if lang in self.models and self.vectorizers.get(lang):
            try:
                X = self.vectorizers[lang].transform([text])
                model_score = self.models[lang].predict_proba(X)[0][1]  # احتمال الإيجابية
                
                # دمج نتيجة النموذج مع تحليل القاموس
                score = (score + model_score) / 2
                if score > 0.6:
                    sentiment = "positive"
                elif score < 0.4:
                    sentiment = "negative"
                else:
                    sentiment = "neutral"
                confidence = abs(score - 0.5) * 2
            except:
                # استمر باستخدام النتيجة المحسوبة من القاموس
                pass
        
        return {
            "sentiment": sentiment,
            "score": score,
            "confidence": confidence,
            "language": lang,
            "positive_words": positive_count,
            "negative_words": negative_count
        }
    
    def train_model(self, texts, labels, language=None):
        """تدريب نموذج جديد على بيانات معينة"""
        if language is None:
            language = self._detect_language(texts[0]) if texts else "en"
        
        # إنشاء النموذج
        vectorizer = TfidfVectorizer()
        X = vectorizer.fit_transform(texts)
        
        # تقسيم البيانات
        X_train, X_test, y_train, y_test = train_test_split(
            X, labels, test_size=0.2, random_state=42
        )
        
        # تدريب النموذج
        model = LogisticRegression()
        model.fit(X_train, y_train)
        
        # تقييم النموذج
        accuracy = model.score(X_test, y_test)
        
        # حفظ النموذج
        self.vectorizers[language] = vectorizer
        self.models[language] = model
        
        # إنشاء المجلد إذا لم يكن موجوداً
        os.makedirs(os.path.dirname(self.model_path[language]), exist_ok=True)
        
        # حفظ النموذج إلى ملف
        model_pipeline = Pipeline([
            ('vectorizer', vectorizer),
            ('classifier', model)
        ])
        joblib.dump(model_pipeline, self.model_path[language])
        
        return {
            "accuracy": accuracy,
            "language": language,
            "model_path": self.model_path[language]
        }
    
    @staticmethod
    def get_emotion_emoji(sentiment):
        """الحصول على رمز تعبيري للمشاعر"""
        if sentiment == "positive":
            return "😃"
        elif sentiment == "negative":
            return "😔"
        else:
            return "😐"

# وظيفة تحليل المشاعر لاستخدامها في الواجهة الرئيسية
def analyze_sentiment(text):
    """تحليل مشاعر النص باستخدام محلل المشاعر"""
    analyzer = SentimentAnalyzer()
    result = analyzer.analyze_text(text)
    return result
