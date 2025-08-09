from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import requests
import os
from django.conf import settings



def index(request):
    return render(request, 'index.html')

@csrf_exempt
@require_http_methods(["POST"])
def process_speech(request):
    """
    Process speech-to-text, translation, and chatbot response
    """
    try:
        data = json.loads(request.body)
        spoken_text = data.get('spoken_text', '')
        language = data.get('language', 'en-US')
        
        if not spoken_text:
            return JsonResponse({
                'success': False,
                'error': 'No speech text provided'
            })
        
        # Step 1: Translate to English if not already in English
        english_text = spoken_text
        if language != 'en-US':
            english_text = translate_to_english(spoken_text, language)
        
        # Step 2: Send to chatbot
        chatbot_response = send_to_chatbot(english_text)
        
        # Step 3: Translate response back to original language if needed
        final_response = chatbot_response
        if language != 'en-US':
            final_response = translate_to_language(chatbot_response, language)
        
        return JsonResponse({
            'success': True,
            'original_text': spoken_text,
            'english_text': english_text,
            'chatbot_response': final_response,
            'detected_language': language
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

def translate_to_english(text, source_language):
    """
    Translate text to English using LibreTranslate
    """
    try:
        # LibreTranslate public instance
        url = "https://libretranslate.de/translate"
        
        # Map language codes to LibreTranslate format
        language_map = {
            'hi-IN': 'hi',  # Hindi
            'bn-IN': 'bn',  # Bengali
            'te-IN': 'te',  # Telugu
            'mr-IN': 'mr',  # Marathi
            'ta-IN': 'ta',  # Tamil
            'gu-IN': 'gu',  # Gujarati
            'kn-IN': 'kn',  # Kannada
            'ml-IN': 'ml',  # Malayalam
            'pa-IN': 'pa',  # Punjabi
            'ur-IN': 'ur',  # Urdu
            'en-US': 'en',
            'en-IN': 'en'
        }
        
        source_lang = language_map.get(source_language, 'auto')
        
        payload = {
            "q": text,
            "source": source_lang,
            "target": "en",
            "format": "text"
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        return result.get('translatedText', text)
        
    except Exception as e:
        print(f"Translation error: {e}")
        # Fallback: return original text
        return text

def translate_to_language(text, target_language):
    """
    Translate English text to target language using LibreTranslate
    """
    try:
        # LibreTranslate public instance
        url = "https://libretranslate.de/translate"
        
        # Map language codes to LibreTranslate format
        language_map = {
            'hi-IN': 'hi',  # Hindi
            'bn-IN': 'bn',  # Bengali
            'te-IN': 'te',  # Telugu
            'mr-IN': 'mr',  # Marathi
            'ta-IN': 'ta',  # Tamil
            'gu-IN': 'gu',  # Gujarati
            'kn-IN': 'kn',  # Kannada
            'ml-IN': 'ml',  # Malayalam
            'pa-IN': 'pa',  # Punjabi
            'ur-IN': 'ur',  # Urdu
            'en-US': 'en',
            'en-IN': 'en'
        }
        
        target_lang = language_map.get(target_language, 'en')
        
        payload = {
            "q": text,
            "source": "en",
            "target": target_lang,
            "format": "text"
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        return result.get('translatedText', text)
        
    except Exception as e:
        print(f"Translation error: {e}")
        # Fallback: return original text
        return text

def send_to_chatbot(text):
    return f"I received your message: '{text}'. The AI chatbot functionality is currently disabled."

@csrf_exempt
@require_http_methods(["POST"])
def text_to_speech(request):
    """
    Text-to-speech endpoint (handled on frontend)
    """
    try:
        data = json.loads(request.body)
        text = data.get('text', '')
        language = data.get('language', 'en-US')
        
        return JsonResponse({
            'success': True,
            'text': text,
            'language': language
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })