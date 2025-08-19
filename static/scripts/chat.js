// Backend communication and processing functions

// Commodity trend helper (fetches from the price API and answers in a fixed sentence)
const PRICE_API_URL = '/api/price/all/';
const ADVISORY_API_BASE = '/api/advisory/';

// Removed parse-based commodity extraction; rely on Gemini intent understanding.

function extractFromTo(item) {
    const candidates = [
        // Prefer the provided API schema
        ['current_price', 'predicted_price'],
        ['current_price_quintal', 'predicted_price_quintal'],
        // Other common possibilities
        ['previous', 'current'],
        ['prev', 'curr'],
        ['yesterday', 'today'],
        ['start', 'end'],
        ['open', 'close'],
        ['from', 'to'],
        ['price_from', 'price_to'],
        ['old', 'new'],
        ['last', 'price'],
    ];
    const numeric = (v) => typeof v === 'number' && isFinite(v);
    for (const [fromKey, toKey] of candidates) {
        const from = item[fromKey];
        const to = item[toKey];
        if (numeric(from) && numeric(to)) {
            return { from, to };
        }
    }
    const numericEntries = Object.entries(item).filter(([, v]) => numeric(v));
    if (numericEntries.length >= 2) {
        const keyScore = (k) => {
            if (/prev|previous|yesterday|start|open|from|old|last/i.test(k)) return -1;
            if (/curr|current|today|end|close|to|new|price/i.test(k)) return 1;
            return 0;
        };
        numericEntries.sort((a, b) => keyScore(a[0]) - keyScore(b[0]));
        const from = numericEntries[0][1];
        const to = numericEntries[1][1];
        return { from, to };
    }
    return null;
}

// Track current audio to avoid overlaps
let __currentTtsAudio = null;

function __stopAnySpeech() {
    try { if (window && window.speechSynthesis) window.speechSynthesis.cancel(); } catch {}
    try { if (__currentTtsAudio) { __currentTtsAudio.pause(); __currentTtsAudio.currentTime = 0; } } catch {}
    __currentTtsAudio = null;
}

