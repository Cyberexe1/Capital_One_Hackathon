from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
import json
import os
import requests
import re


@require_GET
def price_prediction_view(request):
    # Lazy import to avoid importing heavy deps at startup
    from commodity_price import predict_price
    commodity_raw = request.GET.get("commodity", "")
    commodity = _normalize_commodity_param(commodity_raw)
    market = request.GET.get("market") or "Varanasi"
    if not commodity.strip():
        return JsonResponse({"ok": False, "error": "commodity is required"}, status=400)
    result = predict_price(commodity, market)
    status = 200 if result.get("ok") else 400
    return JsonResponse(result, status=status)


@require_GET
def price_all_view(request):
    # Lazy import
    from commodity_price import predict_all_prices
    market = request.GET.get("market") or "Varanasi"
    q = (request.GET.get("q") or "").strip()
    result = predict_all_prices(market)
    if result.get("ok") and q:
        items = result.get("items") or []
        best = _filter_items_by_query(items, q)
        if best is not None:
            result = {"ok": True, "count": 1, "items": [best], "resolved_query": q}
        else:
            result = {"ok": False, "error": f"Commodity not found: {q}", "available": [it.get("commodity") for it in items]}
    status = 200 if result.get("ok") else 400
    return JsonResponse(result, status=status)


@require_GET
def advisory_view(request):
    # Lazy import to avoid importing heavy deps at startup
    from smart_farming import get_advisory
    city = request.GET.get("city")
    ph_raw = request.GET.get("ph")
    try:
        ph = float(ph_raw) if ph_raw is not None else None
    except ValueError:
        return JsonResponse({"ok": False, "error": "Invalid ph"}, status=400)

    if ph is None:
        return JsonResponse({"ok": False, "error": "ph is required"}, status=400)

    result = get_advisory(city, ph)
    status = 200 if result.get("ok") else 400
    return JsonResponse(result, status=status)


@csrf_exempt
@require_POST
def text_to_speech_view(request):
    """
    Sarvam AI TTS passthrough.
    Expects JSON body: {"text": "...", "language": "hi-IN"}
    Returns: {"success": true, "audio_base64": "..."}
    """
    try:
        body = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"success": False, "error": "Invalid JSON body"}, status=400)

    text = (body.get("text") or "").strip()
    language = (body.get("language") or "en-IN").strip()
    # Support selecting Sarvam voice/model; default to 'Anushka' per request
    voice = (body.get("voice") or body.get("model") or "Anushka").strip()
    if not text:
        return JsonResponse({"success": False, "error": "text is required"}, status=400)

    api_key = os.getenv("SARVAM_API_KEY")
    if not api_key:
        return JsonResponse({"success": False, "error": "SARVAM_API_KEY not configured"}, status=500)

    # NOTE: Adjust endpoint and payload as per Sarvam AI's latest API.
    # This is a generic passthrough that forwards text+language and expects base64 audio.
    sarvam_url = os.getenv("SARVAM_TTS_URL", "https://api.sarvam.ai/tts")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "language": language,
        # Many providers accept either 'voice' or 'model' to select speaker
        "voice": voice,
        "model": voice,
        # You may add: 'format': 'mp3', 'speed': 1.0, etc., if supported by API
    }

    try:
        resp = requests.post(sarvam_url, headers=headers, json=payload, timeout=30)
        if resp.status_code != 200:
            return JsonResponse({"success": False, "error": f"Sarvam API error: {resp.status_code}"}, status=502)
        data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        audio_base64 = data.get("audio_base64") or data.get("audio")
        if not audio_base64:
            return JsonResponse({"success": False, "error": "No audio returned from Sarvam"}, status=502)
        return JsonResponse({"success": True, "audio_base64": audio_base64})
    except requests.Timeout:
        return JsonResponse({"success": False, "error": "Sarvam API timeout"}, status=504)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=502)


