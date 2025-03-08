
# -*- coding: utf-8 -*-
"""
وحدة التعرف على الصور باستخدام التعلم العميق
"""

import os
import json
import base64
import numpy as np
from io import BytesIO
from PIL import Image

# تقديم محاكاة لوظائف التعلم العميق
# في البيئة الحقيقية، سنستخدم TensorFlow أو PyTorch

class ImageRecognizer:
    """فئة للتعرف على محتوى الصور"""
    
    def __init__(self):
        """تهيئة محرك التعرف على الصور"""
        # قائمة الفئات التي يمكن التعرف عليها
        self.categories = [
            "شخص", "حيوان", "نبات", "طعام", "مبنى", "منظر طبيعي", "سيارة", "آلة",
            "رياضة", "أثاث", "إلكترونيات", "ملابس", "فن", "أداة", "كتاب", "لعبة"
        ]
        
        # البيانات الوصفية الإضافية التي يمكن استخراجها
        self.attributes = {
            "لون": ["أحمر", "أخضر", "أزرق", "أصفر", "برتقالي", "أرجواني", "أبيض", "أسود", "رمادي", "بني"],
            "شكل": ["مربع", "دائري", "مثلث", "بيضاوي", "مستطيل", "غير منتظم"],
            "حجم": ["صغير", "متوسط", "كبير"],
            "مظهر": ["لامع", "باهت", "شفاف", "معتم", "خشن", "ناعم"]
        }
        
        # سجل التعرف
        self.recognition_log = []
    
    def _preprocess_image(self, image_data):
        """معالجة أولية للصورة"""
        try:
            # إذا كان المدخل هو سلسلة Base64
            if isinstance(image_data, str) and image_data.startswith('data:image'):
                # استخراج بيانات Base64
                image_data = image_data.split(',')[1]
                image = Image.open(BytesIO(base64.b64decode(image_data)))
            # إذا كان المدخل هو مسار ملف
            elif isinstance(image_data, str) and os.path.exists(image_data):
                image = Image.open(image_data)
            # إذا كان المدخل هو كائن صورة بالفعل
            elif isinstance(image_data, Image.Image):
                image = image_data
            # إذا كان المدخل هو مصفوفة numpy
            elif isinstance(image_data, np.ndarray):
                image = Image.fromarray(image_data)
            else:
                raise ValueError("تنسيق صورة غير مدعوم")
            
            # تغيير حجم الصورة لتناسب النموذج
            image = image.resize((224, 224))
            return image
        except Exception as e:
            print(f"خطأ في معالجة الصورة: {e}")
            return None
    
    def _extract_features(self, image):
        """استخراج الميزات من الصورة"""
        # في التنفيذ الحقيقي، سيتم هنا تمرير الصورة إلى نموذج الشبكة العصبية
        # هنا نقوم بمحاكاة ذلك بتحليل بسيط للصورة
        
        # تحويل الصورة إلى مصفوفة
        img_array = np.array(image)
        
        # حساب متوسط اللون في الصورة
        avg_color = np.mean(img_array, axis=(0, 1))
        
        # حساب متوسط السطوع
        if len(avg_color) >= 3:
            brightness = 0.299 * avg_color[0] + 0.587 * avg_color[1] + 0.114 * avg_color[2]
        else:
            brightness = np.mean(avg_color)
        
        # حساب تباين الصورة
        contrast = np.std(img_array)
        
        return {
            "avg_color": avg_color.tolist() if isinstance(avg_color, np.ndarray) else avg_color,
            "brightness": float(brightness),
            "contrast": float(contrast),
            "dimensions": image.size
        }
    
    def _simulate_recognition(self, features):
        """محاكاة عملية التعرف باستخدام خوارزمية بسيطة"""
        # توليد نتائج مشابهة لما قد ينتجه نموذج تعلم عميق حقيقي
        
        # تخصيص فئة بناءً على ميزات الصورة
        brightness = features["brightness"]
        contrast = features["contrast"]
        
        # توليد تقييمات احتمالية للفئات
        np.random.seed(int(brightness * 100) + int(contrast * 10))
        probabilities = np.random.random(len(self.categories))
        probabilities = probabilities / np.sum(probabilities)
        
        # ترتيب الفئات حسب الاحتمالية
        category_probs = [(cat, prob) for cat, prob in zip(self.categories, probabilities)]
        category_probs.sort(key=lambda x: x[1], reverse=True)
        
        # استخراج السمات
        selected_attributes = {}
        for attr_type, attr_values in self.attributes.items():
            selected_idx = np.random.randint(0, len(attr_values))
            selected_attributes[attr_type] = attr_values[selected_idx]
        
        return {
            "top_categories": category_probs[:5],  # أعلى 5 فئات
            "attributes": selected_attributes
        }
    
    def recognize_image(self, image_data):
        """التعرف على محتوى الصورة"""
        # معالجة الصورة
        processed_image = self._preprocess_image(image_data)
        if processed_image is None:
            return {"error": "فشل في معالجة الصورة"}
        
        # استخراج الميزات
        features = self._extract_features(processed_image)
        
        # محاكاة عملية التعرف
        recognition_results = self._simulate_recognition(features)
        
        # إعداد النتيجة النهائية
        result = {
            "main_category": recognition_results["top_categories"][0][0],
            "confidence": recognition_results["top_categories"][0][1],
            "alternative_categories": [
                {"category": cat, "probability": prob}
                for cat, prob in recognition_results["top_categories"][1:]
            ],
            "attributes": recognition_results["attributes"],
            "features": features
        }
        
        # تسجيل النتيجة
        self.recognition_log.append({
            "timestamp": __import__('datetime').datetime.now().isoformat(),
            "main_category": result["main_category"],
            "confidence": result["confidence"]
        })
        
        return result
    
    def get_log(self):
        """الحصول على سجل التعرف"""
        return self.recognition_log
    
    def save_log(self, file_path="logs/image_recognition_log.json"):
        """حفظ سجل التعرف إلى ملف"""
        # إنشاء المجلد إذا لم يكن موجوداً
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.recognition_log, f, ensure_ascii=False, indent=4)
        
        return {"message": f"تم حفظ السجل في {file_path}", "count": len(self.recognition_log)}

# وظيفة مساعدة للاستخدام في الواجهة الرئيسية
def recognize_image(image_data):
    """تعرف على محتوى الصورة باستخدام محرك التعرف"""
    recognizer = ImageRecognizer()
    result = recognizer.recognize_image(image_data)
    return result

# وظيفة لتحويل صورة إلى نص وصفي
def image_to_description(image_data):
    """إنشاء وصف نصي للصورة"""
    recognition_result = recognize_image(image_data)
    
    if "error" in recognition_result:
        return "لم أتمكن من التعرف على هذه الصورة."
    
    # بناء وصف مفصل
    main_category = recognition_result["main_category"]
    confidence = recognition_result["confidence"] * 100
    attributes = recognition_result["attributes"]
    
    # إنشاء الوصف
    description = f"يظهر في الصورة {main_category} "
    
    # إضافة الصفات
    attributes_text = []
    for attr_type, attr_value in attributes.items():
        attributes_text.append(f"{attr_type}ه {attr_value}")
    
    if attributes_text:
        description += f"({', '.join(attributes_text)})"
    
    # إضافة مستوى الثقة
    description += f". مستوى الثقة في التحليل: {confidence:.1f}%."
    
    # إضافة فئات بديلة
    alternatives = [item["category"] for item in recognition_result["alternative_categories"][:2]]
    if alternatives:
        description += f" قد تكون الصورة أيضًا: {' أو '.join(alternatives)}."
    
    return description
