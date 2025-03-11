
import os
import time
import base64
import requests
import numpy as np
import io
from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel
import google.generativeai as genai

# Configure Gemini API
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', "AIzaSyBUDUURqkN5Lvid5P8V0ZXIRpseKC7ffMU")
genai.configure(api_key=GEMINI_API_KEY)

class MultimodalIntelligence:
    def __init__(self):
        # State tracking
        self.clip_model = None
        self.clip_processor = None
        self.gemini_vision_model = None
        self.model_initialized = False
        self.initialize_models()
    
    def initialize_models(self):
        """Initialize multimodal AI models"""
        try:
            print("Initializing multimodal models...")
            
            # Initialize Gemini Pro Vision Model for image analysis
            generation_config = {
                "temperature": 0.4,
                "top_p": 0.95,
                "top_k": 32,
                "max_output_tokens": 4096,
            }
            
            self.gemini_vision_model = genai.GenerativeModel(
                model_name="gemini-1.5-pro-vision",
                generation_config=generation_config,
            )
            
            # Initialize CLIP for image understanding and concept matching
            self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            
            # Move to GPU if available
            if torch.cuda.is_available():
                self.clip_model = self.clip_model.to("cuda")
            
            self.model_initialized = True
            print("Multimodal models initialized successfully")
        except Exception as e:
            print(f"Error initializing multimodal models: {e}")
            self.model_initialized = False
    
    def analyze_image(self, image_data, query=None):
        """Analyze image content using Gemini Vision"""
        if not self.model_initialized:
            return {"error": "Models not initialized"}
        
        try:
            # Process image data (accepts base64, PIL Image, or file path)
            if isinstance(image_data, str):
                if image_data.startswith('data:image'):
                    # Handle base64 data URL
                    image_data = image_data.split(',')[1]
                    image = Image.open(io.BytesIO(base64.b64decode(image_data)))
                elif os.path.exists(image_data):
                    # Handle file path
                    image = Image.open(image_data)
                else:
                    # Assume it's base64
                    image = Image.open(io.BytesIO(base64.b64decode(image_data)))
            elif isinstance(image_data, Image.Image):
                image = image_data
            else:
                return {"error": "Unsupported image format"}
            
            # Prepare prompt based on query
            if query:
                prompt = f"Analyze this image and answer the following question: {query}"
            else:
                prompt = "Describe this image in detail. Identify key objects, people, text, and context."
            
            # Generate response with Gemini Vision
            response = self.gemini_vision_model.generate_content([prompt, image])
            
            # Extract concepts from image
            concepts = self.extract_image_concepts(image)
            
            return {
                "description": response.text,
                "concepts": concepts
            }
        except Exception as e:
            print(f"Error analyzing image: {e}")
            return {"error": str(e)}
    
    def extract_image_concepts(self, image, top_k=5):
        """Extract key concepts from an image using CLIP"""
        if not self.model_initialized:
            return []
        
        try:
            # Define potential concepts to check against
            concepts = [
                "person", "building", "car", "animal", "food", "landscape", 
                "technology", "art", "text", "nature", "indoor", "outdoor",
                "daytime", "nighttime", "water", "plant", "furniture", "clothing",
                "face", "group of people", "vehicle", "sign", "electronic device"
            ]
            
            # Process image and concept texts
            inputs = self.clip_processor(
                text=concepts,
                images=image,
                return_tensors="pt",
                padding=True
            )
            
            # Move to GPU if available
            if torch.cuda.is_available():
                inputs = {k: v.to("cuda") for k, v in inputs.items()}
            
            # Get similarity scores
            with torch.no_grad():
                outputs = self.clip_model(**inputs)
                logits_per_image = outputs.logits_per_image
                probs = logits_per_image.softmax(dim=1)
            
            # Get top concepts
            values, indices = probs[0].topk(top_k)
            
            # Convert to CPU for processing
            if torch.cuda.is_available():
                values = values.cpu()
                indices = indices.cpu()
            
            # Format results
            top_concepts = [
                {"concept": concepts[idx], "confidence": float(val)}
                for val, idx in zip(values, indices)
            ]
            
            return top_concepts
        except Exception as e:
            print(f"Error extracting image concepts: {e}")
            return []
    
    def text_to_speech(self, text, voice_id=None):
        """Convert text to speech using ElevenLabs API"""
        try:
            # Import text_to_speech module
            from attached_assets.text_to_speech import text_to_speech as tts
            
            # Use default voice if not specified
            if voice_id is None:
                voice_id = '21m00Tcm4TlvDq8ikWAM'  # Default ElevenLabs voice
            
            # Convert text to speech
            audio_data = tts(text, voice_id)
            
            return {
                "success": True,
                "audio_data": audio_data
            }
        except Exception as e:
            print(f"Error generating speech: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def speech_to_text(self, audio_data):
        """Convert speech to text using Whisper API"""
        try:
            # Whisper API endpoint
            api_url = "https://api.openai.com/v1/audio/transcriptions"
            
            # Get API key from environment
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                return {"error": "OpenAI API key not found in environment variables"}
            
            # Prepare headers
            headers = {
                "Authorization": f"Bearer {api_key}"
            }
            
            # Prepare files data
            if isinstance(audio_data, str) and os.path.exists(audio_data):
                # If audio_data is a file path
                files = {
                    "file": open(audio_data, "rb"),
                    "model": (None, "whisper-1")
                }
            else:
                # If audio_data is already bytes
                files = {
                    "file": ("audio.mp3", audio_data),
                    "model": (None, "whisper-1")
                }
            
            # Send request
            response = requests.post(api_url, headers=headers, files=files)
            response.raise_for_status()
            
            # Parse response
            result = response.json()
            
            return {
                "success": True,
                "text": result.get("text", "")
            }
        except Exception as e:
            print(f"Error transcribing speech: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def process_multimodal_input(self, text_input=None, image_input=None, audio_input=None):
        """Process a combined multimodal input with text, image, and/or audio"""
        result = {"success": True}
        
        try:
            # Process audio input (if provided)
            if audio_input:
                audio_result = self.speech_to_text(audio_input)
                if audio_result.get("success", False):
                    result["speech_text"] = audio_result["text"]
                    
                    # Combine with text input if provided
                    if text_input:
                        text_input = f"{text_input} {audio_result['text']}"
                    else:
                        text_input = audio_result["text"]
                else:
                    result["audio_error"] = audio_result.get("error", "Unknown audio processing error")
            
            # Process image input (if provided)
            if image_input:
                image_result = self.analyze_image(image_input, query=text_input)
                result["image_analysis"] = image_result
            
            # Generate comprehensive response
            if text_input or "speech_text" in result:
                # Use Gemini to generate response based on all inputs
                prompt = text_input or result.get("speech_text", "Describe what you see")
                
                if "image_analysis" in result:
                    concepts = ", ".join([c["concept"] for c in result["image_analysis"].get("concepts", [])])
                    image_desc = result["image_analysis"].get("description", "")
                    
                    combined_prompt = f"""
                    User query: {prompt}
                    
                    Image analysis:
                    {image_desc}
                    
                    Detected concepts: {concepts}
                    
                    Please provide a comprehensive response addressing the user's query in light of the image content.
                    """
                else:
                    combined_prompt = prompt
                
                # Generate response with Gemini
                gemini_model = genai.GenerativeModel("gemini-1.5-pro")
                response = gemini_model.generate_content(combined_prompt)
                
                result["response"] = response.text
            
            return result
        except Exception as e:
            print(f"Error processing multimodal input: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Create singleton instance
multimodal_intelligence = MultimodalIntelligence()