@csrf_exempt
@require_POST
def process_speech_view(request):
    """
    Pipeline:
    1) Take user text + language
    2) Translate to English (best effort)
    3) Detect intent (commodity price) on English text
    4) Produce answer (call predict_price)
    5) Translate answer back to user's language (best effort)

    Body: {"spoken_text": "...", "language": "hi-IN"}
    Returns: {"success": true, "chatbot_response": "...", "detected_language": "hi-IN"}
    """
    try:
        body = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"success": False, "error": "Invalid JSON body"}, status=400)

    text = (body.get("spoken_text") or "").strip()
    user_lang = (body.get("language") or "en-US").strip()
    if not text:
        return JsonResponse({"success": False, "error": "spoken_text is required"}, status=400)

    # 1-2) Translate inbound to English (best-effort)
    english_text = _translate_text(text, src_lang=_short_lang(user_lang), tgt_lang="en") or text

    # 3) Detect commodity price intent (English first)
    intent = _detect_price_intent_en(english_text)
    if intent:
        commodity = intent.get("commodity")
        market = intent.get("market") or (request.GET.get("market") or "Varanasi")
        from commodity_price import predict_price
        result = predict_price(commodity, market)
        if not result.get("ok"):
            return JsonResponse({"success": False, "error": result.get("error", "prediction failed")}, status=400)

        # 4) Compose English answer
        answer_en = _format_price_answer_en(result)
        # 5) Translate back to user's language if not English
        out_lang = _short_lang(user_lang)
        final_text = _translate_text(answer_en, src_lang="en", tgt_lang=out_lang) if out_lang != "en" else answer_en
        final_text = final_text or answer_en

        return JsonResponse({
            "success": True,
            "chatbot_response": final_text,
            "detected_language": user_lang,
        })

    # 3b) Fallback: try Hindi intent directly on original text
    intent_hi = _detect_price_intent_hi(text)
    if intent_hi:
        raw_comm = intent_hi.get("commodity")
        market = intent_hi.get("market") or (request.GET.get("market") or "Varanasi")
        commodity_norm = _normalize_commodity_hi(raw_comm)
        from commodity_price import predict_price
        result = predict_price(commodity_norm, market)
        if not result.get("ok"):
            return JsonResponse({"success": False, "error": result.get("error", "prediction failed")}, status=400)

        answer_en = _format_price_answer_en(result)
        out_lang = _short_lang(user_lang)
        final_text = _translate_text(answer_en, src_lang="en", tgt_lang=out_lang) if out_lang != "en" else answer_en
        final_text = final_text or answer_en

        return JsonResponse({
            "success": True,
            "chatbot_response": final_text,
            "detected_language": user_lang,
        })

    # No known intent matched
    return JsonResponse({
        "success": True,
        "chatbot_response": "I'm not sure I understood. You can ask for commodity prices, e.g., 'price of onion in Varanasi'.",
        "detected_language": user_lang,
    })


# ---------------- Internal helpers ----------------

def _short_lang(lang_code: str) -> str:
    # Map locale like 'hi-IN' -> 'hi'
    return (lang_code or "en").split("-")[0].lower()


def _translate_text(text: str, src_lang: str, tgt_lang: str) -> str | None:
    """Translate using LibreTranslate-like API if available via TRANSLATE_URL.
    Returns None on failure to allow graceful fallback.
    """
    url = os.getenv("TRANSLATE_URL", "https://libretranslate.de/translate")
    try:
        resp = requests.post(url, timeout=10, data={
            "q": text,
            "source": src_lang,
            "target": tgt_lang,
            "format": "text",
        }, headers={"accept": "application/json"})
        if resp.status_code != 200:
            return None
        data = resp.json()
        # LibreTranslate returns {"translatedText": "..."}
        return data.get("translatedText") or data.get("translation")
    except Exception:
        return None


