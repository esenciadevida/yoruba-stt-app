import os
import tempfile
import logging
import numpy as np
from transformers import pipeline
import torch
import librosa
import streamlit as st

logger = logging.getLogger(__name__)

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "yoruba_model")

# Audio quality thresholds
MIN_RMS = 0.005
MAX_RMS = 0.95
SILENCE_THRESHOLD = 0.01
CLIPPING_THRESHOLD = 0.99

@st.cache_resource
def load_model():

    device = 0 if torch.cuda.is_available() else -1

    pipe = pipeline(
        "automatic-speech-recognition",
        model=MODEL_PATH,
        device=device
    )

    return pipe


def analyze_audio_quality(audio, sr=16000):
    """Analyze audio quality: RMS energy, silence, clipping, duration."""
    duration_sec = len(audio) / sr
    rms = float(np.sqrt(np.mean(audio ** 2)))
    clipped_fraction = float(np.mean(np.abs(audio) >= CLIPPING_THRESHOLD))
    is_silent = rms < SILENCE_THRESHOLD

    chunk_size = sr
    energies = []
    for i in range(0, len(audio), chunk_size):
        chunk = audio[i:i + chunk_size]
        if len(chunk) > 0:
            energies.append(float(np.sqrt(np.mean(chunk ** 2))))

    silent_segments = sum(1 for e in energies if e < SILENCE_THRESHOLD)

    quality = {
        "duration_sec": round(duration_sec, 2),
        "rms_energy": round(rms, 4),
        "is_silent": is_silent,
        "is_clipped": clipped_fraction > 0.01,
        "warnings": [],
    }

    if is_silent:
        quality["warnings"].append("Audio is silent or too quiet. Try speaking closer to the microphone.")
    elif rms < MIN_RMS:
        quality["warnings"].append("Audio volume is very low. Try speaking louder or closer to the mic.")
    elif rms > MAX_RMS:
        quality["warnings"].append("Audio may be too loud or distorted.")

    if quality["is_clipped"]:
        quality["warnings"].append("Audio is clipping (distorted). Try reducing your recording volume.")

    if duration_sec < 0.5:
        quality["warnings"].append("Audio is very short. Try recording a longer phrase.")
    elif duration_sec > 60:
        quality["warnings"].append("Audio is very long. Consider recording shorter segments for better accuracy.")

    if silent_segments > len(energies) * 0.5 and len(energies) > 1:
        quality["warnings"].append("More than half the audio is silent. Check your recording environment.")

    return quality


def _compute_confidence(model, audio):
    """Compute overall confidence and per-token confidence from model logits."""
    try:
        device = next(model.model.parameters()).device if hasattr(model, 'model') else torch.device('cpu')
        inputs = model.preprocessor(audio, return_tensors="pt", sampling_rate=16000)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = model.model(**inputs)
            logits = outputs.logits
        probs = torch.softmax(logits, dim=-1)
        max_probs = probs.max(dim=-1).values
        avg_confidence = max_probs.mean().item()
        token_confidences = max_probs[0].cpu().tolist()
        return max(0.0, min(1.0, avg_confidence)), token_confidences
    except Exception:
        return 0.0, []


def _tokens_to_words(text, token_confidences):
    """Map token-level confidences to word-level confidences."""
    if not token_confidences or not text:
        return []
    words = text.split()
    if not words:
        return []
    n_tokens = len(token_confidences)
    n_words = len(words)
    total_chars = sum(len(w) for w in words)
    result = []
    token_idx = 0
    for word in words:
        char_ratio = len(word) / max(total_chars, 1)
        n_tokens_for_word = max(1, round(char_ratio * n_tokens))
        start = token_idx
        end = min(token_idx + n_tokens_for_word, n_tokens)
        if start < end:
            word_conf = sum(token_confidences[start:end]) / (end - start)
        else:
            word_conf = token_confidences[min(token_idx, n_tokens - 1)]
        result.append({"word": word, "confidence": round(word_conf, 4)})
        token_idx = end
    return result


def transcribe_audio(model, audio_path):

    audio, sr = librosa.load(audio_path, sr=16000)

    quality = analyze_audio_quality(audio, sr)

    result = model(audio)

    confidence, token_confidences = _compute_confidence(model, audio)
    word_confidences = _tokens_to_words(result["text"], token_confidences)

    return {
        "text": result["text"],
        "confidence": confidence,
        "word_confidences": word_confidences,
        "quality": quality,
        "engine": "w2v-bert-2.0-yoruba",
    }


def transcribe_audio_bytes(model, audio_bytes, filename=None, language="yo"):
    """Transcribe audio bytes, preferring OpenAI (gpt-4o-transcribe / whisper-1)
    when an API key is configured. Falls back to the local W2V-BERT model.

    Returns the same dict shape as :func:`transcribe_audio`. Cloud results have
    ``confidence`` 0.0 and no per-word confidence / quality breakdown.
    """
    try:
        from common.transcription_api import transcribe_with_openai
    except Exception as e:
        logger.warning("Could not import cloud transcription: %s", e)
        transcribe_with_openai = None

    if transcribe_with_openai is not None:
        try:
            result = transcribe_with_openai(audio_bytes, filename or "recording.wav", language=language)
            if result is not None:
                return {
                    "text": result["text"],
                    "confidence": 0.0,
                    "word_confidences": [],
                    "quality": None,
                    "engine": result["engine"],
                }
        except Exception as e:
            logger.warning("OpenAI transcription failed, using local model: %s", e)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        return transcribe_audio(model, tmp_path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)