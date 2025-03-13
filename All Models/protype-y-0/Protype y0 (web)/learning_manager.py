
import threading
import time
import random
import json
import os
from datetime import datetime

# Import database functions
from database import save_data, load_data, get_knowledge_by_source

# Import learning functions from celery_tasks
from celery_tasks import learn_from_wikipedia, learn_from_gemini_flash

class LearningManager:
    """مدير للتعلم المستمر في الخلفية"""
    
    def __init__(self):
        """تهيئة مدير التعلم"""
        self.is_learning = False
        self.learning_thread = None
        self.topics = [
            "Artificial_intelligence", "Machine_learning", "Deep_learning",
            "Natural_language_processing", "Computer_vision", "Robotics",
            "Quantum_computing", "Blockchain", "Cryptocurrency", "Big_data",
            "Cloud_computing", "Internet_of_Things", "Augmented_reality",
            "Virtual_reality", "5G_technology", "Autonomous_vehicles",
            "Renewable_energy", "Space_exploration", "Biotechnology",
            "Nanotechnology", "Genetics", "Climate_change", "Sustainability"
        ]
        self.questions = [
            "What is the theory of relativity?",
            "How does quantum entanglement work?",
            "Why is biodiversity important?",
            "What are black holes?",
            "How does the human brain store memories?",
            "What causes climate change?",
            "How do vaccines work?",
            "What is the blockchain technology?",
            "How do neural networks learn?",
            "What is the future of artificial intelligence?"
        ]
        self.log_path = "learning_logs.json"
        self.load_logs()
    
    def load_logs(self):
        """تحميل سجلات التعلم"""
        try:
            if os.path.exists(self.log_path):
                with open(self.log_path, 'r') as f:
                    self.logs = json.load(f)
            else:
                self.logs = {"logs": []}
        except (json.JSONDecodeError, Exception) as e:
            print(f"خطأ في تحميل سجلات التعلم: {e}")
            self.logs = {"logs": []}
    
    def save_logs(self):
        """حفظ سجلات التعلم"""
        try:
            with open(self.log_path, 'w') as f:
                json.dump(self.logs, f, indent=2)
        except Exception as e:
            print(f"خطأ في حفظ سجلات التعلم: {e}")
    
    def log_action(self, action, details=None):
        """تسجيل إجراء تعلم"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action
        }
        if details:
            log_entry["details"] = details
        
        self.logs["logs"].append(log_entry)
        self.save_logs()
    
    def add_custom_knowledge(self, question, answer, source="user_taught"):
        """إضافة معرفة مخصصة إلى النظام"""
        success = save_data(question, answer, 0.8, source, "learning_manager")
        if success:
            self.log_action("custom_knowledge_added", {
                "question": question,
                "source": source
            })
            return True
        return False
    
    def add_topic(self, topic):
        """إضافة موضوع جديد لقائمة المواضيع"""
        if topic not in self.topics:
            self.topics.append(topic)
            self.log_action("topic_added", {"topic": topic})
            return True
        return False
    
    def add_question(self, question):
        """إضافة سؤال جديد لقائمة الأسئلة"""
        if question not in self.questions:
            self.questions.append(question)
            self.log_action("question_added", {"question": question})
            return True
        return False
    
    def start_learning(self):
        """بدء عملية التعلم المستمر"""
        if self.is_learning:
            print("التعلم المستمر قيد التشغيل بالفعل!")
            return False
        
        self.is_learning = True
        self.learning_thread = threading.Thread(target=self._learn_continuously, daemon=True)
        self.learning_thread.start()
        self.log_action("learning_started", {"mode": "continuous"})
        print("تم بدء التعلم المستمر!")
        return True
    
    def stop_learning(self):
        """إيقاف عملية التعلم المستمر"""
        if not self.is_learning:
            print("التعلم المستمر غير نشط!")
            return False
        
        self.is_learning = False
        # انتظار إنهاء الخيط (بحد أقصى 5 ثوانٍ)
        if self.learning_thread and self.learning_thread.is_alive():
            self.learning_thread.join(timeout=5)
        
        self.log_action("learning_stopped")
        print("تم إيقاف التعلم المستمر!")
        return True
    
    def _learn_continuously(self):
        """عملية التعلم المستمر الداخلية"""
        while self.is_learning:
            try:
                # اختيار عشوائي للتعلم من ويكيبيديا أو Gemini
                if random.random() < 0.6:  # 60% فرصة للتعلم من ويكيبيديا
                    topic = random.choice(self.topics)
                    print(f"التعلم عن: {topic} من ويكيبيديا...")
                    result = learn_from_wikipedia(topic)
                    
                    if result and result.get("status") == "نجاح":
                        print(f"تم التعلم بنجاح عن: {topic}")
                        self.log_action("wikipedia_learning", {
                            "topic": topic,
                            "question": result.get("question", "غير معروف")
                        })
                    else:
                        print(f"فشل التعلم عن: {topic}")
                        self.log_action("learning_error", {
                            "source": "wikipedia",
                            "topic": topic,
                            "reason": result.get("reason", "سبب غير معروف")
                        })
                else:
                    # التعلم من Gemini
                    question = random.choice(self.questions)
                    print(f"التعلم عن: {question} من Gemini...")
                    result = learn_from_gemini_flash(question)
                    
                    if result and result.get("status") == "نجاح":
                        print(f"تم التعلم بنجاح عن: {question}")
                        self.log_action("gemini_learning", {
                            "question": question,
                            "answer_snippet": result.get("answer_snippet", "غير متوفر")
                        })
                    else:
                        print(f"فشل التعلم عن: {question}")
                        self.log_action("learning_error", {
                            "source": "gemini",
                            "question": question,
                            "reason": result.get("reason", "سبب غير معروف")
                        })
                
                # انتظار قبل الدورة التالية (بين 30 و60 ثانية)
                wait_time = random.randint(30, 60)
                print(f"انتظار {wait_time} ثانية قبل الموضوع التالي...")
                
                # انتظار مع التحقق الدوري من الإيقاف
                for _ in range(wait_time):
                    if not self.is_learning:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                print(f"خطأ في دورة التعلم المستمر: {e}")
                self.log_action("learning_cycle_error", {"error": str(e)})
                # انتظار قبل المحاولة مرة أخرى
                time.sleep(10)

# إنشاء كائن مفرد (singleton) لمدير التعلم
learning_manager = LearningManager()

# تصدير للاستخدام من قبل التطبيق
if __name__ == "__main__":
    # عند التشغيل المباشر، بدء التعلم التلقائي
    print("بدء مدير التعلم...")
    learning_manager.start_learning()
    
    try:
        # إبقاء البرنامج قيد التشغيل
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("إيقاف التعلم المستمر...")
        learning_manager.stop_learning()