def _detect_price_intent_hi(text_hi: str):
    """Basic Hindi extractor for commodity and optional market.
    Examples: 'लखनऊ में प्याज का भाव', 'टमाटर की कीमत', 'आलू का रेट'
    """
    t = (text_hi or "").lower()
    # Market capture: ... में <city>
    market = None
    mkt = re.search(r"\b(?:में|me|mai)\s+([\w\s]{3,})\b", t)
    if mkt:
        market = mkt.group(1).strip()

    patterns = [
        r"\b([\w\s]{2,}?)\s*(?:का|की)?\s*(?:भाव|कीमत|दाम|रेट)\b",
        r"(?:भाव|कीमत|दाम|रेट)\s*(?:का|की)?\s*([\w\s]{2,}?)\b",
    ]
    for p in patterns:
        m = re.search(p, t, flags=re.UNICODE)
        if m and m.group(1):
            token = m.group(1)
            token = _clean_hi_token(token)
            if token and len(token) >= 2:
                return {"commodity": token, "market": market}
    return None


def _clean_hi_token(s: str) -> str:
    if not s:
        return s
    # Remove punctuation
    s = re.sub(r"[\"'“”‘’\-_,.?!()/]+", " ", s)
    # Remove common Hindi stopwords/verbs and price words
    stop = set(["में","me","mai","का","की","के","भाव","कीमत","दाम","रेट","क्या","है","वाली","वाले","आज","कल","बढ़","बढ़ने","घट","घटने"]) 
    tokens = [tok for tok in re.split(r"\s+", s) if tok]
    kept = [tok for tok in tokens if tok not in stop and len(tok) >= 2]
    return " ".join(kept).strip()


def _normalize_commodity_hi(name: str) -> str:
    n = (name or "").strip().lower()
    mapping = {
        "प्याज": "onion", "pyaz": "onion", "pyaj": "onion",
        "टमाटर": "tomato", "tamatar": "tomato",
        "आलू": "potato", "aloo": "potato",
        "गेहूं": "wheat", "gehun": "wheat", "gehu": "wheat",
        "चावल": "rice", "chawal": "rice", "धान": "rice",
        "मक्का": "maize", "makka": "maize",
        "गन्ना": "sugarcane", "ganna": "sugarcane",
        "सरसों": "mustard", "sarson": "mustard",
        "कपास": "cotton", "kapas": "cotton",
        "मिर्च": "chili", "मिर्ची": "chilli", "mirch": "chili",
        "सेब": "apple", "seb": "apple",
        "केला": "banana", "kela": "banana",
        "अदरक": "ginger", "adrak": "ginger",
        "लहसुन": "garlic", "lahsun": "garlic",
    }
    return mapping.get(n, n)


def _detect_price_intent_en(text_en: str):
    """Very simple English extractor for commodity + optional market.
    Examples: 'price of onion in varanasi', 'onion price', 'tomato rate at lucknow'
    """
    t = (text_en or "").lower()
    # Extract market
    market = None
    mkt = re.search(r"\b(?:in|at)\s+([a-zA-Z ]{3,})\b", t)
    if mkt:
        market = mkt.group(1).strip()

    # Try patterns
    patterns = [
        r"price\s+of\s+([a-zA-Z ]{2,})",
        r"rate\s+of\s+([a-zA-Z ]{2,})",
        r"\b([a-zA-Z ]{2,})\s+price\b",
        r"\b([a-zA-Z ]{2,})\s+rate\b",
    ]
    for p in patterns:
        m = re.search(p, t)
        if m and m.group(1):
            commodity = m.group(1)
            # Clean common trailing words
            commodity = re.sub(r"\b(in|at)\b", "", commodity).strip()
            if commodity:
                return {"commodity": commodity, "market": market}
    return None


def _format_price_answer_en(res: dict) -> str:
    trend = res.get("trend")
    change = res.get("change")
    current_price = res.get("current_price")
    predicted_price = res.get("predicted_price")
    commodity = res.get("commodity")
    diff = abs(change) if isinstance(change, (int, float)) else 0
    if trend == "increase":
        return f"{commodity.capitalize()} price is likely to increase by ₹{diff:.2f}/kg. Current: ₹{current_price}/kg → Predicted: ₹{predicted_price}/kg."
    elif trend == "decrease":
        return f"{commodity.capitalize()} price is likely to decrease by ₹{diff:.2f}/kg. Current: ₹{current_price}/kg → Predicted: ₹{predicted_price}/kg."
    else:
        return f"{commodity.capitalize()} price is likely to stay the same. Current: ₹{current_price}/kg → Predicted: ₹{predicted_price}/kg."


