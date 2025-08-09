// Backend communication and processing functions

// Complete speech processing pipeline
async function processSpeechPipeline(spokenText, language) {
    try {
        updateStatus('Processing speech...');
        
        // Send to backend for processing
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

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        const data = await response.json();
        
        if (data.success) {
            // Add AI response to chat
            addMessage('ai', data.chatbot_response);
            
            // Store for replay
            chatbotResponse = data.chatbot_response;
            
            updateStatus('Processing complete!');
            updateUI('ready');
            showLoading(false);
            
            // Auto-speak the response if enabled
            if (autoSpeakEnabled) {
                speakText(data.chatbot_response, 'en-US');
            }
        } else {
            throw new Error(data.error || 'Processing failed');
        }
        
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
        showLoading(true);
        
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

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        const data = await response.json();
        
        if (data.success) {
            addMessage('ai', data.chatbot_response);
            chatbotResponse = data.chatbot_response;
            
            if (autoSpeakEnabled) {
                speakText(data.chatbot_response, 'en-US');
            }
        } else {
            throw new Error(data.error || 'Processing failed');
        }
        
        updateStatus('Ready');
        showLoading(false);
        
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
