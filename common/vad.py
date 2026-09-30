"""Simple Voice Activity Detection (VAD) using energy analysis.

Detects speech segments in audio by analyzing RMS energy levels.
Used to trim silence from recordings before transcription.
"""

import io
import struct
import wave
import numpy as np

# Energy thresholds (tuned for Yoruba speech)
ENERGY_THRESHOLD = 0.015  # Below this = silence
MIN_SPEECH_DURATION_MS = 300  # Minimum speech segment duration
MIN_SILENCE_DURATION_MS = 500  # Minimum silence to split segments
PRE_SPEECH_PADDING_MS = 200  # Add padding before speech starts
POST_SPEECH_PADDING_MS = 300  # Add padding after speech ends


def analyze_audio(audio_bytes: bytes, sample_rate: int = 16000) -> dict:
    """Analyze audio for voice activity.

    Returns:
        dict with:
            - segments: list of (start_ms, end_ms) tuples for speech segments
            - total_speech_ms: total duration of speech
            - total_silence_ms: total duration of silence
            - ratio: speech / total duration
    """
    try:
        # Try to read as WAV first
        if audio_bytes[:4] == b"RIFF":
            with wave.open(io.BytesIO(audio_bytes), "rb") as wf:
                frames = wf.readframes(wf.getnframes())
                sr = wf.getframerate()
                channels = wf.getnchannels()
                sampwidth = wf.getsampwidth()
        else:
            # Try to decode as raw PCM (assume 16-bit mono)
            frames = audio_bytes
            sr = sample_rate
            channels = 1
            sampwidth = 2

        # Convert to numpy array
        if sampwidth == 2:
            audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
        elif sampwidth == 4:
            audio = np.frombuffer(frames, dtype=np.int32).astype(np.float32) / 2147483648.0
        else:
            audio = np.frombuffer(frames, dtype=np.uint8).astype(np.float32) / 128.0 - 1.0

        if channels > 1:
            audio = audio.reshape(-1, channels)[:, 0]

    except Exception:
        return {
            "segments": [],
            "total_speech_ms": 0,
            "total_silence_ms": 0,
            "ratio": 0,
        }

    if len(audio) == 0:
        return {
            "segments": [],
            "total_speech_ms": 0,
            "total_silence_ms": 0,
            "ratio": 0,
        }

    # Frame-based energy analysis
    frame_ms = 20  # 20ms frames
    frame_size = int(sr * frame_ms / 1000)
    num_frames = len(audio) // frame_size

    energies = []
    for i in range(num_frames):
        frame = audio[i * frame_size : (i + 1) * frame_size]
        rms = np.sqrt(np.mean(frame ** 2))
        energies.append(rms)

    energies = np.array(energies)

    # Detect speech frames
    is_speech = energies > ENERGY_THRESHOLD

    # Find speech segments
    segments = []
    in_speech = False
    start = 0

    for i, speech in enumerate(is_speech):
        if speech and not in_speech:
            start = i
            in_speech = True
        elif not speech and in_speech:
            duration_ms = (i - start) * frame_ms
            if duration_ms >= MIN_SPEECH_DURATION_MS:
                start_ms = max(0, start * frame_ms - PRE_SPEECH_PADDING_MS)
                end_ms = i * frame_ms + POST_SPEECH_PADDING_MS
                segments.append((start_ms, end_ms))
            in_speech = False

    # Handle last segment
    if in_speech:
        duration_ms = (num_frames - start) * frame_ms
        if duration_ms >= MIN_SPEECH_DURATION_MS:
            start_ms = max(0, start * frame_ms - PRE_SPEECH_PADDING_MS)
            end_ms = num_frames * frame_ms + POST_SPEECH_PADDING_MS
            segments.append((start_ms, end_ms))

    # Merge close segments
    merged = []
    for seg in segments:
        if merged and seg[0] - merged[-1][1] < MIN_SILENCE_DURATION_MS:
            merged[-1] = (merged[-1][0], seg[1])
        else:
            merged.append(seg)

    total_ms = len(audio) / sr * 1000
    speech_ms = sum(end - start for start, end in merged)

    return {
        "segments": merged,
        "total_speech_ms": speech_ms,
        "total_silence_ms": total_ms - speech_ms,
        "ratio": speech_ms / total_ms if total_ms > 0 else 0,
    }


def trim_silence(audio_bytes: bytes, sample_rate: int = 16000) -> bytes:
    """Trim silence from audio, keeping only speech segments.

    Returns trimmed audio as WAV bytes.
    """
    try:
        with wave.open(io.BytesIO(audio_bytes), "rb") as wf:
            frames = wf.readframes(wf.getnframes())
            sr = wf.getframerate()
            channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
    except Exception:
        return audio_bytes

    analysis = analyze_audio(audio_bytes, sample_rate)
    if not analysis["segments"]:
        return audio_bytes

    # Convert segments to sample ranges
    audio = np.frombuffer(frames, dtype=np.int16)
    trimmed_parts = []

    for start_ms, end_ms in analysis["segments"]:
        start_sample = int(start_ms * sr / 1000)
        end_sample = int(end_ms * sr / 1000)
        end_sample = min(end_sample, len(audio))
        if start_sample < end_sample:
            trimmed_parts.append(audio[start_sample:end_sample])

    if not trimmed_parts:
        return audio_bytes

    trimmed = np.concatenate(trimmed_parts)

    # Write back as WAV
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(sr)
        wf.writeframes(trimmed.tobytes())

    return buf.getvalue()