# ---------------- Commodity aliasing and query filtering for /api/price/all?q=... ----------------

_COMMODITY_ALIASES = {
    # Hindi script
    "टमाटर": "tomato",
    "प्याज़": "onion",
    "प्याज": "onion",
    "आलू": "potato",
    "गेहूं": "wheat",
    "चावल": "rice",
    "अरहर": "pigeon pea",
    "तूर": "pigeon pea",
    "चना": "chickpea",
    "सोयाबीन": "soybean",
    "कपास": "cotton",
    "गन्ना": "sugarcane",
    "मक्का": "maize",
    "सरसों": "mustard",
    # Transliterations
    "tamatar": "tomato",
    "pyaz": "onion",
    "pyaaz": "onion",
    "aloo": "potato",
    "aalu": "potato",
    "gehu": "wheat",
    "gehun": "wheat",
    "chawal": "rice",
    "arhar": "pigeon pea",
    "toor": "pigeon pea",
    "tur": "pigeon pea",
    "dal": "lentil",
    "chana": "chickpea",
    "soyabean": "soybean",
    "soya": "soybean",
    "kapas": "cotton",
    "ganna": "sugarcane",
    "makka": "maize",
    "makai": "maize",
    "corn": "maize",
    "sarson": "mustard",
}

def _norm_text(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[_\-]+", " ", s)
    s = re.sub(r"[^\w\s]", "", s, flags=re.UNICODE)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _normalize_candidates(name: str) -> list[str]:
    raw = (name or "").strip()
    if not raw:
        return []
    lower = raw.lower()
    mapped = _COMMODITY_ALIASES.get(raw) or _COMMODITY_ALIASES.get(lower)
    cands = [raw]
    if lower != raw:
        cands.append(lower)
    if mapped:
        cands.append(mapped)
    if lower.endswith("s"):
        cands.append(lower[:-1])
    else:
        cands.append(lower + "s")
    if mapped == "maize":
        cands.append("corn")
    if mapped == "pigeon pea":
        cands.extend(["toor dal", "arhar dal", "tur dal"]) 
    if mapped == "chickpea":
        cands.append("gram")
    # unique + truthy
    seen = set()
    out = []
    for c in cands:
        c = c.strip()
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out

def _find_item(items: list[dict], name: str):
    if not isinstance(items, list):
        return None
    def norm(s: str) -> str:
        return _norm_text(str(s or ""))
    cand_list = _normalize_candidates(name)
    # Build list of (item, normalized name)
    name_keys = ["name", "commodity", "commodity_name", "symbol", "title"]
    normalized = []
    for it in items:
        key = next((k for k in name_keys if k in it), None)
        if not key:
            continue
        normalized.append((it, norm(it.get(key))))
    # Try each candidate through matching strategies
    for cand in cand_list:
        target = norm(cand)
        if not target:
            continue
        tokens = [t for t in target.split(" ") if len(t) >= 3]
        # 1) Exact
        for it, nv in normalized:
            if nv == target:
                return it
        # 2) Substring (target in item)
        for it, nv in normalized:
            if target in nv:
                return it
        # 3) Reverse substring (item in target)
        for it, nv in normalized:
            if nv and nv in target:
                return it
        # 4) Token overlap
        if tokens:
            for it, nv in normalized:
                val_tokens = [t for t in nv.split(" ") if len(t) >= 3]
                if any(t in val_tokens for t in tokens):
                    return it
    return None

def _filter_items_by_query(items: list[dict], q: str):
    return _find_item(items, q)

def _normalize_commodity_param(name: str) -> str:
    """Normalize explicit commodity param using alias table only (no sentence parsing)."""
    n = (name or "").strip()
    lower = n.lower()
    mapped = _COMMODITY_ALIASES.get(n) or _COMMODITY_ALIASES.get(lower)
    return mapped or n
