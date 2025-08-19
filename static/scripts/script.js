 // Speech Recognition API
let recognition;
let isListening = false;
let spokenText = '';
let detectedLanguage = 'en-US';
let chatbotResponse = '';

// TTS audio handle to prevent overlaps in this module
let __scriptCurrentTtsAudio = null;

function __scriptStopAnySpeech() {
    try { if (window && window.speechSynthesis) window.speechSynthesis.cancel(); } catch {}
    try { if (__scriptCurrentTtsAudio) { __scriptCurrentTtsAudio.pause(); __scriptCurrentTtsAudio.currentTime = 0; } } catch {}
    __scriptCurrentTtsAudio = null;
}

// Web Speech API fallback (browser speech synthesis)
function __scriptWebSpeechFallback(text, lang) {
    try {
        if (!('speechSynthesis' in window)) {
            console.warn('[TTS][script.js] Web Speech API not available for fallback');
            return;
        }
        const speakNow = () => {
            const utterance = new SpeechSynthesisUtterance(text);
            // Map hi-IN/en-IN to language codes
            utterance.lang = (lang && lang.toLowerCase().startsWith('hi')) ? 'hi-IN' : 'en-US';
            // Apply speed
            if (typeof voiceSpeed === 'number' && voiceSpeed > 0) utterance.rate = Math.max(0.5, Math.min(2, voiceSpeed));
            // Try pick a voice roughly matching
            const voices = window.speechSynthesis.getVoices();
            const wantHi = utterance.lang === 'hi-IN';
            if (voices && voices.length) {
                const match = voices.find(v => (wantHi ? /hi|hindi/i.test(v.lang) : /en/i.test(v.lang)));
                if (match) utterance.voice = match;
            }
            window.speechSynthesis.cancel();
            window.speechSynthesis.speak(utterance);
            console.log('[TTS][script.js] Using Web Speech fallback');
        };

        // If voices not yet loaded, wait for them
        const existing = window.speechSynthesis.getVoices();
        if (!existing || existing.length === 0) {
            let spoke = false;
            const onVoices = () => {
                if (spoke) return;
                spoke = true;
                try { window.speechSynthesis.removeEventListener('voiceschanged', onVoices); } catch {}
                speakNow();
            };
            try { window.speechSynthesis.addEventListener('voiceschanged', onVoices); } catch {}
            // Safety timeout in case event never fires
            setTimeout(() => { if (!spoke) { onVoices(); } }, 600);
        } else {
            speakNow();
        }
    } catch (err) {
        console.warn('[TTS][script.js] Web Speech fallback failed:', err?.message || err);
    }
}

// Helper: direct Sarvam TTS from browser for script.js module
async function __scriptSarvamDirectTTS(text, lang, voice) {
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

// Chat History
let chatHistory = [];
let autoScrollEnabled = true;

// DOM Elements
const mickCircle = document.getElementById('mickCircle');
const conversationContainer = document.getElementById('conversationContainer');
const textInput = document.getElementById('textInput');
const sendBtn = document.getElementById('sendBtn');
const statusMessage = document.getElementById('statusMessage');
const statusDot = document.getElementById('statusDot');
const replayBtn = document.getElementById('replayBtn');
const clearBtn = document.getElementById('clearBtn');
const settingsBtn = document.getElementById('settingsBtn');
const loadingOverlay = document.getElementById('loadingOverlay');
const voiceVisualizer = document.getElementById('voiceVisualizer');
const particleContainer = document.getElementById('particleContainer');
const settingsModal = document.getElementById('settingsModal');
const modalClose = document.getElementById('modalClose');
const voiceSpeedSlider = document.getElementById('voiceSpeed');
const speedValue = document.getElementById('speedValue');
const autoSpeakToggle = document.getElementById('autoSpeak');

// Settings
let voiceSpeed = 1.0;
let autoSpeakEnabled = true;

// Initialize speech recognition
function initSpeechRecognition() {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = detectedLanguage;

        recognition.onstart = function() {
            isListening = true;
            updateUI('listening');
            updateStatus('Listening for speech...');
            showLoading(false);
            activateVoiceVisualizer();
        };

        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            spokenText = transcript;
            
            addMessage('user', transcript);
            isListening = false;
            updateUI('processing');
            updateStatus('Processing your speech...');
            showLoading(true);
            deactivateVoiceVisualizer();
            
            // Process the speech through the complete pipeline
            processSpeechPipeline(transcript, detectedLanguage);
        };

        recognition.onerror = function(event) {
            console.error('Speech recognition error:', event.error);
            isListening = false;
            updateUI('error');
            updateStatus('Error: ' + event.error);
            showLoading(false);
            deactivateVoiceVisualizer();
        };

        recognition.onend = function() {
            isListening = false;
            updateUI('ready');
            showLoading(false);
            deactivateVoiceVisualizer();
        };
    } else {
        console.log('Speech recognition not supported');
        updateUI('error');
        updateStatus('Speech recognition not supported in this browser');
    }
}



