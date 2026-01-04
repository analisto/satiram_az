// ================================
// DOM Elements
// ================================
const inputText = document.getElementById('inputText');
const charCount = document.getElementById('charCount');
const maxLengthSlider = document.getElementById('maxLength');
const maxLengthValue = document.getElementById('maxLengthValue');
const synthesizeBtn = document.getElementById('synthesizeBtn');
const loadingState = document.getElementById('loadingState');
const resultSection = document.getElementById('resultSection');
const errorState = document.getElementById('errorState');
const resultImage = document.getElementById('resultImage');
const resultMeta = document.getElementById('resultMeta');
const errorText = document.getElementById('errorText');
const exampleBtns = document.querySelectorAll('.example-btn');
const downloadImageBtn = document.getElementById('downloadImageBtn');
const downloadAudioBtn = document.getElementById('downloadAudioBtn');
const audioElement = document.getElementById('audioElement');
const audioPlayerContainer = document.getElementById('audioPlayerContainer');

// ================================
// Event Listeners
// ================================

// Character count
inputText.addEventListener('input', () => {
    charCount.textContent = inputText.value.length;
});

// Slider value display
maxLengthSlider.addEventListener('input', () => {
    maxLengthValue.textContent = maxLengthSlider.value;
});

// Synthesize button
synthesizeBtn.addEventListener('click', async () => {
    await synthesizeSpeech();
});

// Example buttons
exampleBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const text = btn.dataset.text;
        inputText.value = text;
        charCount.textContent = text.length;

        // Smooth scroll to input
        inputText.scrollIntoView({ behavior: 'smooth', block: 'center' });
        inputText.focus();
    });
});

// Smooth scroll for nav links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Download buttons
downloadImageBtn.addEventListener('click', () => {
    downloadSpectrogram();
});

downloadAudioBtn.addEventListener('click', () => {
    downloadAudio();
});

// ================================
// Synthesis Function
// ================================
async function synthesizeSpeech() {
    const text = inputText.value.trim();

    // Validation
    if (!text) {
        showError('Please enter some text');
        return;
    }

    // Hide previous states
    resultSection.style.display = 'none';
    errorState.style.display = 'none';

    // Show loading
    loadingState.style.display = 'block';
    synthesizeBtn.disabled = true;

    try {
        const maxLength = parseInt(maxLengthSlider.value);

        // Make API request
        const response = await fetch('/api/synthesize/image', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                text: text,
                max_length: maxLength
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Synthesis failed');
        }

        // Get image blob
        const blob = await response.blob();
        const imageUrl = URL.createObjectURL(blob);

        // Display result
        resultImage.src = imageUrl;
        resultMeta.textContent = `Generated ${maxLength} frames`;

        // Generate audio in parallel
        generateAudio(text, maxLength);

        // Hide loading, show result
        loadingState.style.display = 'none';
        resultSection.style.display = 'block';

        // Smooth scroll to result
        setTimeout(() => {
            resultSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }, 100);

    } catch (error) {
        console.error('Synthesis error:', error);
        showError(error.message || 'An error occurred during synthesis');
    } finally {
        synthesizeBtn.disabled = false;
    }
}

// ================================
// Audio Generation
// ================================
async function generateAudio(text, maxLength) {
    try {
        console.log('Generating audio...');

        // Call audio endpoint
        const response = await fetch('/api/synthesize/audio', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                text: text,
                max_length: maxLength
            })
        });

        if (!response.ok) {
            throw new Error('Audio generation failed');
        }

        // Get audio blob
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);

        // Set audio source and show player
        audioElement.src = audioUrl;
        audioPlayerContainer.style.display = 'block';
        downloadAudioBtn.style.display = 'inline-flex';

        console.log('Audio generated successfully');

    } catch (error) {
        console.error('Audio generation error:', error);
        // Don't show error to user - image synthesis already succeeded
        // Just hide the audio player
        audioPlayerContainer.style.display = 'none';
        downloadAudioBtn.style.display = 'none';
    }
}

// ================================
// Error Handling
// ================================
function showError(message) {
    loadingState.style.display = 'none';
    resultSection.style.display = 'none';
    errorState.style.display = 'block';
    errorText.textContent = message;

    // Smooth scroll to error
    setTimeout(() => {
        errorState.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 100);
}

// ================================
// Keyboard Shortcuts
// ================================
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + Enter to synthesize
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        synthesizeSpeech();
    }
});

// ================================
// Initialize
// ================================
document.addEventListener('DOMContentLoaded', () => {
    console.log('Azerbaijani TTS App initialized');

    // Check API health
    fetch('/health')
        .then(response => response.json())
        .then(data => {
            console.log('API Health:', data);
            if (!data.model_loaded) {
                showError('Model is not loaded. Please check the server logs.');
            }
        })
        .catch(error => {
            console.error('Health check failed:', error);
            showError('Cannot connect to API server');
        });
});

// ================================
// Download Functionality
// ================================
function downloadSpectrogram() {
    const imgSrc = resultImage.src;
    if (!imgSrc || imgSrc === '') {
        showError('No spectrogram to download');
        return;
    }

    // Create download link
    const link = document.createElement('a');
    link.href = imgSrc;
    link.download = `azerbaijani_tts_spectrogram_${Date.now()}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function downloadAudio() {
    const audioSrc = audioElement.src;
    if (!audioSrc || audioSrc === '') {
        showError('No audio to download');
        return;
    }

    // Create download link
    const link = document.createElement('a');
    link.href = audioSrc;
    link.download = `azerbaijani_tts_audio_${Date.now()}.wav`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// ================================
// Utility Functions
// ================================
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