// Helper: direct Sarvam TTS from browser
async function __sarvamDirectTTS(text, lang, voice) {
    const url = (typeof window !== 'undefined' && window.SARVAM_TTS_URL) ? window.SARVAM_TTS_URL : '';
    const key = (typeof window !== 'undefined' && window.SARVAM_API_KEY) ? window.SARVAM_API_KEY : '';
    if (!url || !key) throw new Error('Direct Sarvam missing url or key');
    const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${key}`,
        'x-api-key': key,
        'X-API-Key': key,
        'api-key': key,
        'subscription-key': key,
        'Subscription-Key': key,
        'Ocp-Apim-Subscription-Key': key,
    };
    const payload = { text, language: lang, voice, model: voice };
    const res = await fetch(url, { method: 'POST', headers, body: JSON.stringify(payload) });
    if (!res.ok) {
        const t = await res.text().catch(() => '');
        throw new Error(`Sarvam direct ${res.status}: ${t}`);
    }
    const data = await res.json();
    const b64 = data && (data.audio_base64 || data.audio);
    if (!b64) throw new Error('No audio in Sarvam direct response');
    return b64;
}

// --- Sarvam TTS client (tries direct first; falls back to backend) ---
async function speakResponse(text, useHindi) {
    const lang = useHindi ? 'hi-IN' : 'en-IN';
    const voice = (typeof window !== 'undefined' && window.SARVAM_VOICE) ? window.SARVAM_VOICE : 'Anushka';
    try {
        __stopAnySpeech();
        console.log('[TTS] Using Sarvam voice:', voice, 'lang:', lang);
        // Try direct provider call first if enabled
        if (typeof window !== 'undefined' && window.USE_DIRECT_SARVAM) {
            try {
                const b64 = await __sarvamDirectTTS(text, lang, voice);
                const audio = new Audio(`data:audio/mp3;base64,${b64}`);
                __currentTtsAudio = audio;
                await audio.play();
                return;
            } catch (e) {
                console.warn('[TTS][chat.js] Direct Sarvam failed, falling back to backend:', e?.message || e);
            }
        }
        const ttsHeaders = { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') };
        if (typeof window !== 'undefined' && window.SARVAM_API_KEY) {
            ttsHeaders['X-Sarvam-Key'] = window.SARVAM_API_KEY;
        }
        const res = await fetch('/api/text-to-speech/', {
            method: 'POST',
            headers: ttsHeaders,
            body: JSON.stringify({ text, language: lang, voice })
        });
        if (!res.ok) {
            let errText = '';
            try { errText = await res.text(); } catch {}
            console.error('[TTS][chat.js] /api/text-to-speech/ failed', res.status, errText);
            return; // no fallback
        }
        const data = await res.json();
        const b64 = data && (data.audio_base64 || data.audio);
        if (!b64) {
            console.error('[TTS][chat.js] No audio in response', data);
            return;
        }
        const audio = new Audio(`data:audio/mp3;base64,${b64}`);
        __currentTtsAudio = audio;
        await audio.play();
    } catch (e) {
        console.error('[TTS][chat.js] exception', e);
        return;
    }
}

// Map common Hindi and transliterated commodity names to canonical English API names
const COMMODITY_ALIASES = {
    // Hindi script
    'टमाटर': 'tomato',
    'प्याज़': 'onion',
    'प्याज': 'onion',
    'आलू': 'potato',
    'गेहूं': 'wheat',
    'चावल': 'rice',
    'अरहर': 'pigeon pea',
    'तूर': 'pigeon pea',
    'चना': 'chickpea',
    'सोयाबीन': 'soybean',
    'कपास': 'cotton',
    'गन्ना': 'sugarcane',
    'मक्का': 'maize',
    'सरसों': 'mustard',
    // Transliterations
    'tamatar': 'tomato',
    'pyaz': 'onion',
    'pyaaz': 'onion',
    'aloo': 'potato',
    'aalu': 'potato',
    'gehu': 'wheat',
    'gehun': 'wheat',
    'chawal': 'rice',
    'arhar': 'pigeon pea',
    'toor': 'pigeon pea',
    'tur': 'pigeon pea',
    'dal': 'lentil',
    'chana': 'chickpea',
    'soyabean': 'soybean',
    'soya': 'soybean',
    'kapas': 'cotton',
    'ganna': 'sugarcane',
    'makka': 'maize',
    'makai': 'maize',
    'corn': 'maize',
    'sarson': 'mustard'
};

function normalizeCommodityCandidates(name) {
    const raw = String(name || '').trim();
    if (!raw) return [];
    const lower = raw.toLowerCase();
    const mapped = COMMODITY_ALIASES[raw] || COMMODITY_ALIASES[lower];
    const candidates = [];
    // Original provided name
    candidates.push(raw);
    if (lower !== raw) candidates.push(lower);
    // Mapped alias
    if (mapped) candidates.push(mapped);
    // Simple plural/singular variants
    if (lower.endsWith('s')) candidates.push(lower.slice(0, -1));
    else candidates.push(lower + 's');
    // Common pairs
    if (mapped === 'maize') candidates.push('corn');
    if (mapped === 'pigeon pea') candidates.push('toor dal', 'arhar dal', 'tur dal');
    if (mapped === 'chickpea') candidates.push('gram');
    return Array.from(new Set(candidates)).filter(Boolean);
}

// Language detector for Hindi
// - Detects Devanagari script
// - Also detects common Romanized Hindi tokens (heuristic)
function isHindi(text) {
    if (!text) return false;
    const s = String(text).toLowerCase();
    // Devanagari range
    if (/[\u0900-\u097F]/.test(s)) return true;
    // Common Romanized Hindi function words and price words
    const romanHi = [
        'ka','ki','ke','mein','me','mai','kya','hai','hain','wala','wale','wali',
        'aaj','kal','bhav','bhaav','daam','kimat','keemat','rate','badhega','badhegi','ghatega','ghategi',
        'tamatar','pyaz','pyaaz','aloo','chawal','gehu','gehun','makka','sarson','toor','arhar','chana'
    ];
    let hits = 0;
    for (const w of romanHi) {
        if (s.includes(` ${w} `) || s.startsWith(`${w} `) || s.endsWith(` ${w}`) || s === w) {
            hits++;
            if (hits >= 2) return true; // require at least 2 hits to avoid false positives
        }
    }
    return false;
}

// Sanitize Gemini natural-language answers (remove stray labels/markdown)
function sanitizeAnswer(text) {
    if (!text) return '';
    let t = String(text).trim();
    // Remove code fences and markdown artifacts
    t = t.replace(/^```[\s\S]*?```$/g, '').replace(/```/g, '').trim();
    // Remove leading intent/labels if model leaks them
    t = t.replace(/^\s*(intent|seed_variety|irrigation_timing|cold_risk)\s*[:\-]?\s*/i, '');
    // Collapse multiple spaces
    t = t.replace(/\s{2,}/g, ' ').trim();
    // Keep exactly one sentence: split on terminal punctuation and keep first non-empty
    const parts = t.split(/(?<=[.!?])\s+/);
    const first = parts.find(p => p && p.trim().length > 0) || t;
    let one = first.trim();
    // Ensure it ends with period if it lacks terminal punctuation
    if (!/[.!?]$/.test(one)) one = one + '.';
    return one;
}