// Add message to chat
function addMessage(type, text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    
    const icon = document.createElement('i');
    icon.className = type === 'user' ? 'fas fa-user' : 'fas fa-robot';
    avatar.appendChild(icon);
    
    const content = document.createElement('div');
    content.className = 'message-content';
    
    const messageText = document.createElement('div');
    messageText.className = 'message-text';
    messageText.textContent = text;
    
    const messageTime = document.createElement('div');
    messageTime.className = 'message-time';
    messageTime.textContent = getCurrentTime();
    
    content.appendChild(messageText);
    content.appendChild(messageTime);
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    
    conversationContainer.appendChild(messageDiv);
    
    // Add to chat history
    chatHistory.push({
        type: type,
        text: text,
        timestamp: new Date()
    });
    
    // Auto-scroll to bottom
    if (autoScrollEnabled) {
        scrollToBottom();
    }
}

// Get current time
function getCurrentTime() {
    const now = new Date();
    return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// Scroll to bottom of chat
function scrollToBottom() {
    conversationContainer.scrollTop = conversationContainer.scrollHeight;
}

// Clear chat history
function clearChat() {
    // Keep only the welcome message
    const welcomeMessage = conversationContainer.querySelector('.ai-message');
    conversationContainer.innerHTML = '';
    if (welcomeMessage) {
        conversationContainer.appendChild(welcomeMessage);
    }
    
    chatHistory = [];
    updateStatus('Chat cleared');
}

// Handle text input
function handleTextInput() {
    const text = textInput.value.trim();
    if (text) {
        addMessage('user', text);
        textInput.value = '';
        resizeTextarea();
        
        // Process the text
        processTextInput(text);
    }
}



// Resize textarea
function resizeTextarea() {
    textInput.style.height = 'auto';
    textInput.style.height = Math.min(textInput.scrollHeight, 120) + 'px';
}

// Update status display
function updateStatus(message) {
    if (statusMessage) {
        statusMessage.textContent = message;
    }
}

// Update UI status with visual feedback
function updateUI(status) {
    if (mickCircle) {
        // Remove all status classes
        mickCircle.classList.remove('listening', 'processing', 'error');
        
        switch (status) {
            case 'listening':
                mickCircle.classList.add('listening');
                break;
            case 'processing':
                mickCircle.classList.add('processing');
                break;
            case 'error':
                mickCircle.classList.add('error');
                break;
            default:
                // Ready state - no additional classes
                break;
        }
    }
    
    if (statusDot) {
        statusDot.classList.remove('listening', 'processing');
        
        switch (status) {
            case 'listening':
                statusDot.classList.add('listening');
                break;
            case 'processing':
                statusDot.classList.add('processing');
                break;
            default:
                // Ready state
                break;
        }
    }
}

// Show/hide loading overlay
function showLoading(show) {
    if (loadingOverlay) {
        if (show) {
            loadingOverlay.classList.add('show');
        } else {
            loadingOverlay.classList.remove('show');
        }
    }
}

// Voice visualizer functions
function activateVoiceVisualizer() {
    if (voiceVisualizer) {
        voiceVisualizer.classList.add('active');
    }
}

function deactivateVoiceVisualizer() {
    if (voiceVisualizer) {
        voiceVisualizer.classList.remove('active');
    }
}

// Enhanced replay functionality (Sarvam only)
async function replaySpeech() {
    if (!chatbotResponse) return;
    const langNorm = (detectedLanguage && detectedLanguage.toLowerCase().startsWith('hi')) ? 'hi-IN' : 'en-IN';
    __scriptStopAnySpeech();
    console.log('[Replay] Sarvam voice:', (window && window.SARVAM_VOICE) ? window.SARVAM_VOICE : 'Anushka', 'lang:', langNorm);
    await speakResponseSarvam(chatbotResponse, langNorm);
    // Visual feedback
    if (replayBtn) {
        replayBtn.style.transform = 'scale(0.95)';
        setTimeout(() => { replayBtn.style.transform = 'scale(1)'; }, 150);
    }
}

// Speak text with specified language (Sarvam only)
async function speakText(text, language) {
    const langNorm = (language && language.toLowerCase().startsWith('hi')) ? 'hi-IN' : 'en-IN';
    __scriptStopAnySpeech();
    console.log('[SpeakText] Sarvam voice:', (window && window.SARVAM_VOICE) ? window.SARVAM_VOICE : 'Anushka', 'lang:', langNorm);
    await speakResponseSarvam(text, langNorm);
}

// Local Sarvam TTS client (duplicates minimal logic; avoids browser TTS fallback)
async function speakResponseSarvam(text, language) {
    try {
        const voice = (typeof window !== 'undefined' && window.SARVAM_VOICE) ? window.SARVAM_VOICE : 'Anushka';
        const lang = language || 'en-IN';
        // Try direct provider call first if enabled and helper exists
        if (typeof window !== 'undefined' && window.USE_DIRECT_SARVAM && typeof __scriptSarvamDirectTTS === 'function') {
            try {
                const b64 = await __scriptSarvamDirectTTS(text, lang, voice);
                const audio = new Audio(`data:audio/mp3;base64,${b64}`);
                __scriptCurrentTtsAudio = audio;
                await audio.play();
                return;
            } catch (e) {
                console.warn('[TTS][script.js] Direct Sarvam failed, falling back to backend:', e?.message || e);
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
            console.error('[TTS][script.js] /api/text-to-speech/ failed', res.status, errText);
            // Fallback to Web Speech API
            __scriptWebSpeechFallback(text, lang);
            return;
        }
        const data = await res.json();
        const b64 = data && (data.audio_base64 || data.audio);
        if (!b64) {
            console.error('[TTS][script.js] No audio in response', data);
            // Fallback to Web Speech API
            __scriptWebSpeechFallback(text, lang);
            return;
        }
        const audio = new Audio(`data:audio/mp3;base64,${b64}`);
        audio.playbackRate = (typeof voiceSpeed === 'number' && voiceSpeed > 0) ? voiceSpeed : 1.0;
        __scriptCurrentTtsAudio = audio;
        try {
            await audio.play();
        } catch (playErr) {
            console.warn('[TTS][script.js] Audio play() failed, falling back to Web Speech:', playErr?.message || playErr);
            __scriptWebSpeechFallback(text, lang);
        }
    } catch (e) {
        console.error('[TTS][script.js] exception', e);
        // Fallback to Web Speech API
        try { __scriptWebSpeechFallback(text, language || 'en-IN'); } catch {}
    }
}

// Minimal CSRF getter (for safety if chat.js not yet loaded)
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

// Start listening function
function startListening() {
    if (recognition && !isListening) {
        recognition.start();
    }
}

// Particle system
function createParticles() {
    if (!particleContainer) return;
    
    setInterval(() => {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.animationDuration = (Math.random() * 3 + 3) + 's';
        
        particleContainer.appendChild(particle);
        
        // Remove particle after animation
        setTimeout(() => {
            if (particle.parentNode) {
                particle.parentNode.removeChild(particle);
            }
        }, 6000);
    }, 200);
}

// Modal functions
function showSettingsModal() {
    if (settingsModal) {
        settingsModal.classList.add('show');
    }
}

function hideSettingsModal() {
    if (settingsModal) {
        settingsModal.classList.remove('show');
    }
}

// Settings handlers
function handleVoiceSpeedChange() {
    voiceSpeed = parseFloat(voiceSpeedSlider.value);
    speedValue.textContent = voiceSpeed.toFixed(1) + 'x';
}

function handleAutoSpeakChange() {
    autoSpeakEnabled = autoSpeakToggle.checked;
}

// Add click event to mICK circle
function addCircleClickEvent() {
    if (mickCircle) {
        mickCircle.addEventListener('click', startListening);
    }
}

// Add text input events
function addTextInputEvents() {
    if (textInput) {
        textInput.addEventListener('input', resizeTextarea);
        textInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleTextInput();
            }
        });
    }
}

