
import os
import json
import time
import google.generativeai as genai
import random

# Configure Gemini API
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', "AIzaSyBUDUURqkN5Lvid5P8V0ZXIRpseKC7ffMU")
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini model
generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 4096,
    "response_mime_type": "text/plain",
}

gemini_model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    generation_config=generation_config,
)

critic_chat = gemini_model.start_chat(history=[])

class SelfReflection:
    def __init__(self):
        self.reasoning_records = []
        self.max_records = 100  # Maximum reasoning records to store
        self.load_records()
        
    def load_records(self):
        """Load existing reasoning records if available"""
        try:
            with open('reasoning_records.json', 'r') as f:
                data = json.load(f)
                self.reasoning_records = data.get('records', [])
                print(f"Loaded {len(self.reasoning_records)} reasoning records")
        except (FileNotFoundError, json.JSONDecodeError):
            self.reasoning_records = []
            
    def save_records(self):
        """Save reasoning records to file"""
        try:
            with open('reasoning_records.json', 'w') as f:
                json.dump({'records': self.reasoning_records}, f, indent=2)
        except Exception as e:
            print(f"Error saving reasoning records: {e}")
    
    def evaluate_inference(self, source, target, relation, confidence):
        """Evaluate whether an inferred relationship is valid using self-reflection"""
        # Format the inference as a statement
        inference_statement = f"Entity '{source}' is related to entity '{target}' with relation type '{relation}' (confidence: {confidence:.2f})."
        
        # Use Chain of Thought reasoning to evaluate the inference
        prompt = f"""
As a critical thinking AI, please evaluate whether the following inference is likely to be correct:

INFERENCE: {inference_statement}

Please use Chain of Thought reasoning:
1. First, think about what you know about both entities.
2. Consider whether this type of relationship makes sense between these entities.
3. Look for potential logical errors or fallacies.
4. Provide reasons why this inference might be correct or incorrect.
5. Finally, provide your judgment on whether this inference is [VALID] or [INVALID].

Your response should follow this format:
REASONING: [Your step-by-step reasoning about the inference]
JUDGMENT: [VALID/INVALID]
CONFIDENCE: [A number between 0 and 1]
        """
        
        try:
            # Get model response
            response = critic_chat.send_message(prompt)
            response_text = response.text
            
            # Parse the response
            reasoning = None
            judgment = None
            eval_confidence = None
            
            for line in response_text.split('\n'):
                if line.startswith('REASONING:'):
                    reasoning = line[len('REASONING:'):].strip()
                elif line.startswith('JUDGMENT:'):
                    judgment = line[len('JUDGMENT:'):].strip()
                elif line.startswith('CONFIDENCE:'):
                    try:
                        eval_confidence = float(line[len('CONFIDENCE:'):].strip())
                    except ValueError:
                        eval_confidence = 0.5
            
            # Default values if parsing failed
            if reasoning is None:
                reasoning = response_text
            if judgment is None:
                judgment = "INVALID"
            if eval_confidence is None:
                eval_confidence = 0.5
                
            # Store the reasoning record
            record = {
                'timestamp': time.time(),
                'source': source,
                'target': target,
                'relation': relation,
                'original_confidence': confidence,
                'reasoning': reasoning,
                'judgment': judgment,
                'evaluation_confidence': eval_confidence
            }
            
            self.reasoning_records.append(record)
            
            # Trim records if exceeding maximum
            if len(self.reasoning_records) > self.max_records:
                self.reasoning_records = self.reasoning_records[-self.max_records:]
                
            # Save records
            self.save_records()
            
            # Return evaluation results
            is_valid = judgment == "VALID"
            adjusted_confidence = confidence * eval_confidence if is_valid else confidence * (1 - eval_confidence)
            
            return {
                'is_valid': is_valid,
                'adjusted_confidence': adjusted_confidence,
                'reasoning': reasoning,
                'judgment': judgment,
                'eval_confidence': eval_confidence
            }
            
        except Exception as e:
            print(f"Error during self-reflection: {e}")
            # Default fallback response
            return {
                'is_valid': confidence > 0.8,  # Default to original confidence
                'adjusted_confidence': confidence,
                'reasoning': f"Error in evaluation: {e}",
                'judgment': "UNCERTAIN",
                'eval_confidence': 0.5
            }
    
    def verify_answer(self, question, answer):
        """Verify if an answer is correct using self-reflection"""
        # Use Chain of Thought reasoning to verify the answer
        prompt = f"""
As a critical fact-checking AI, please evaluate whether the following answer to the question is likely to be correct:

QUESTION: {question}
ANSWER: {answer}

Please use Chain of Thought reasoning:
1. Break down the question to understand what is being asked.
2. Analyze the provided answer for factual accuracy.
3. Consider what you know about the topic.
4. Look for potential errors, misconceptions, or incomplete information.
5. Finally, provide your judgment on whether this answer is [CORRECT], [PARTIALLY CORRECT], or [INCORRECT].

Your response should follow this format:
REASONING: [Your step-by-step reasoning about the answer]
JUDGMENT: [CORRECT/PARTIALLY CORRECT/INCORRECT]
CONFIDENCE: [A number between 0 and 1]
IMPROVEMENT: [Suggestion for improving the answer, if needed]
        """
        
        try:
            # Get model response
            response = critic_chat.send_message(prompt)
            response_text = response.text
            
            # Parse the response
            reasoning = None
            judgment = None
            eval_confidence = None
            improvement = None
            
            for line in response_text.split('\n'):
                if line.startswith('REASONING:'):
                    reasoning = line[len('REASONING:'):].strip()
                elif line.startswith('JUDGMENT:'):
                    judgment = line[len('JUDGMENT:'):].strip()
                elif line.startswith('CONFIDENCE:'):
                    try:
                        eval_confidence = float(line[len('CONFIDENCE:'):].strip())
                    except ValueError:
                        eval_confidence = 0.7
                elif line.startswith('IMPROVEMENT:'):
                    improvement = line[len('IMPROVEMENT:'):].strip()
            
            # Default values if parsing failed
            if reasoning is None:
                reasoning = response_text
            if judgment is None:
                judgment = "PARTIALLY CORRECT"
            if eval_confidence is None:
                eval_confidence = 0.7
            if improvement is None:
                improvement = "No specific improvements suggested."
                
            # Return evaluation results
            return {
                'is_correct': judgment == "CORRECT",
                'is_partially_correct': judgment == "PARTIALLY CORRECT",
                'reasoning': reasoning,
                'judgment': judgment,
                'confidence': eval_confidence,
                'improvement': improvement
            }
            
        except Exception as e:
            print(f"Error during answer verification: {e}")
            # Default fallback response
            return {
                'is_correct': True,  # Default to assuming correct
                'is_partially_correct': False,
                'reasoning': f"Error in evaluation: {e}",
                'judgment': "UNCERTAIN",
                'confidence': 0.5,
                'improvement': "Could not evaluate the answer due to an error."
            }
    
    def generate_critical_questions(self, topic, count=3):
        """Generate critical thinking questions about a topic"""
        prompt = f"""
Generate {count} critical thinking questions about the topic "{topic}" that would encourage deep analytical reasoning.
The questions should:
1. Challenge assumptions
2. Require evaluation of evidence
3. Promote consideration of multiple perspectives
4. Avoid simple yes/no answers

Format your response as a numbered list.
        """
        
        try:
            response = critic_chat.send_message(prompt)
            
            # Extract questions
            questions = []
            lines = response.text.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if line and (line[0].isdigit() and line[1] in ['.', ')', ':']):
                    question = line[2:].strip() if line[1] in [')', ':'] else line[3:].strip()
                    questions.append(question)
                elif line and line.startswith('-'):
                    question = line[1:].strip()
                    questions.append(question)
            
            # If parsing failed, fall back to splitting by newlines
            if not questions:
                questions = [line.strip() for line in lines if line.strip()]
                
            return questions[:count]  # Limit to requested count
        except Exception as e:
            print(f"Error generating critical questions: {e}")
            # Fallback questions
            fallback_questions = [
                f"What are the most compelling arguments for and against {topic}?",
                f"How might our understanding of {topic} change in the next decade?",
                f"What assumptions underlie common beliefs about {topic}?"
            ]
            return random.sample(fallback_questions, min(count, len(fallback_questions)))

# Create singleton instance
self_reflection = SelfReflection()