function findCommodity(data, name) {
    if (!Array.isArray(data)) return null;
    const norm = (s) => String(s || '')
        .toLowerCase()
        .replace(/[_\-]+/g, ' ')
        .replace(/[^a-z0-9\s]/g, '')
        .replace(/\s+/g, ' ')
        .trim();
    const target = norm(name);
    if (!target) return null;

    const tokens = target.split(' ').filter(t => t.length >= 3);
    const nameKeys = ['name', 'commodity', 'commodity_name', 'symbol', 'title'];

    // 1) Exact match
    for (const item of data) {
        const key = nameKeys.find((k) => k in item);
        if (!key) continue;
        const val = norm(item[key]);
        if (val === target) return item;
    }

    // 2) Substring match (target inside item value)
    for (const item of data) {
        const key = nameKeys.find((k) => k in item);
        if (!key) continue;
        const val = norm(item[key]);
        if (val.includes(target)) return item;
    }

    // 3) Reverse substring match (item value inside target)
    for (const item of data) {
        const key = nameKeys.find((k) => k in item);
        if (!key) continue;
        const val = norm(item[key]);
        if (val && target.includes(val)) return item;
    }

    // 4) Token overlap (any meaningful token matches)
    if (tokens.length) {
        for (const item of data) {
            const key = nameKeys.find((k) => k in item);
            if (!key) continue;
            const val = norm(item[key]);
            const valTokens = val.split(' ').filter(t => t.length >= 3);
            if (tokens.some(t => valTokens.includes(t))) return item;
        }
    }

    return null;
}

function buildAnswerLocalized(commodityName, from, to, useHindi) {
    if (useHindi) {
        // Hinglish (Latin script Hindi)
        let trend = 'waisi hi rahegi';
        if (to > from) trend = 'badhegi';
        else if (to < from) trend = 'ghategi';
        return `${commodityName} ki keemat ${from}/kg se ${to}/kg tak ${trend}.`;
    }
    let trend = 'stay the same';
    if (to > from) trend = 'increase';
    else if (to < from) trend = 'decrease';
    return `${commodityName} price is going to ${trend} from ${from}/kg to ${to}/kg`;
}