// Add send button event
function addSendButtonEvent() {
    if (sendBtn) {
        sendBtn.addEventListener('click', handleTextInput);
    }
}

// Add click event to replay button
function addReplayClickEvent() {
    if (replayBtn) {
        replayBtn.addEventListener('click', replaySpeech);
    }
}

// Add click event to clear button
function addClearClickEvent() {
    if (clearBtn) {
        clearBtn.addEventListener('click', clearChat);
    }
}

// Add click event to settings button
function addSettingsClickEvent() {
    if (settingsBtn) {
        settingsBtn.addEventListener('click', showSettingsModal);
    }
}

// Add modal close event
function addModalCloseEvent() {
    if (modalClose) {
        modalClose.addEventListener('click', hideSettingsModal);
    }
    
    // Close modal when clicking outside
    if (settingsModal) {
        settingsModal.addEventListener('click', (e) => {
            if (e.target === settingsModal) {
                hideSettingsModal();
            }
        });
    }
}

// Add settings change events
function addSettingsChangeEvents() {
    if (voiceSpeedSlider) {
        voiceSpeedSlider.addEventListener('input', handleVoiceSpeedChange);
    }
    
    if (autoSpeakToggle) {
        autoSpeakToggle.addEventListener('change', handleAutoSpeakChange);
    }
}

