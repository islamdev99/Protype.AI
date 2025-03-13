
/**
 * Speech Processing for Protype.AI
 * Handles text-to-speech and speech-to-text functionality
 */

// DOM elements
const ttsAudio = document.getElementById('tts-audio');
const voiceSelect = document.getElementById('voice-select');
const sttLanguage = document.getElementById('stt-language');

// Speech state
let isRecording = false;
let mediaRecorder = null;
let audioChunks = [];
let availableVoices = [];

// Initialize speech functionality
function initSpeech() {
    // Load available voices
    loadVoices();
    
    // Set up voice input
    voiceInputButton.addEventListener('click', toggleVoiceInput);
    audioFeedback.addEventListener('click', stopVoiceInput);
    
    // Load settings from localStorage
    loadSpeechSettings();
}

// Play text-to-speech
function playTextToSpeech(text) {
    // Get selected voice ID
    const voiceId = voiceSelect.value;
    
    // Show loading indicator
    const audioButtons = document.querySelectorAll('.btn-audio');
    audioButtons.forEach(btn => {
        if (btn.dataset.text === text) {
            const icon = btn.querySelector('i');
            icon.className = 'fas fa-spinner fa-spin';
        }
    });
    
    // Request TTS from server
    fetch('/text-to-speech', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text, voice_id: voiceId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Play audio
            const audioSrc = `data:audio/mpeg;base64,${data.audio_base64}`;
            ttsAudio.src = audioSrc;
            ttsAudio.play();
            
            // Reset button icon
            audioButtons.forEach(btn => {
                if (btn.dataset.text === text) {
                    const icon = btn.querySelector('i');
                    icon.className = 'fas fa-volume-up';
                }
            });
        } else {
            console.error('Error generating speech:', data.message);
            
            // Reset button icon
            audioButtons.forEach(btn => {
                if (btn.dataset.text === text) {
                    const icon = btn.querySelector('i');
                    icon.className = 'fas fa-volume-up';
                }
            });
        }
    })
    .catch(error => {
        console.error('Error:', error);
        
        // Reset button icon
        audioButtons.forEach(btn => {
            if (btn.dataset.text === text) {
                const icon = btn.querySelector('i');
                icon.className = 'fas fa-volume-up';
            }
        });
    });
}

// Toggle voice input
function toggleVoiceInput() {
    if (isRecording) {
        stopVoiceInput();
    } else {
        startVoiceInput();
    }
}

// Start voice recording
function startVoiceInput() {
    // Check if recording is supported
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        alert('Your browser does not support voice recording.');
        return;
    }
    
    // Request microphone access
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            // Show recording UI
            audioFeedback.style.display = 'block';
            voiceInputButton.classList.add('btn-danger');
            isRecording = true;
            
            // Initialize recorder
            audioChunks = [];
            mediaRecorder = new MediaRecorder(stream);
            
            // Handle recorded data
            mediaRecorder.addEventListener('dataavailable', event => {
                audioChunks.push(event.data);
            });
            
            // Handle recording stop
            mediaRecorder.addEventListener('stop', () => {
                // Process recorded audio
                processRecordedAudio();
                
                // Stop all tracks
                stream.getTracks().forEach(track => track.stop());
            });
            
            // Start recording
            mediaRecorder.start();
        })
        .catch(error => {
            console.error('Error accessing microphone:', error);
            alert('Error accessing microphone. Please check your permissions.');
        });
}

// Stop voice recording
function stopVoiceInput() {
    if (!isRecording || !mediaRecorder) return;
    
    // Stop recording
    mediaRecorder.stop();
    
    // Hide recording UI
    audioFeedback.style.display = 'none';
    voiceInputButton.classList.remove('btn-danger');
    isRecording = false;
}

// Process recorded audio
function processRecordedAudio() {
    if (audioChunks.length === 0) return;
    
    // Create audio blob
    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
    
    // Create form data for upload
    const formData = new FormData();
    formData.append('audio', audioBlob);
    formData.append('language', sttLanguage.value);
    
    // Show processing indicator in chat input
    chatInput.setAttribute('disabled', 'disabled');
    chatInput.setAttribute('placeholder', 'Processing speech...');
    
    // Send to server for speech-to-text processing
    fetch('/speech-to-text', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Set recognized text to input
            chatInput.value = data.text;
            
            // Send message if it's valid
            if (data.text.trim() !== '') {
                sendMessage();
            }
        } else {
            console.error('Error recognizing speech:', data.message);
            alert('Could not recognize speech. Please try again.');
        }
        
        // Reset chat input
        chatInput.removeAttribute('disabled');
        chatInput.setAttribute('placeholder', 'Type your message here...');
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error processing speech. Please try again.');
        
        // Reset chat input
        chatInput.removeAttribute('disabled');
        chatInput.setAttribute('placeholder', 'Type your message here...');
    });
}

// Load available voices
function loadVoices() {
    fetch('/voices')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Store available voices
                availableVoices = data.voices;
                
                // Clear loading option
                voiceSelect.innerHTML = '';
                
                // Add voices to select
                availableVoices.forEach(voice => {
                    const option = document.createElement('option');
                    option.value = voice.voice_id;
                    option.textContent = voice.name;
                    voiceSelect.appendChild(option);
                });
                
                // Set selected voice from settings
                const savedVoice = localStorage.getItem('protype_tts_voice');
                if (savedVoice) {
                    voiceSelect.value = savedVoice;
                }
            } else {
                console.error('Error loading voices:', data.message);
                
                // Add default option
                const option = document.createElement('option');
                option.value = '21m00Tcm4TlvDq8ikWAM';
                option.textContent = 'Default Voice';
                voiceSelect.appendChild(option);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            
            // Add default option
            const option = document.createElement('option');
            option.value = '21m00Tcm4TlvDq8ikWAM';
            option.textContent = 'Default Voice';
            voiceSelect.appendChild(option);
        });
}

// Load speech settings from localStorage
function loadSpeechSettings() {
    // Load voice selection
    const savedVoice = localStorage.getItem('protype_tts_voice');
    if (savedVoice) {
        voiceSelect.value = savedVoice;
    }
    
    // Load auto TTS setting
    const autoTTS = localStorage.getItem('protype_auto_tts');
    document.getElementById('auto-tts-switch').checked = autoTTS === 'true';
    
    // Load STT language
    const savedLanguage = localStorage.getItem('protype_stt_language');
    if (savedLanguage) {
        sttLanguage.value = savedLanguage;
    }
}

// Save speech settings to localStorage
function saveSpeechSettings() {
    localStorage.setItem('protype_tts_voice', voiceSelect.value);
    localStorage.setItem('protype_auto_tts', document.getElementById('auto-tts-switch').checked);
    localStorage.setItem('protype_stt_language', sttLanguage.value);
}

// Add save settings listener
document.getElementById('save-settings-btn').addEventListener('click', function() {
    saveSpeechSettings();
    alert('Settings saved successfully!');
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', initSpeech);