async function getCommodityTrend(commodityName, apiUrl = PRICE_API_URL, useHindi = false) {
    const res = await fetch(apiUrl, { cache: 'no-store' });
    if (!res.ok) throw new Error(`API error ${res.status}`);
    const data = await res.json();
    // Support both array response and wrapped responses like { ok, items: [...] }
    const list = Array.isArray(data) ? data : (Array.isArray(data.items) ? data.items : (Array.isArray(data.results) ? data.results : []));
    // Try multiple normalized candidates
    const candidates = normalizeCommodityCandidates(commodityName);
    let item = null;
    let usedName = String(commodityName);
    for (const cand of candidates) {
        item = findCommodity(list, cand);
        if (item) { usedName = cand; break; }
    }
    if (!item) return useHindi ? `कीमत सूची में "${commodityName}" नहीं मिला।` : `Could not find "${commodityName}" in the price list.`;
    const prices = extractFromTo(item);
    if (!prices) return useHindi ? `"${commodityName}" मिला, लेकिन कीमत फ़ील्ड समझ नहीं पाए।` : `Found "${commodityName}" but could not infer price fields.`;
    const displayName = item.name || item.commodity || item.commodity_name || item.symbol || String(usedName);
    return buildAnswerLocalized(displayName, prices.from, prices.to, useHindi);
}

// Removed regex-based advisory detection; rely on Gemini intent understanding.

async function fetchAdvisory(city, ph) {
    const url = `${ADVISORY_API_BASE}?city=${encodeURIComponent(city)}&ph=${encodeURIComponent(ph)}`;
    const res = await fetch(url, { cache: 'no-store' });
    if (!res.ok) throw new Error(`Advisory API error ${res.status}`);
    return res.json();
}

// Gemini integration helpers (client-side). Security note: do not expose keys in production.
function getGeminiApiKey() {
    // Prefer a runtime-provided key; fallback to localStorage for dev
    return (window && window.GEMINI_API_KEY) || localStorage.getItem('GEMINI_API_KEY') || '';
}

async function geminiGenerate(model, prompt) {
    const apiKey = getGeminiApiKey();
    if (!apiKey) throw new Error('Missing GEMINI API key');
    const url = `https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(model)}:generateContent?key=${encodeURIComponent(apiKey)}`;
    const body = {
        contents: [{ parts: [{ text: prompt }]}]
    };
    const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });
    if (!res.ok) throw new Error(`Gemini error ${res.status}`);
    const data = await res.json();
    const text = data?.candidates?.[0]?.content?.parts?.[0]?.text || '';
    if (!text) throw new Error('Empty Gemini response');
    return text.trim();
}

// Ask Gemini to understand user intent and extract slots
async function geminiUnderstandQuestion(question) {
    const apiKey = getGeminiApiKey();
    if (!apiKey) throw new Error('Missing GEMINI API key');
    const model = 'gemini-2.0-flash';
    const schema = `
Respond ONLY with minified JSON like:
{"intent":"commodity_trend|advisory_seed|advisory_irrigation|advisory_cold|unknown","commodity":"<name>|","city":"|","ph":6.4}
Rules:
- intent must be one of the allowed tokens.
- commodity only if clearly mentioned.
- city if user mentions a city; else empty.
- ph number if mentioned; else omit.
No explanation text.`;
    const prompt = `Understand the user's question and extract intent and fields.
User: ${question}
${schema}`;
    const raw = await geminiGenerate(model, prompt);
    // Try to parse JSON from the response safely
    let text = raw.trim();
    // Remove code fences if any
    text = text.replace(/^```(?:json)?/i, '').replace(/```$/i, '').trim();
    try {
        const obj = JSON.parse(text);
        return obj && typeof obj === 'object' ? obj : { intent: 'unknown' };
    } catch {
        // Attempt to find a JSON substring
        const m = text.match(/\{[\s\S]*\}/);
        if (m) {
            try { return JSON.parse(m[0]); } catch {}
        }
        return { intent: 'unknown' };
    }
}

