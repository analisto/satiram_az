"""
FastAPI Backend for Azerbaijani TTS
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import torch
import pickle
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import io
from pathlib import Path
import logging

from .model import SimpleTTS, synthesize_speech, CharacterEncoder
from .vocoder import synthesize_audio_from_mel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Azerbaijani TTS API",
    description="Text-to-Speech synthesis for Azerbaijani language",
    version="1.0.0"
)

# Setup paths
BASE_DIR = Path(__file__).parent.parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"
STATIC_DIR = BASE_DIR / "app" / "static"
TEMPLATES_DIR = BASE_DIR / "app" / "templates"

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Setup templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Global model variables
model = None
char_encoder = None
device = torch.device('cpu')


class SynthesisRequest(BaseModel):
    """Request model for synthesis"""
    text: str
    max_length: int = 300


class SynthesisResponse(BaseModel):
    """Response model for synthesis"""
    success: bool
    message: str
    mel_shape: tuple = None


@app.on_event("startup")
async def load_model():
    """Load model and encoder on startup"""
    global model, char_encoder

    try:
        logger.info("Loading TTS model...")

        # Load character encoder with custom unpickler to handle module path
        encoder_path = ARTIFACTS_DIR / "char_encoder.pkl"

        # Custom unpickler to remap __main__ to app.model
        import sys
        import app.model
        sys.modules['__main__'].CharacterEncoder = CharacterEncoder

        with open(encoder_path, 'rb') as f:
            char_encoder = pickle.load(f)
        logger.info(f"Character encoder loaded: {char_encoder.vocab_size} chars")

        # Initialize model
        model = SimpleTTS(vocab_size=char_encoder.vocab_size, n_mels=80)

        # Load trained weights
        model_path = ARTIFACTS_DIR / "best_model.pt"
        checkpoint = torch.load(model_path, map_location=device)
        model.load_state_dict(checkpoint['model_state_dict'])
        model.to(device)
        model.eval()

        logger.info(f"Model loaded successfully (epoch {checkpoint['epoch'] + 1})")
        logger.info(f"Validation loss: {checkpoint['val_loss']:.4f}")

    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise


@app.get("/")
async def home(request: Request):
    """Render home page"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": "Azerbaijani TTS",
    })


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "vocab_size": char_encoder.vocab_size if char_encoder else None
    }


@app.post("/api/synthesize", response_model=SynthesisResponse)
async def synthesize(request: SynthesisRequest):
    """
    Synthesize speech from text

    Args:
        request: SynthesisRequest containing text

    Returns:
        SynthesisResponse with success status
    """
    if not model or not char_encoder:
        raise HTTPException(status_code=503, detail="Model not loaded")

    if not request.text or len(request.text.strip()) == 0:
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    try:
        logger.info(f"Synthesizing: {request.text[:50]}...")

        # Synthesize
        mel_spectrogram = synthesize_speech(
            text=request.text,
            model=model,
            char_encoder=char_encoder,
            device=device,
            max_len=request.max_length
        )

        logger.info(f"Generated mel spectrogram: {mel_spectrogram.shape}")

        return SynthesisResponse(
            success=True,
            message="Synthesis completed successfully",
            mel_shape=mel_spectrogram.shape
        )

    except Exception as e:
        logger.error(f"Synthesis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {str(e)}")


@app.post("/api/synthesize/image")
async def synthesize_image(request: SynthesisRequest):
    """
    Synthesize speech and return mel spectrogram as image

    Args:
        request: SynthesisRequest containing text

    Returns:
        PNG image of mel spectrogram
    """
    if not model or not char_encoder:
        raise HTTPException(status_code=503, detail="Model not loaded")

    if not request.text or len(request.text.strip()) == 0:
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    try:
        logger.info(f"Synthesizing image for: {request.text[:50]}...")

        # Synthesize
        mel_spectrogram = synthesize_speech(
            text=request.text,
            model=model,
            char_encoder=char_encoder,
            device=device,
            max_len=request.max_length
        )

        # Create visualization
        plt.figure(figsize=(12, 4))
        plt.imshow(mel_spectrogram, aspect='auto', origin='lower', cmap='viridis')
        plt.colorbar(label='dB', format='%+2.0f')
        plt.xlabel('Time Frames', fontsize=12)
        plt.ylabel('Mel Frequency Bands', fontsize=12)
        plt.title(f'Synthesized Mel Spectrogram\n"{request.text}"', fontsize=13, fontweight='bold', pad=15)
        plt.tight_layout()

        # Save to bytes
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        plt.close()
        buf.seek(0)

        return StreamingResponse(buf, media_type="image/png")

    except Exception as e:
        logger.error(f"Image synthesis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {str(e)}")


@app.post("/api/synthesize/audio")
async def synthesize_audio(request: SynthesisRequest):
    """
    Synthesize speech and return as WAV audio file

    Args:
        request: SynthesisRequest containing text

    Returns:
        WAV audio file
    """
    if not model or not char_encoder:
        raise HTTPException(status_code=503, detail="Model not loaded")

    if not request.text or len(request.text.strip()) == 0:
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    try:
        logger.info(f"Synthesizing audio for: {request.text[:50]}...")

        # Generate mel spectrogram
        mel_spectrogram = synthesize_speech(
            text=request.text,
            model=model,
            char_encoder=char_encoder,
            device=device,
            max_len=request.max_length
        )

        logger.info(f"Generated mel spectrogram: {mel_spectrogram.shape}")

        # Convert mel spectrogram to audio
        wav_bytes = synthesize_audio_from_mel(
            mel_spectrogram,
            sample_rate=16000,
            n_fft=1024,
            hop_length=256
        )

        logger.info(f"Generated audio: {len(wav_bytes)} bytes")

        # Return as WAV file
        return StreamingResponse(
            io.BytesIO(wav_bytes),
            media_type="audio/wav",
            headers={
                "Content-Disposition": f"attachment; filename=azerbaijani_tts_{request.text[:20]}.wav"
            }
        )

    except Exception as e:
        logger.error(f"Audio synthesis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Audio synthesis failed: {str(e)}")


@app.get("/api/stats")
async def get_stats():
    """Get model statistics"""
    if not model:
        raise HTTPException(status_code=503, detail="Model not loaded")

    total_params = sum(p.numel() for p in model.parameters())

    return {
        "model_architecture": "Seq2Seq with Attention",
        "total_parameters": total_params,
        "vocab_size": char_encoder.vocab_size,
        "n_mels": 80,
        "device": str(device),
        "max_text_length": 200,
        "vocoder": "Griffin-Lim (librosa)"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
