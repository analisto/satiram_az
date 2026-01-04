"""
Vocoder for converting mel spectrograms to audio waveforms
Uses Griffin-Lim algorithm (built into librosa)
"""
import numpy as np
import librosa
import io
from scipy.io import wavfile


def mel_to_audio(mel_spectrogram, sample_rate=16000, n_fft=1024, hop_length=256, n_iter=32):
    """
    Convert mel spectrogram to audio waveform using Griffin-Lim algorithm

    Args:
        mel_spectrogram: Mel spectrogram (n_mels x time) in dB scale
        sample_rate: Audio sample rate (Hz)
        n_fft: FFT window size
        hop_length: Hop length for STFT
        n_iter: Number of Griffin-Lim iterations (more = better quality)

    Returns:
        audio: Audio waveform as numpy array
    """
    # Convert from dB scale back to power
    mel_spec_power = librosa.db_to_power(mel_spectrogram)

    # Convert mel spectrogram back to linear spectrogram
    stft = librosa.feature.inverse.mel_to_stft(
        mel_spec_power,
        sr=sample_rate,
        n_fft=n_fft,
        fmax=8000
    )

    # Use Griffin-Lim to reconstruct phase and get audio
    audio = librosa.griffinlim(
        stft,
        n_iter=n_iter,
        hop_length=hop_length,
        win_length=n_fft
    )

    # Normalize audio to prevent clipping
    audio = np.clip(audio, -1.0, 1.0)

    return audio


def audio_to_wav_bytes(audio, sample_rate=16000):
    """
    Convert audio waveform to WAV format bytes

    Args:
        audio: Audio waveform (numpy array)
        sample_rate: Sample rate in Hz

    Returns:
        wav_bytes: WAV file as bytes
    """
    # Convert float audio to int16
    audio_int16 = (audio * 32767).astype(np.int16)

    # Create WAV file in memory
    wav_io = io.BytesIO()
    wavfile.write(wav_io, sample_rate, audio_int16)
    wav_io.seek(0)

    return wav_io.getvalue()


def synthesize_audio_from_mel(mel_spectrogram, sample_rate=16000, n_fft=1024, hop_length=256):
    """
    Complete pipeline: mel spectrogram → audio waveform → WAV bytes

    Args:
        mel_spectrogram: Mel spectrogram (n_mels x time)
        sample_rate: Sample rate in Hz
        n_fft: FFT window size
        hop_length: Hop length

    Returns:
        wav_bytes: WAV file as bytes, ready to send to client
    """
    # Convert mel to audio
    audio = mel_to_audio(
        mel_spectrogram,
        sample_rate=sample_rate,
        n_fft=n_fft,
        hop_length=hop_length,
        n_iter=32  # Good balance between quality and speed
    )

    # Convert to WAV bytes
    wav_bytes = audio_to_wav_bytes(audio, sample_rate)

    return wav_bytes