function buildAdvisoryPrompt(question, advisoryJson) {
    const dataStr = JSON.stringify(advisoryJson, null, 2);
    const wantHindi = isHindi(question);
    const langInstruction = wantHindi
        ? 'Answer STRICTLY in Hindi.'
        : 'Answer STRICTLY in English.';
    return `You are an expert agricultural assistant.
Task:
1) First infer the user's intent internally as one of: seed_variety, irrigation_timing, cold_risk. Do NOT output the word "Intent" or any labels.
2) Respond with EXACTLY ONE concise, user-friendly sentence in plain text, suitable for a farmer.
3) Base your answer STRICTLY on the JSON data provided. Do not invent or assume anything outside the JSON.
4) If helpful and present, you may reference city and soil pH from the JSON.
5) Do NOT output JSON, markdown, code fences, or headings. Just the answer sentence(s).
6) Use fields if present:
   - seed_variety: crop_recommendation
   - irrigation_timing: irrigation_advice
   - cold_risk: cold_risk
7) ${langInstruction}

User question: ${question}

JSON data:\n${dataStr}\n`;
}

async function answerAdvisoryQuestion(q, slots = {}) {
    const city = (slots.city && String(slots.city).trim()) || 'Varanasi';
    const ph = typeof slots.ph === 'number' ? slots.ph : 6.5;
    const data = await fetchAdvisory(city, ph);
    const s = String(q).toLowerCase();
    const model = 'gemini-2.0-flash';
    try {
        // Always let Gemini infer intent first
        const prompt = buildAdvisoryPrompt(q, data);
        const out = await geminiGenerate(model, prompt);
        return sanitizeAnswer(out);
    } catch (e) {
        console.warn('[MICK] Gemini unavailable, falling back:', e?.message || e);
        // fall through to deterministic fallback
    }

    // Deterministic fallback (previous behavior)
    // Seed variety
    const hindi = isHindi(q);
    if (/seed|variety|crop\s+recommendation/i.test(s)) {
        const crop = data.crop_recommendation || (hindi ? 'उपलब्ध नहीं' : 'Not available');
        return hindi
            ? `${data.city || city} (pH ${data.inputs?.ph ?? ph}) के लिए अनुशंसित बीज/फसल: ${crop}।`
            : `Recommended seed/crop for ${data.city || city} (pH ${data.inputs?.ph ?? ph}): ${crop}.`;
    }
    // Irrigation timing
    if (/irrigat(e|ion)/i.test(s)) {
        const advice = data.irrigation_advice || (hindi ? 'कोई सिंचाई सलाह उपलब्ध नहीं है।' : 'No irrigation advice available.');
        return advice;
    }
    // Cold/temperature risk
    if (/cold|temperature|risk/i.test(s)) {
        const risk = data.cold_risk || (hindi ? 'कोई जोखिम डेटा उपलब्ध नहीं है।' : 'No risk data available.');
        return risk;
    }
    return hindi
        ? 'कृपया इनमें से पूछें: Q1 बीज/फसल सिफारिश, Q2 सिंचाई का समय, Q3 तापमान/ठंड जोखिम।'
        : 'Please ask one of: Q1 seed variety, Q2 irrigation timing, Q3 temperature risk.';
}

