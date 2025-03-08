
# -*- coding: utf-8 -*-
"""
وحدة التفكير العميق للذكاء الاصطناعي
"""
import re
import json
import time
import random
import os

class DeepThinking:
    """فئة للتحليل المنطقي وتوليد أفكار معمقة"""
    
    def __init__(self):
        """تهيئة محرك التفكير العميق"""
        # قوالب التفكير
        self.thinking_templates = {
            "factual": [
                "هناك عدة حقائق يمكن استخلاصها من هذا الموضوع...",
                "من الناحية الواقعية، نستطيع تحليل الموضوع كالتالي...",
                "بالنظر إلى الحقائق المتوفرة، يمكن القول أن..."
            ],
            "process": [
                "لنفكر في هذه العملية خطوة بخطوة...",
                "يمكن تقسيم هذه العملية إلى مراحل متتالية...",
                "لفهم كيفية عمل هذا، دعنا نتتبع الخطوات التالية..."
            ],
            "reasoning": [
                "هناك عدة أسباب منطقية تفسر هذا الأمر...",
                "بتحليل الأسباب والنتائج، يمكننا استنتاج...",
                "المنطق وراء هذا الأمر يكمن في..."
            ],
            "temporal": [
                "لنلقي نظرة على التسلسل الزمني للأحداث...",
                "تطور هذا الموضوع عبر الزمن كالتالي...",
                "من منظور تاريخي، يمكننا ملاحظة..."
            ],
            "spatial": [
                "بالنظر إلى الموقع الجغرافي، نلاحظ...",
                "التوزيع المكاني لهذه الظاهرة يشير إلى...",
                "من ناحية الموقع والعلاقات المكانية..."
            ],
            "person": [
                "بدراسة الشخصيات المؤثرة في هذا المجال...",
                "الأفراد الذين ساهموا في هذا الموضوع هم...",
                "من خلال فهم دوافع وإنجازات الشخصيات المعنية..."
            ],
            "selection": [
                "عند المقارنة بين الخيارات المتاحة...",
                "لتحديد الخيار الأفضل، يجب النظر في...",
                "تقييم البدائل يقودنا إلى..."
            ],
            "capability": [
                "لفهم القدرات والإمكانيات المتاحة...",
                "تحليل ما يمكن وما لا يمكن إنجازه...",
                "بالنظر إلى حدود الإمكانيات الحالية..."
            ],
            "future": [
                "استشراف المستقبل لهذا الموضوع يشير إلى...",
                "التوجهات المستقبلية المحتملة تتضمن...",
                "بناءً على المعطيات الحالية، يمكننا توقع..."
            ],
            "possibility": [
                "لنستكشف الاحتمالات المختلفة...",
                "هناك عدة سيناريوهات محتملة...",
                "من بين الاحتمالات الممكنة..."
            ],
            "recommendation": [
                "بعد دراسة متأنية، أوصي بما يلي...",
                "الخطوات المقترحة لتحقيق أفضل النتائج...",
                "بناءً على التحليل السابق، ينصح بـ..."
            ],
            "hypothetical": [
                "في حالة افتراضية مماثلة...",
                "لو افترضنا أن...",
                "في سيناريو مشابه..."
            ],
            "comparative": [
                "عند مقارنة الجوانب المختلفة...",
                "نقاط التشابه والاختلاف تشمل...",
                "تحليل مقارن يكشف عن..."
            ],
            "exemplification": [
                "لتوضيح هذه الفكرة، إليك بعض الأمثلة...",
                "النماذج التوضيحية التالية تساعد على فهم...",
                "لنستعرض بعض الحالات كأمثلة..."
            ],
            "definition": [
                "تعريف هذا المفهوم يتضمن...",
                "لفهم المعنى الدقيق، يجب توضيح...",
                "مصطلح يشير إلى..."
            ],
            "opinion": [
                "مع مراعاة وجهات النظر المختلفة...",
                "تتنوع الآراء حول هذا الموضوع...",
                "بالنظر إلى مختلف المنظورات..."
            ],
            "general": [
                "بشكل عام، يمكن القول...",
                "من المنظور الشامل...",
                "بالنظر إلى الصورة الكلية..."
            ]
        }
        
        # أنماط المحادثة
        self.conversation_patterns = [
            {"pattern": "فكرة توسعية", "response": "لنتوسع في هذه الفكرة من زاوية أخرى..."},
            {"pattern": "تناقض ظاهري", "response": "هناك تناقض ظاهري هنا، لكن يمكن حله من خلال..."},
            {"pattern": "تلخيص", "response": "لتلخيص ما ناقشناه حتى الآن..."},
            {"pattern": "سؤال توجيهي", "response": "لنفكر في السؤال التالي للتعمق أكثر..."},
            {"pattern": "مثال توضيحي", "response": "لتوضيح هذه النقطة، دعنا نتخيل المثال التالي..."},
            {"pattern": "استدراك", "response": "من المهم الإشارة إلى أن..."},
            {"pattern": "سياق تاريخي", "response": "وضع هذا الموضوع في سياقه التاريخي يساعدنا على فهم..."},
            {"pattern": "تحليل الأثر", "response": "لنفكر في الآثار المترتبة على ذلك..."},
            {"pattern": "تحول منطقي", "response": "هذا يقودنا منطقياً إلى..."},
            {"pattern": "تفنيد", "response": "على الرغم من شيوع هذه الفكرة، إلا أن..."}
        ]
        
        # سجل التفكير
        self.thinking_log = []
    
    def _analyze_question_type(self, question):
        """تحليل نوع السؤال"""
        # قواعد بسيطة لتصنيف نوع السؤال
        question_lower = question.lower()
        
        # كلمات دلالية للتصنيف
        if any(word in question_lower for word in ["ما هو", "ما هي", "عرّف", "تعريف"]):
            return "definition"
        elif any(word in question_lower for word in ["كيف", "طريقة", "خطوات"]):
            return "process"
        elif any(word in question_lower for word in ["لماذا", "لم", "سبب"]):
            return "reasoning"
        elif any(word in question_lower for word in ["متى", "تاريخ", "زمن"]):
            return "temporal"
        elif any(word in question_lower for word in ["أين", "مكان", "موقع"]):
            return "spatial"
        elif any(word in question_lower for word in ["من هو", "من هي", "شخص"]):
            return "person"
        elif any(word in question_lower for word in ["أي", "أفضل", "مقارنة"]):
            return "selection"
        elif any(word in question_lower for word in ["هل يمكن", "قدرة", "استطاعة"]):
            return "capability"
        elif any(word in question_lower for word in ["مستقبل", "ستكون", "سيحدث"]):
            return "future"
        elif any(word in question_lower for word in ["ربما", "احتمال", "ممكن"]):
            return "possibility"
        elif any(word in question_lower for word in ["ينصح", "أفضل", "توصية"]):
            return "recommendation"
        elif any(word in question_lower for word in ["لو", "إذا", "افتراض"]):
            return "hypothetical"
        elif any(word in question_lower for word in ["مقارنة", "أفضل من", "الفرق"]):
            return "comparative"
        elif any(word in question_lower for word in ["مثال", "توضيح", "مثل"]):
            return "exemplification"
        elif any(word in question_lower for word in ["رأي", "تعتقد", "نظر"]):
            return "opinion"
            
        # إذا لم يتم التعرف على نوع محدد، استخدم النوع العام
        return "general"
    
    def _extract_keywords(self, text):
        """استخراج الكلمات المفتاحية من النص"""
        # في التنفيذ الحقيقي، يمكن استخدام تقنيات NLP أكثر تقدماً
        # هذه طريقة مبسطة لاستخراج الكلمات المهمة
        
        # قائمة كلمات التوقف (stop words) العربية الشائعة
        stop_words = [
            "من", "إلى", "عن", "على", "في", "مع", "هذا", "هذه", "ذلك", "تلك",
            "هناك", "هنا", "أنا", "أنت", "هو", "هي", "نحن", "هم", "كان", "كانت",
            "يكون", "أن", "إن", "لا", "ما", "لم", "لن", "و", "أو", "ثم", "بل"
        ]
        
        # تنظيف النص وتقسيمه إلى كلمات
        words = re.findall(r'\w+', text.lower())
        
        # تصفية كلمات التوقف والكلمات القصيرة
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        # عد تكرار الكلمات
        word_counts = {}
        for word in keywords:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        # ترتيب الكلمات حسب التكرار
        sorted_keywords = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        
        # إرجاع الكلمات الأكثر تكراراً (بحد أقصى 5)
        return [word for word, count in sorted_keywords[:5]]
    
    def _generate_thinking_steps(self, question_type, question, answer, steps=3):
        """توليد خطوات تفكير منطقية"""
        # اختيار قالب التفكير المناسب
        template = random.choice(self.thinking_templates.get(question_type, self.thinking_templates["general"]))
        
        # استخراج الكلمات المفتاحية
        keywords = self._extract_keywords(question + " " + answer)
        
        # توليد خطوات التفكير
        thinking_steps = [template]
        
        # إنشاء أنماط المحادثة العشوائية باستخدام الكلمات المفتاحية
        patterns = random.sample(self.conversation_patterns, min(steps, len(self.conversation_patterns)))
        
        for i, pattern in enumerate(patterns):
            # إضافة بعض التنوع باستخدام الكلمات المفتاحية
            if keywords and random.random() > 0.5:
                keyword = random.choice(keywords)
                step = f"{pattern['response']} نلاحظ أهمية {keyword} في هذا السياق..."
            else:
                step = pattern['response']
            
            thinking_steps.append(step)
        
        return thinking_steps
    
    def think_deep(self, question, answer):
        """إجراء تفكير عميق ومنطقي حول السؤال والإجابة"""
        # تحليل نوع السؤال
        question_type = self._analyze_question_type(question)
        
        # توليد خطوات التفكير
        thinking_steps = self._generate_thinking_steps(question_type, question, answer)
        
        # محاكاة وقت التفكير (لأغراض العرض فقط)
        steps_with_delay = []
        for step in thinking_steps:
            # إضافة بعض التأخير المتغير لتقليد التفكير البشري
            delay_seconds = random.uniform(0.5, 1.0)
            steps_with_delay.append({"text": step, "delay_seconds": delay_seconds})
        
        # تسجيل عملية التفكير
        thinking_process = {
            "timestamp": __import__('datetime').datetime.now().isoformat(),
            "question": question,
            "question_type": question_type,
            "thinking_steps": thinking_steps,
            "answer": answer
        }
        
        self.thinking_log.append(thinking_process)
        
        return {
            "question_type": question_type,
            "thinking_steps": steps_with_delay,
            "answer": answer,
            "enhanced_answer": self._enhance_answer(question_type, answer)
        }
    
    def _enhance_answer(self, question_type, answer):
        """تحسين الإجابة بناءً على نوع السؤال"""
        # إضافة مقدمة مناسبة للإجابة
        introductions = {
            "definition": "يمكن تعريف هذا المفهوم كالتالي: ",
            "process": "تتضمن هذه العملية الخطوات التالية: ",
            "reasoning": "هناك عدة أسباب تفسر ذلك: ",
            "temporal": "من الناحية الزمنية: ",
            "spatial": "من الناحية المكانية: ",
            "person": "فيما يتعلق بهذه الشخصية: ",
            "selection": "عند المقارنة بين الخيارات: ",
            "capability": "من ناحية الإمكانيات والقدرات: ",
            "future": "بالنظر إلى المستقبل: ",
            "possibility": "من بين الاحتمالات المتاحة: ",
            "recommendation": "أفضل التوصيات في هذا السياق: ",
            "hypothetical": "في هذه الحالة الافتراضية: ",
            "comparative": "عند المقارنة: ",
            "exemplification": "على سبيل المثال: ",
            "opinion": "مع مراعاة وجهات النظر المختلفة: ",
            "general": ""
        }
        
        # الحصول على المقدمة المناسبة
        intro = introductions.get(question_type, "")
        
        # دمج المقدمة مع الإجابة
        if intro and not answer.startswith(intro):
            enhanced_answer = intro + answer
        else:
            enhanced_answer = answer
        
        return enhanced_answer
    
    def generate_follow_up_questions(self, question, answer, count=3):
        """توليد أسئلة متابعة ذات صلة"""
        # استخراج الكلمات المفتاحية
        keywords = self._extract_keywords(question + " " + answer)
        
        # قوالب لأسئلة المتابعة
        follow_up_templates = [
            "كيف يمكن تطبيق {keyword} في مجالات أخرى؟",
            "ما هي العلاقة بين {keyword} و{keyword2}؟",
            "ما هي التحديات التي تواجه {keyword}؟",
            "كيف تطور مفهوم {keyword} عبر الزمن؟",
            "ما هي الآثار المترتبة على {keyword}؟",
            "ما هي أهم الإنجازات في مجال {keyword}؟",
            "هل هناك بدائل لـ {keyword}؟",
            "ما رأيك في مستقبل {keyword}؟",
            "كيف يؤثر {keyword} على المجتمع؟",
            "ما هي أفضل الممارسات في مجال {keyword}؟"
        ]
        
        # توليد أسئلة المتابعة
        follow_up_questions = []
        if keywords:
            # اختيار عدد من القوالب بشكل عشوائي
            selected_templates = random.sample(follow_up_templates, min(count, len(follow_up_templates)))
            
            for template in selected_templates:
                # اختيار كلمة مفتاحية بشكل عشوائي
                keyword = random.choice(keywords)
                
                # إذا كان القالب يحتاج إلى كلمتين مفتاحيتين
                if "{keyword2}" in template:
                    # اختيار كلمة مفتاحية ثانية مختلفة
                    remaining_keywords = [k for k in keywords if k != keyword]
                    keyword2 = random.choice(remaining_keywords) if remaining_keywords else keyword
                    question = template.format(keyword=keyword, keyword2=keyword2)
                else:
                    question = template.format(keyword=keyword)
                
                follow_up_questions.append(question)
        
        return follow_up_questions
    
    def save_log(self, file_path="logs/thinking_log.json"):
        """حفظ سجل التفكير العميق"""
        # إنشاء المجلد إذا لم يكن موجوداً
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.thinking_log, f, ensure_ascii=False, indent=4)
        
        return {"message": f"تم حفظ سجل التفكير في {file_path}", "count": len(self.thinking_log)}

