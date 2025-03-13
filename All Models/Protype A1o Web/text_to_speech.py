
import requests
import tempfile
import os
import base64
from pathlib import Path

ELEVEN_LABS_API_KEY = "sk_cbd39322bde98a014726dcd9a61545d542fb283137bcc9a5"

def text_to_speech(text, voice_id="21m00Tcm4TlvDq8ikWAM", model_id="eleven_monolingual_v1"):
    """
    Convert text to speech using Eleven Labs API
    Returns base64 encoded audio
    
    Voice IDs:
    - 21m00Tcm4TlvDq8ikWAM - Default for Arabic
    - pNInz6obpgDQGcFmaJgB - Adam (male)
    - EXAVITQu4vr4xnSDxMaL - Rachel (female)
    """
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVEN_LABS_API_KEY
    }
    
    # Check if text is arabic and adjust settings if needed
    is_arabic = any('\u0600' <= c <= '\u06FF' for c in text)
    
    # Optimize voice settings for language
    stability = 0.6 if is_arabic else 0.5
    similarity_boost = 0.7 if is_arabic else 0.5
    
    data = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {
            "stability": stability,
            "similarity_boost": similarity_boost
        }
    }
    
    try:
        print(f"Sending TTS request for text: {text[:50]}...")
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        
        # Convert audio to base64 for web embedding
        audio_base64 = base64.b64encode(response.content).decode('utf-8')
        print("Successfully generated audio")
        return audio_base64
    except Exception as e:
        print(f"Error generating speech: {e}")
        return None

def get_available_voices():
    """Get available voices from Eleven Labs"""
    url = "https://api.elevenlabs.io/v1/voices"
    
    headers = {
        "Accept": "application/json",
        "xi-api-key": ELEVEN_LABS_API_KEY
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching voices: {e}")
        return {"voices": []}