// Add keyboard shortcuts
function addKeyboardShortcuts() {
    document.addEventListener('keydown', function(event) {
        if (event.key === ' ' && !isListening && event.target !== textInput) {
            event.preventDefault();
            startListening();
        } else if (event.key === '0' || event.key === '0') {
            event.preventDefault();
            replaySpeech();
        } else if (event.key === 'Escape') {
            hideSettingsModal();
        }
    });
}



// Add smooth animations
function addSmoothAnimations() {
    // Add entrance animations
    const elements = document.querySelectorAll('.message, .mick-circle-container');
    elements.forEach((element, index) => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            element.style.transition = 'all 0.6s ease';
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        }, index * 200);
    });
}

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initSpeechRecognition();
    addCircleClickEvent();
    addTextInputEvents();
    addSendButtonEvent();
    addReplayClickEvent();
    addClearClickEvent();
    addSettingsClickEvent();
    addModalCloseEvent();
    addSettingsChangeEvents();
    addKeyboardShortcuts();
    addSmoothAnimations();
    createParticles();
    
    // Initialize textarea
    resizeTextarea();
    
    console.log('MICK AI Assistant initialized');
    console.log('Click the MICK circle to start listening');
    console.log('Press SPACE to start listening');
    console.log('Press ENTER to send message');
    console.log('Press 0 to replay');
    console.log('Press ESC to close modals');
});