# وظيفة مساعدة للاستخدام في الواجهة الرئيسية
def apply_deep_thinking(question, answer):
    """تطبيق التفكير العميق على السؤال والإجابة"""
    thinking_engine = DeepThinking()
    result = thinking_engine.think_deep(question, answer)
    
    # إنشاء سلسلة مفصلة لعملية التفكير
    thinking_process = "\n".join([step["text"] for step in result["thinking_steps"]])
    
    # دمج عملية التفكير مع الإجابة المحسنة
    enhanced_response = f"{thinking_process}\n\n{result['enhanced_answer']}"
    
    # توليد أسئلة متابعة
    follow_ups = thinking_engine.generate_follow_up_questions(question, answer)
    
    return {
        "response": enhanced_response,
        "follow_up_questions": follow_ups,
        "question_type": result["question_type"]
    }

# تسجيل التفكير العميق في سجل محلي
def log_thinking(question, answer, thinking_result):
    """تسجيل عملية التفكير العميق"""
    log_entry = {
        "timestamp": __import__('datetime').datetime.now().isoformat(),
        "question": question,
        "answer": answer,
        "thinking_result": thinking_result
    }
    
    # تحميل السجل الحالي
    log_file = "logs/deep_thinking_log.json"
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            logs = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        logs = {"entries": []}
    
    # إضافة السجل الجديد
    logs["entries"].append(log_entry)
    
    # حفظ السجل
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(logs, f, ensure_ascii=False, indent=4)
    
    return True
