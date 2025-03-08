
# -*- coding: utf-8 -*-
"""
وحدة معالجة اللغة العربية للذكاء الاصطناعي
"""
import re
import json
import os
from collections import Counter
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk

# تنزيل البيانات المطلوبة إذا لم تكن موجودة
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

# قائمة الحروف العربية
ARABIC_LETTERS = "ابتثجحخدذرزسشصضطظعغفقكلمنهويءآأؤإئ"
# قائمة حروف العلة العربية
ARABIC_VOWELS = "اويءآأؤإئ"
# كلمات التوقف العربية الشائعة
ARABIC_STOP_WORDS = [
    "من", "إلى", "عن", "على", "في", "مع", "هذا", "هذه", "ذلك", "تلك",
    "هناك", "هنا", "أنا", "أنت", "هو", "هي", "نحن", "هم", "كان", "كانت",
    "يكون", "أن", "إن", "لا", "ما", "لم", "لن", "و", "أو", "ثم", "بل",
    "كما", "حتى", "إذا", "لو", "لكن", "مثل", "مثلما", "منذ", "عندما",
    "قد", "ليس", "كل", "بعض", "غير", "بين", "فوق", "تحت", "أمام", "خلف"
]

class ArabicNLP:
    """فئة لمعالجة النصوص العربية"""
    
    @staticmethod
    def normalize_arabic_text(text):
        """تعديل النص العربي وتوحيد شكله"""
        if not text or not isinstance(text, str):
            return ""
            
        # استبدال الحركات والتشكيل
        text = re.sub(r'[\u064B-\u065F]', '', text)
        
        # استبدال أشكال الألف المختلفة
        text = re.sub(r'[آأإٱ]', 'ا', text)
        
        # استبدال التاء المربوطة بالتاء المفتوحة
        text = re.sub('ة', 'ه', text)
        
        # استبدال الياء المقصورة بالياء العادية
        text = re.sub('ى', 'ي', text)
        
        # حذف المسافات الزائدة
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    @staticmethod
    def tokenize_arabic(text):
        """تقسيم النص العربي إلى كلمات"""
        text = ArabicNLP.normalize_arabic_text(text)
        # استخدام nltk لتقسيم النص
        words = nltk.word_tokenize(text)
        # تصفية الكلمات للاحتفاظ بالكلمات العربية فقط
        arabic_words = [w for w in words if any(c in ARABIC_LETTERS for c in w)]
        return arabic_words
    
    @staticmethod
    def remove_stopwords(words):
        """إزالة كلمات التوقف العربية"""
        return [w for w in words if w not in ARABIC_STOP_WORDS]
    
    @staticmethod
    def get_word_frequency(text):
        """حساب تكرار الكلمات في النص"""
        words = ArabicNLP.tokenize_arabic(text)
        words = ArabicNLP.remove_stopwords(words)
        return Counter(words)
    
    @staticmethod
    def get_similarity(text1, text2):
        """حساب التشابه بين نصين باستخدام التجيب التمثيل المتجهي TF-IDF"""
        text1 = ArabicNLP.normalize_arabic_text(text1)
        text2 = ArabicNLP.normalize_arabic_text(text2)
        
        # TF-IDF Vectorizer
        vectorizer = TfidfVectorizer()
        try:
            tfidf_matrix = vectorizer.fit_transform([text1, text2])
            # حساب تشابه الجيب تمام
            cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return cosine_sim
        except:
            return 0.0
    
    @staticmethod
    def extract_arabic_entities(text):
        """استخراج الكيانات المسماة من النص العربي (مبسط)"""
        entities = {
            "أشخاص": [],
            "أماكن": [],
            "منظمات": [],
            "تواريخ": []
        }
        
        # قائمة مبسطة للكشف عن الأشخاص
        person_indicators = ["السيد", "السيدة", "الدكتور", "الأستاذ", "المهندس", "الشيخ", "الرئيس", "الملك", "الأمير", "بن", "ابن"]
        # قائمة مبسطة للكشف عن الأماكن
        place_indicators = ["مدينة", "قرية", "دولة", "بلد", "جمهورية", "مملكة", "شارع", "منطقة", "حي", "محافظة", "ولاية"]
        # قائمة مبسطة للكشف عن المنظمات
        org_indicators = ["شركة", "مؤسسة", "جامعة", "منظمة", "هيئة", "وزارة", "مديرية", "مركز", "جمعية", "مجلس"]
        # قائمة مبسطة للكشف عن التواريخ
        date_indicators = ["يوم", "شهر", "سنة", "عام", "أسبوع", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد", 
                         "يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]
        
        words = ArabicNLP.tokenize_arabic(text)
        
        # البحث عن أنماط بسيطة
        for i, word in enumerate(words):
            if i > 0:
                # البحث عن الأشخاص
                if words[i-1] in person_indicators:
                    entities["أشخاص"].append(word)
                # البحث عن الأماكن
                elif words[i-1] in place_indicators:
                    entities["أماكن"].append(word)
                # البحث عن المنظمات
                elif words[i-1] in org_indicators:
                    entities["منظمات"].append(word)
                # البحث عن التواريخ
                elif words[i-1] in date_indicators and word.isdigit():
                    entities["تواريخ"].append(f"{words[i-1]} {word}")
        
        return entities
    
    @staticmethod
    def analyze_arabic_text(text):
        """تحليل شامل للنص العربي"""
        text = ArabicNLP.normalize_arabic_text(text)
        words = ArabicNLP.tokenize_arabic(text)
        clean_words = ArabicNLP.remove_stopwords(words)
        
        # إحصائيات عامة
        word_count = len(words)
        unique_words = len(set(words))
        letter_count = sum(len(word) for word in words)
        avg_word_length = letter_count / word_count if word_count > 0 else 0
        
        # كلمات مفتاحية
        word_freq = ArabicNLP.get_word_frequency(text)
        keywords = [word for word, count in word_freq.most_common(10)]
        
        # استخراج الكيانات
        entities = ArabicNLP.extract_arabic_entities(text)
        
        return {
            "إحصائيات": {
                "عدد_الكلمات": word_count,
                "كلمات_فريدة": unique_words,
                "متوسط_طول_الكلمة": avg_word_length
            },
            "كلمات_مفتاحية": keywords,
            "كيانات": entities
        }

# وظيفة لمعالجة النص العربي في الذكاء الاصطناعي
def process_arabic_query(query):
    """معالجة الاستعلام باللغة العربية"""
    
    # تنظيف النص وتحليله
    normalized_query = ArabicNLP.normalize_arabic_text(query)
    analysis = ArabicNLP.analyze_arabic_text(query)
    
    # فحص اللغة للتأكد من وجود نص عربي
    is_arabic = any(c in ARABIC_LETTERS for c in query)
    
    # اكتشاف نوع الاستعلام
    query_type = "غير محدد"
    if "ما هو" in query or "ما هي" in query:
        query_type = "تعريف"
    elif "كيف" in query:
        query_type = "إجراء"
    elif "متى" in query:
        query_type = "زمني"
    elif "أين" in query:
        query_type = "مكاني"
    elif "لماذا" in query:
        query_type = "سببي"
    elif "من هو" in query or "من هي" in query:
        query_type = "شخصي"
    
    return {
        "query": query,
        "normalized": normalized_query,
        "is_arabic": is_arabic,
        "query_type": query_type,
        "keywords": analysis["كلمات_مفتاحية"],
        "entities": analysis["كيانات"]
    }

# حفظ ملفات بيانات اللغة العربية
def save_arabic_data(file_path="data/arabic_corpus.json", data=None):
    """حفظ بيانات اللغة العربية في ملف JSON"""
    if data is None:
        data = {}
    
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# تحميل ملفات بيانات اللغة العربية
def load_arabic_data(file_path="data/arabic_corpus.json"):
    """تحميل بيانات اللغة العربية من ملف JSON"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