// Complete speech processing pipeline
async function processSpeechPipeline(spokenText, language) {
    try {
        updateStatus('Processing speech...');
        
        // Gemini-only understanding (voice)
        const apiKey = getGeminiApiKey();
        showLoading(true);
        let ans = '';
        const wantHindi = isHindi(spokenText);
        try {
            if (!apiKey) throw new Error('Missing GEMINI API key');
            const u = await geminiUnderstandQuestion(spokenText);
            if (u && u.intent === 'commodity_trend') {
                if (!u.commodity) {
                    ans = wantHindi ? 'कृपया कमोडिटी का नाम बताइए (जैसे प्याज़, टमाटर) ताकि कीमत का रुझान बताया जा सके।' : 'Please mention the commodity name for price trend (e.g., onion, tomato).';
                } else {
                    ans = await getCommodityTrend(u.commodity, PRICE_API_URL, wantHindi);
                }
            } else if (u && (u.intent === 'advisory_seed' || u.intent === 'advisory_irrigation' || u.intent === 'advisory_cold')) {
                ans = await answerAdvisoryQuestion(spokenText, u);
            } else {
                throw new Error('Unknown intent');
            }
        } catch (e) {
            console.warn('[MICK] Gemini understand failed, falling back to backend:', e?.message || e);
            // Backend fallback to deterministic pipeline
            try {
                const response = await fetch('/api/process-speech/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify({
                        spoken_text: spokenText,
                        language: language
                    })
                });
                if (response.ok) {
                    const data = await response.json();
                    ans = data && (data.chatbot_response || '');
                    if (!ans) throw new Error('Empty backend response');
                } else {
                    const errText = await response.text().catch(()=>'');
                    throw new Error(`Backend ${response.status}: ${errText}`);
                }
            } catch (be) {
                console.warn('[MICK] Backend fallback failed:', be?.message || be);
                ans = wantHindi ? 'माफ़ कीजिए, समझने में दिक्कत हुई। कृपया थोड़ी देर बाद फिर से प्रयास करें।' : 'Sorry, I had trouble understanding the request. Please try again shortly.';
            }
        }
        addMessage('ai', ans);
        chatbotResponse = ans;
        updateStatus('Ready');
        updateUI('ready');
        showLoading(false);
        if (autoSpeakEnabled) await speakResponse(ans, wantHindi);
    } catch (error) {
        console.error('Pipeline error:', error);
        updateStatus('Error: ' + error.message);
        updateUI('error');
        showLoading(false);
    }
}

// Process text input
async function processTextInput(text) {
    try {
        updateStatus('Processing text...');
        
        // Gemini-only understanding (text)
        const apiKey = getGeminiApiKey();
        showLoading(true);
        let ans = '';
        const wantHindi = isHindi(text);
        try {
            if (!apiKey) throw new Error('Missing GEMINI API key');
            const u = await geminiUnderstandQuestion(text);
            if (u && u.intent === 'commodity_trend') {
                if (!u.commodity) {
                    ans = wantHindi ? 'कृपया कमोडिटी का नाम बताइए (जैसे प्याज़, टमाटर) ताकि कीमत का रुझान बताया जा सके।' : 'Please mention the commodity name for price trend (e.g., onion, tomato).';
                } else {
                    ans = await getCommodityTrend(u.commodity, PRICE_API_URL, wantHindi);
                }
            } else if (u && (u.intent === 'advisory_seed' || u.intent === 'advisory_irrigation' || u.intent === 'advisory_cold')) {
                ans = await answerAdvisoryQuestion(text, u);
            } else {
                throw new Error('Unknown intent');
            }
        } catch (e) {
            console.warn('[MICK] Gemini understand failed, falling back to backend:', e?.message || e);
            // Backend fallback
            try {
                const response = await fetch('/api/process-speech/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify({
                        spoken_text: text,
                        language: 'en-US'
                    })
                });
                if (response.ok) {
                    const data = await response.json();
                    ans = data && (data.chatbot_response || '');
                    if (!ans) throw new Error('Empty backend response');
                } else {
                    const errText = await response.text().catch(()=>'');
                    throw new Error(`Backend ${response.status}: ${errText}`);
                }
            } catch (be) {
                console.warn('[MICK] Backend fallback failed:', be?.message || be);
                ans = wantHindi ? 'माफ़ कीजिए, समझने में दिक्कत हुई। कृपया थोड़ी देर बाद फिर से प्रयास करें।' : 'Sorry, I had trouble understanding the request. Please try again shortly.';
            }
        }
        addMessage('ai', ans);
        chatbotResponse = ans;
        updateStatus('Ready');
        showLoading(false);
        if (autoSpeakEnabled) await speakResponse(ans, wantHindi);
        return;
        
    } catch (error) {
        console.error('Text processing error:', error);
        updateStatus('Error: ' + error.message);
        showLoading(false);
    }
}

// Get CSRF token for Django
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
