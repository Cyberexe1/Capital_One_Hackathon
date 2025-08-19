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
    Sarvam AI TTS passthrough.
    Expects JSON body: {"text": "...", "language": "hi-IN", "voice": "Anushka"}
    Returns: {"success": true, "audio_base64": "..."}
    """
    try:
        body = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"success": False, "error": "Invalid JSON body"}, status=400)

    text = (body.get("text") or "").strip()
    language = (body.get("language") or "en-IN").strip()
    voice = (body.get("voice") or body.get("model") or "Anushka").strip()
    if not text:
        return JsonResponse({"success": False, "error": "text is required"}, status=400)

    # Allow dev override via header/body; fallback to environment
    header_key = ''
    try:
        header_key = (request.headers.get('X-Sarvam-Key') or '').strip()
    except Exception:
        pass
    if not header_key:
        header_key = (request.META.get('HTTP_X_SARVAM_KEY') or '').strip()
    body_key = (body.get('api_key') or '').strip()
    api_key = (header_key or body_key or os.getenv("SARVAM_API_KEY", "")).strip()
    if not api_key:
        return JsonResponse({"success": False, "error": "SARVAM_API_KEY not configured"}, status=500)

    # Default to official Sarvam TTS endpoint per docs
    # https://docs.sarvam.ai/api-reference-docs/text-to-speech/convert
    sarvam_url = os.getenv("SARVAM_TTS_URL", "https://api.sarvam.ai/text-to-speech")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "X-API-Key": api_key,
        "X-Api-Key": api_key,
        "api-key": api_key,
        "apikey": api_key,
        "subscription-key": api_key,
        "Subscription-Key": api_key,
        "Ocp-Apim-Subscription-Key": api_key,
        "x-subscription-key": api_key,
        "X-Subscription-Key": api_key,
        "X-Subscription-Token": api_key,
    }
    # Official payload expects 'text' and 'target_language_code'.
    # Keep only documented fields to improve success rate.
    payload = {
        "text": text,
        "target_language_code": language,
    }

    try:
        # Try the configured URL first; then common variants derived from base host
        attempts = []
        candidate_urls = [sarvam_url]
        try:
            from urllib.parse import urlparse
            parsed = urlparse(sarvam_url)
            if parsed.scheme and parsed.netloc:
                base = f"{parsed.scheme}://{parsed.netloc}"
                for suffix in [
                    "/text-to-speech",
                    "/v1/tts",
                    "/tts",
                    "/v1/text-to-speech",
                    "/v1/speech/tts",
                    "/speech/tts",
                    "/v1/voice/tts",
                    "/voice/tts",
                    "/v1/audio/speech",
                    "/audio/speech",
                ]:
                    url_try = base + suffix
                    if url_try not in candidate_urls:
                        candidate_urls.append(url_try)
        except Exception:
            pass

        # Expand candidates by adding query-param API key variants
        def with_key_params(u: str):
            try:
                from urllib.parse import urlparse, urlencode, parse_qsl, urlunparse
                parsed = urlparse(u)
                q = dict(parse_qsl(parsed.query))
                urls = []
                for param in [
                    'subscription-key','api_key','apikey','api-key','x-api-key'
                ]:
                    q2 = q.copy()
                    q2[param] = api_key
                    new_q = urlencode(q2)
                    urls.append(urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_q, parsed.fragment)))
                return urls
            except Exception:
                return []

        expanded = []
        seen = set()
        for u in candidate_urls:
            if u not in seen:
                expanded.append(u); seen.add(u)
            for u2 in with_key_params(u):
                if u2 not in seen:
                    expanded.append(u2); seen.add(u2)

        # Define distinct header sets to try to satisfy provider's required header name
        header_sets = [
            ("api-subscription-key", {"Content-Type": "application/json", "api-subscription-key": api_key}),
            ("x-api-key", {"Content-Type": "application/json", "x-api-key": api_key}),
            ("api-key", {"Content-Type": "application/json", "api-key": api_key}),
            ("Ocp-Apim-Subscription-Key", {"Content-Type": "application/json", "Ocp-Apim-Subscription-Key": api_key}),
            ("Authorization-Bearer", {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}),
            ("Authorization-Raw", {"Content-Type": "application/json", "Authorization": api_key}),
        ]

        last_resp = None
        for url_try in expanded:
            try:
                for hdr_name, hdrs in header_sets:
                    # Merge any extra headers such as multiple subscription headers if needed later
                    try:
                        merged_headers = hdrs
                        resp = requests.post(url_try, headers=merged_headers, json=payload, timeout=30)
                        last_resp = resp
                        if resp.status_code == 200:
                            ct = resp.headers.get("content-type", "")
                            data = resp.json() if ct.startswith("application/json") else {}
                            # Official response contains 'audios': [ base64, ... ]
                            audio_base64 = data.get("audio_base64") or data.get("audio")
                            if (not audio_base64) and isinstance(data.get("audios"), list) and data["audios"]:
                                audio_base64 = data["audios"][0]
                            if not audio_base64:
                                body_snippet = resp.text[:500] if hasattr(resp, 'text') else ''
                                return JsonResponse({
                                    "success": False,
                                    "error": "No audio returned from Sarvam",
                                    "provider_body": body_snippet,
                                    "content_type": ct,
                                    "endpoint": url_try,
                                    "header_set": hdr_name,
                                }, status=502)
                            return JsonResponse({"success": True, "audio_base64": audio_base64})
                        elif resp.status_code == 404:
                            attempts.append({
                                "endpoint": url_try,
                                "status": 404,
                                "header_set": hdr_name,
                                "body": (resp.text[:300] if hasattr(resp, 'text') else '')
                            })
                            # 404 indicates wrong path; no need to try other header sets for this URL
                            break
                        else:
                            attempts.append({
                                "endpoint": url_try,
                                "status": resp.status_code,
                                "header_set": hdr_name,
                                "body": (resp.text[:300] if hasattr(resp, 'text') else '')
                            })
                            # Try next header set for same URL
                            continue
                    except requests.Timeout:
                        return JsonResponse({"success": False, "error": "Sarvam API timeout", "endpoint": url_try, "header_set": hdr_name}, status=504)
                    except Exception as e_inner:
                        attempts.append({"endpoint": url_try, "header_set": hdr_name, "exception": str(e_inner)})
                        continue
                # Move to next URL
                continue
            except requests.Timeout:
                return JsonResponse({"success": False, "error": "Sarvam API timeout", "endpoint": url_try}, status=504)
            except Exception as e:
                # Continue to next candidate on connection errors
                attempts.append({"endpoint": url_try, "exception": str(e)})
                continue

        # If we get here, all attempts failed (likely 404 variants)
        return JsonResponse({
            "success": False,
            "error": "Sarvam API not found at any known endpoint",
            "attempts": attempts,
        }, status=502)
    except requests.Timeout:
        return JsonResponse({"success": False, "error": "Sarvam API timeout"}, status=504)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=502)