import os
import subprocess
import tempfile
import logging
import sys
import librosa
import numpy as np
from config import OPENAI_API_KEY

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

logger = logging.getLogger(__name__)

_model = None
_whisper_model = None

NON_WAV_TYPES = {"audio/webm", "audio/ogg", "audio/flac"}


def _base_content_type(ct: str) -> str:
    return (ct or "").split(";")[0].strip().lower()

MIN_RMS = 0.005
MAX_RMS = 0.95
SILENCE_THRESHOLD = 0.01
CLIPPING_THRESHOLD = 0.99

# Chunking parameters (tuned to help fast / continuous speech)
# Fast speakers compress many syllables into short windows; long no-pause runs
# cause ASR models (CTC local models especially, but also API models) to drop
# content. We split audio into manageable chunks and merge results.
MAX_CHUNK_SEC = 18.0        # longest single chunk we send to any model (sec)
TARGET_CHUNK_SEC = 14.0     # preferred chunk length (sec)
CHUNK_OVERLAP_SEC = 1.0     # context overlap across hard time-based cuts (sec)
MIN_SPLIT_SEC = 3.0         # only split segments longer than this

# Confidence-gated retry: re-transcribe once if the API result falls below this,
# since fast speech occasionally produces a low-confidence (garbled) first pass.
RETRY_LOW_CONFIDENCE_THRESHOLD = 0.55

# Request-level retry + exponential backoff for transient OpenAI failures
# (rate limits, 5xx, timeouts, connection errors). Permanent errors (400/401/404)
# are never retried so the engine fallback fires immediately.
OPENAI_RETRY_ATTEMPTS = 3
OPENAI_RETRY_BASE_DELAY = 0.8
OPENAI_RETRY_MAX_DELAY = 6.0
_TRANSIENT_STATUS_CODES = {429, 500, 501, 502, 503, 504}


def _transcribe_with_retry(call_fn, label: str = "openai"):
    """Call `call_fn()` (one OpenAI transcription request) with retry + backoff.

    Transient failures (`status_code` in the 429/5xx set, or no status code at
    all, i.e. timeout/connection-level errors) are retried up to
    OPENAI_RETRY_ATTEMPTS times with exponential delay. Permanent HTTP errors
    (400/401/404/...) raise immediately so the engine cascade can fall back.
    """
    import time as _time
    delay = OPENAI_RETRY_BASE_DELAY
    last_exc = None
    for attempt in range(1, OPENAI_RETRY_ATTEMPTS + 1):
        try:
            return call_fn()
        except Exception as e:  # openai surfaces several error shapes
            code = getattr(e, "status_code", None)
            if code is not None and code not in _TRANSIENT_STATUS_CODES:
                raise
            last_exc = e
            if attempt == OPENAI_RETRY_ATTEMPTS:
                break
            logger.warning(
                "%s transient failure (attempt %d/%d): %s; retrying in %.1fs",
                label, attempt, OPENAI_RETRY_ATTEMPTS, e, delay,
            )
            _time.sleep(delay)
            delay = min(delay * 2, OPENAI_RETRY_MAX_DELAY)
    raise last_exc


def load_stt_model():
    global _model
    if _model is None:
        from transformers import pipeline
        import torch
        model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "yoruba_model"))
        device = 0 if torch.cuda.is_available() else -1
        _model = pipeline("automatic-speech-recognition", model=model_path, device=device)
    return _model


def load_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "yoruba_whisper_model"))
        if not os.path.exists(os.path.join(model_path, "config.json")):
            return None
        try:
            from transformers import WhisperProcessor, WhisperForConditionalGeneration
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            processor = WhisperProcessor.from_pretrained(model_path)
            model = WhisperForConditionalGeneration.from_pretrained(model_path).to(device)
            _whisper_model = {"processor": processor, "model": model, "device": device}
            logger.info("Loaded yoruba_whisper_model from %s", model_path)
        except Exception as e:
            logger.warning("Failed to load whisper model: %s", e)
            return None
    return _whisper_model


def convert_to_wav(input_path: str) -> str:
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.close()
    subprocess.run(
        ["ffmpeg", "-y", "-i", input_path, "-ar", "16000", "-ac", "1", tmp.name],
        capture_output=True, check=True,
    )
    return tmp.name


def analyze_audio_quality(audio: np.ndarray, sr: int = 16000) -> dict:
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
        "clipped_fraction": round(clipped_fraction, 4),
        "silent_segments": silent_segments,
        "total_segments": len(energies),
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


def _vad_segments_ms(audio: np.ndarray, sr: int) -> list:
    """Return speech segments (start_ms, end_ms) using the shared VAD."""
    try:
        import io
        import soundfile as sf
        from common.vad import analyze_audio

        buf = io.BytesIO()
        sf.write(buf, audio, sr, format="WAV")
        return analyze_audio(buf.getvalue(), sr).get("segments", [])
    except Exception:
        return []


def _split_range(start_sec: float, end_sec: float, target_sec: float, overlap_sec: float) -> list:
    """Split [start_sec, end_sec] into sub-ranges with overlap at boundaries.

    Returns a list of (start_sec, end_sec) tuples. Each sub-range is at most
    `target_sec` long, and consecutive sub-ranges share `overlap_sec` of audio
    so the context around a cut is preserved.
    """
    chunks = []
    cursor = start_sec
    while cursor < end_sec:
        chunk_end = min(cursor + target_sec, end_sec)
        # Only add overlap to really-adjacent cuts (not the very first chunk).
        chunk_start = max(cursor, start_sec)
        chunks.append((chunk_start, chunk_end))
        if chunk_end >= end_sec:
            break
        # Step forward by (target - overlap) so next chunk overlaps this one.
        step = max(1.0, target_sec - overlap_sec)
        cursor = chunk_end - overlap_sec
    return chunks


def segment_audio_for_asr(
    audio: np.ndarray,
    sr: int,
    max_chunk_sec: float = MAX_CHUNK_SEC,
    target_chunk_sec: float = TARGET_CHUNK_SEC,
    overlap_sec: float = CHUNK_OVERLAP_SEC,
) -> list:
    """Segment an array into (start_sample, end_sample) chunks for ASR.

    Prefers natural VAD pause boundaries; any segment still longer than
    `max_chunk_sec` (e.g. fast continuous speech with no pauses) is split by
    time into ~`target_chunk_sec` chunks with `overlap_sec` of context.
    """
    total_sec = len(audio) / sr
    if total_sec <= max_chunk_sec:
        return [(0, len(audio))]

    vad = _vad_segments_ms(audio, sr)
    if not vad:
        vad = [(0.0, total_sec * 1000.0)]

    # Build raw (sec) ranges from VAD segments. Do NOT drop short segments --
    # a short final phrase (or any short utterance separated by a pause) is real
    # content; dropping it would stop the transcription before the end.
    raw_ranges = []
    for start_ms, end_ms in vad:
        start_sec = max(0.0, start_ms / 1000.0)
        end_sec = min(total_sec, end_ms / 1000.0)
        if end_sec > start_sec:
            raw_ranges.append((start_sec, end_sec))

    if not raw_ranges:
        raw_ranges = [(0.0, total_sec)]

    # Merge very short segments into a neighbor so we never lose their words
    # and don't create tiny fragmented chunks (each keeps its own duration).
    merged_ranges = []
    for start_sec, end_sec in raw_ranges:
        if merged_ranges:
            prev_start, prev_end = merged_ranges[-1]
            # Short segment: fold into the previous range.
            if end_sec - start_sec < MIN_SPLIT_SEC:
                merged_ranges[-1] = (prev_start, end_sec)
                continue
            # Also absorb a tiny gap (< 500ms) into the previous range so we
            # don't carve out content at the boundary.
            if start_sec - prev_end < 0.5:
                merged_ranges[-1] = (prev_start, end_sec)
                continue
        merged_ranges.append((start_sec, end_sec))
    raw_ranges = merged_ranges

    # Guard against a single tiny leftover range being dropped by the splitter.
    raw_ranges = [r for r in raw_ranges if r[1] > r[0]]

    out = []
    for start_sec, end_sec in raw_ranges:
        duration = end_sec - start_sec
        if duration <= max_chunk_sec:
            out.append((start_sec, end_sec))
            continue
        for cs, ce in _split_range(start_sec, end_sec, target_chunk_sec, overlap_sec):
            out.append((cs, ce))

    # Sanitize and sort
    result = []
    for start_sec, end_sec in out:
        s = max(0, int(round(start_sec * sr)))
        e = min(len(audio), int(round(end_sec * sr)))
        if s < e:
            result.append((s, e))
    return result


def _strip_overlap(text: str, overlap_sec: float, sr: int) -> str:
    """Roughly remove ~overlap of audio that likely duplicated previous chunk.

    With ~overlap_sec of context, roughly a fraction of the chunk text is a
    repeat of the previous chunk's tail. We drop the first `overlap_sec` worth
    of words (approximated by speaking rate) when merging non-timestamped
    results.
    """
    words = text.split()
    if not words:
        return ""
    # ~2.5 words per second is a reasonable fast-speech speaking rate.
    words_to_drop = max(1, int(round(overlap_sec * 2.5)))
    if len(words) <= words_to_drop + 1:
        return text
    return " ".join(words[words_to_drop:])


def _merge_chunk_texts(chunks: list, use_timestamps: bool = False) -> str:
    """Merge per-chunk transcriptions, de-duplicating overlap regions.

    `chunks` is a list of (text, word_timestamps) where word_timestamps is
    either a list of {"word": str, "start": float, "end": float} or None.
    """
    if not chunks:
        return ""
    if len(chunks) == 1:
        return chunks[0][0]

    parts = [chunks[0][0]]

    for i in range(1, len(chunks)):
        text, words = chunks[i]

        if words:
            # Word-timestamped chunk: find the boundary word to keep.
            # Use overlap_sec to estimate how far into the chunk the repeat ends.
            overlap_sec = CHUNK_OVERLAP_SEC
            overlap_end = overlap_sec * 1000.0  # ms
            keep_from = 0
            for j, w in enumerate(words):
                if ("start" in w and w["start"] * 1000.0) >= overlap_end:
                    keep_from = j
                    break
            kept_words = [w["word"] for w in words[keep_from:]]
            if kept_words:
                parts.append(" ".join(kept_words))
            else:
                parts.append(text)
        else:
            parts.append(_strip_overlap(text, CHUNK_OVERLAP_SEC, 16000))

    return " ".join(p for p in parts if p)


def _word_confidences_from_segments(segments: list) -> list:
    """Flatten whisper-style word segments into word entries for merging.

    Each entry carries the word, its start time (seconds, relative to chunk
    start) so overlap regions can be de-duplicated, and a confidence score.
    """
    out = []
    for seg in segments:
        for w in getattr(seg, "words", []) or []:
            out.append({
                "word": getattr(w, "word", ""),
                "start": float(getattr(w, "start", 0.0)),
                "end": float(getattr(w, "end", 0.0)),
                "confidence": round(getattr(w, "probability", 0.9), 4),
            })
    return out


def _should_retry(result: dict) -> bool:
    """Return True when a result is low-confidence enough to warrant a retry."""
    conf = result.get("confidence")
    if conf is None:
        return False
    text = (result.get("text") or "").strip()
    # Don't retry trivial/short inputs at all.
    if len(text) < 1 or len(text.split()) < 2:
        return False
    return conf < RETRY_LOW_CONFIDENCE_THRESHOLD


def _build_prompt(base_prompt: str, custom_vocabulary: str, is_retry: bool) -> str:
    """Compose the effective ASR prompt with optional user glossary + retry nudge."""
    prompt = base_prompt
    if custom_vocabulary and custom_vocabulary.strip():
        prompt += (
            "\nThe speaker frequently says these words. When heard, transcribe with "
            "these exact spellings (do not translate, do not substitute synonyms): "
            + custom_vocabulary.strip()
        )
    if is_retry:
        prompt += (
            "\nYou may have made errors. Transcribe carefully, word by word; do not "
            "add or omit words, and preserve every spoken word exactly."
        )
    return prompt


def _compute_confidence(model, audio) -> tuple:
    import torch
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


def _tokens_to_words(text: str, token_confidences: list) -> list:
    if not token_confidences or not text:
        return []
    words = text.split()
    if not words:
        return []
    n_tokens = len(token_confidences)
    n_words = len(words)
    if n_words == 0:
        return []
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


def _high_pass_filter(audio: np.ndarray, sr: int, cutoff: int = 80) -> np.ndarray:
    """Remove low-frequency rumble below cutoff Hz using a simple Butterworth filter."""
    try:
        from scipy.signal import butter, sosfilt
        nyq = sr / 2
        normalized_cutoff = cutoff / nyq
        sos = butter(4, normalized_cutoff, btype="high", output="sos")
        return sosfilt(sos, audio).astype(np.float32)
    except ImportError:
        return audio


def _trim_preserving_gaps(audio: np.ndarray, sr: int, vad_segments: list) -> np.ndarray:
    """Trim leading/trailing silence and long pauses WITHOUT cutting real words.

    The naive approach concatenates speech segments, which deletes short
    inter-word pauses and clips the attack/release of tonal consonants at every
    boundary -- damaging fast Yoruba speech. Instead we:

      * Decide how to treat each gap from the RAW VAD boundaries (before any
        padding), so real word-internal pauses are never mistaken for long ones.
      * Keep short gaps (<=350ms) exactly as recorded (real word pauses).
      * Shorten only genuinely LONG interior silences (>=700ms, a pause the
        speaker made) down to a small ~120ms gap the model can still interpret
        as a word boundary.
      * Add a little padding only at the very first/last segment outer edges.

    `vad_segments` is a list of (start_ms, end_ms) speech segments.
    """
    if not vad_segments:
        return audio

    PRE_PAD_MS = 150   # leading breathing room before first word
    POST_PAD_MS = 250  # trailing room after last word
    GAP_PRESERVE_MS = 350   # gaps <= this are word-internal pauses: keep fully
    GAP_COLLAPSE_MS = 700   # gaps >= this are long speaker pauses: shorten
    SHORT_GAP_MS = 120      # silence to insert where a long pause is shortened

    total_ms = len(audio) / sr * 1000.0

    # Raw (unpadded) segment sample ranges.
    raw = []
    for start_ms, end_ms in vad_segments:
        s = int(min(total_ms, max(0.0, start_ms)) * sr / 1000.0)
        e = int(min(total_ms, max(0.0, end_ms)) * sr / 1000.0)
        e = min(e, len(audio))
        if s < e:
            raw.append((s, e))

    if not raw:
        return audio

    out_parts = []
    first_s, first_e = raw[0]
    # Outer leading padding for the first segment (never cuts into the word).
    seg_start = int(max(0, first_s - PRE_PAD_MS * sr / 1000.0))
    out_parts.append(audio[seg_start:first_e])

    for i in range(len(raw) - 1):
        _, e = raw[i]
        next_s, next_e = raw[i + 1]
        gap_ms = (next_s - e) * 1000.0 / sr
        # The gap between this segment's raw end and the next's raw start.
        if gap_ms < GAP_PRESERVE_MS:
            # Real word-internal pause: keep it exactly as recorded.
            out_parts.append(audio[e:next_s])
        elif gap_ms >= GAP_COLLAPSE_MS:
            # Long speaker pause: replace with a short boundary silence.
            n = max(1, int(SHORT_GAP_MS * sr / 1000.0))
            out_parts.append(np.zeros(n, dtype=audio.dtype))
        else:
            # Medium pause: keep a portion (scale toward SHORT_GAP_MS).
            keep_samples = int(min(gap_ms, max(SHORT_GAP_MS, gap_ms * 0.4)) * sr / 1000.0)
            keep_samples = max(1, keep_samples)
            out_parts.append(audio[e:e + keep_samples])

        # The speech segment itself (actual word audio) -- must NOT be dropped.
        out_parts.append(audio[next_s:next_e])

    # Outer trailing padding for the last segment.
    last_s, last_e = raw[-1]
    last_end = int(min(len(audio), last_e + POST_PAD_MS * sr / 1000.0))
    out_parts.append(audio[last_e:last_end])

    return np.concatenate(out_parts) if len(out_parts) > 1 else out_parts[0]


def preprocess_audio_for_asr(input_path: str) -> str:
    """Trim silence, normalize loudness, return clean 16kHz mono WAV.

    Uses VAD-based silence trimming that PRESERVES short inter-word pauses so
    fast Yoruba speech keeps its word boundaries, followed by normalization.
    """
    try:
        audio, sr = librosa.load(input_path, sr=16000, mono=True)
    except Exception:
        return input_path

    if len(audio) == 0:
        return input_path

    # Gentle high-pass filter to remove low-frequency rumble only (kept low to preserve tonal cues)
    audio = _high_pass_filter(audio, sr, cutoff=40)

    # VAD-based silence handling
    try:
        from common.vad import analyze_audio
        import soundfile as sf

        tmp_vad = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp_vad.close()
        sf.write(tmp_vad.name, audio, sr)

        with open(tmp_vad.name, "rb") as f:
            vad_audio = f.read()
        os.remove(tmp_vad.name)

        vad_result = analyze_audio(vad_audio, sr)
        segments = vad_result.get("segments", [])
        if segments and vad_result.get("ratio", 0) > 0.3:
            trimmed = _trim_preserving_gaps(audio, sr, segments)
            if len(trimmed) > 0.2 * sr:
                audio = trimmed
                logger.info("VAD trimmed audio preserving word-boundary pauses "
                           "(%d segments, %.0f%% speech ratio)",
                           len(segments), vad_result["ratio"] * 100)
        elif segments:
            # Meaningful speech but low ratio: still trim outer edges safely.
            trimmed = _trim_preserving_gaps(audio, sr, segments)
            if len(trimmed) > 0.2 * sr:
                audio = trimmed
    except Exception as e:
        logger.debug("VAD analysis skipped: %s", e)
        # Fall back to trimming only the outer silence (never cut words inside).
        try:
            trimmed, _ = librosa.effects.trim(audio, top_db=28, frame_length=1024, hop_length=256)
            if len(trimmed) > 0.25 * sr:
                audio = trimmed
        except Exception:
            pass

    # Normalize loudness to consistent level
    rms = float(np.sqrt(np.mean(audio ** 2)))
    target_rms = 0.10
    if rms > 0:
        gain = target_rms / rms
        gain = min(max(gain, 0.5), 3.0)
        audio = audio * gain

    # Soft clip to prevent distortion
    peak = float(np.max(np.abs(audio)))
    if peak > 0.95:
        audio = audio / peak * 0.9

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.close()
    import soundfile as sf
    sf.write(tmp.name, audio, 16000)
    return tmp.name


def _estimate_gpt_confidence(text: str, word_confidences: list) -> float:
    """Estimate confidence from transcription characteristics when API doesn't provide it."""
    if not text or not text.strip():
        return 0.0

    score = 0.92

    words = text.split()
    if len(words) == 0:
        return 0.5

    # Yoruba tone marks indicate high quality
    yoruba_diacritics = sum(1 for c in text if ord(c) > 0x024F)
    tone_ratio = yoruba_diacritics / max(len(text), 1)
    if tone_ratio > 0.03:
        score += 0.03
    elif tone_ratio < 0.005:
        score -= 0.05

    # Very short transcriptions are less reliable
    if len(words) < 3:
        score -= 0.08

    # Nonsense characters reduce confidence
    alpha_ratio = sum(1 for c in text if c.isalpha() or ord(c) > 127) / max(len(text), 1)
    if alpha_ratio < 0.8:
        score -= 0.1

    return round(min(max(score, 0.5), 0.99), 4)


def _normalize_whisper_language(language: str | None) -> str | None:
    if not language:
        return None
    language = language.strip().lower()
    if language in {"en", "english"}:
        return "en"
    if language in {"auto", ""}:
        return None
    if language in {"yo", "yor", "yoruba"}:
        return "yo"
    return language


def _resolve_language(language: str, text: str = None) -> str:
    """Resolve 'auto' to a concrete language code. If text is provided, detect from it.

    Returns "auto" unchanged when no text is available, so the API caller can
    decide (e.g. let gpt-4o-transcribe auto-detect instead of assuming Yoruba).
    """
    lang = (language or "").strip().lower()
    if lang not in {"auto", ""}:
        return lang
    if text and text.strip():
        try:
            from language_detect import detect_language
            detected = detect_language(text)
            logger.info("Auto-detected language: %s from text: %s", detected, text[:50])
            return detected
        except Exception as e:
            logger.warning("Language detection failed: %s", e)
    return "auto"


def transcribe_with_whisper(audio_path: str, content_type: str = "audio/wav", language: str = "yo",
                            custom_vocabulary: str = "", is_retry: bool = False) -> dict:
    """Transcribe audio using OpenAI (gpt-4o-transcribe first, whisper-1 fallback).

    Long / fast speech is split into overlapping chunks and merged so the model
    does not drop content in continuous speech. `custom_vocabulary` adds a
    user-correction glossary to the prompt.
    """
    if not OPENAI_API_KEY:
        raise ValueError("OpenAI API key not configured for Whisper transcription.")

    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)

    needs_convert = _base_content_type(content_type) in NON_WAV_TYPES or not audio_path.lower().endswith(".wav")
    tmp_wav = None
    tmp_clean = None

    if needs_convert:
        tmp_wav = convert_to_wav(audio_path)
        path_to_load = tmp_wav
    else:
        path_to_load = audio_path

    try:
        # Load audio ONCE for quality analysis
        audio_data, sr = librosa.load(path_to_load, sr=16000)
        quality = analyze_audio_quality(audio_data, sr)

        # Preprocess for better ASR accuracy
        tmp_clean = preprocess_audio_for_asr(path_to_load)
        clean_audio, clean_sr = librosa.load(tmp_clean, sr=16000)

        from common.transcription_api import YORUBA_PROMPT
        resolved_lang = _resolve_language(language)

        # Segment long / fast audio into manageable chunks
        chunk_ranges = segment_audio_for_asr(clean_audio, clean_sr)
        logger.info("chunked audio into %d segment(s)", len(chunk_ranges))

        chunk_results = []  # list of (text, word_timestamp_dicts)
        used_engine = None

        def _to_audio_chunks():
            chunks = []
            for s, e in chunk_ranges:
                import io
                import soundfile as sf
                buf = io.BytesIO()
                sf.write(buf, clean_audio[s:e], 16000, format="WAV")
                chunks.append((s, buf.getvalue()))
            return chunks

        composed_prompt = _build_prompt(YORUBA_PROMPT, custom_vocabulary, is_retry)

        def _transcribe_gpt(chunk_bytes: bytes) -> dict:
            # NOTE: gpt-4o-transcribe does NOT accept the "yo" language code
            # (HTTP 400: "Language code 'yo' is not recognized"), nor does the
            # ev3 checkpoint accept response_format='verbose_json' (it wants
            # 'json' or 'text'). Forcing either of those makes gpt fail and the
            # app fall back to whisper-1, which transliterates English words
            # into garbled tone-marked "Yoruba". So: never force language="yo"
            # and never pass verbose_json. For auto we also send NO prompt
            # (long instructional prompts make the model echo the prompt).
            kwargs = {
                "model": "gpt-4o-transcribe",
                "file": ("chunk.wav", chunk_bytes),
                "response_format": "json",
            }
            if resolved_lang == "en":
                kwargs["language"] = "en"
            elif resolved_lang in {"yo", "yor", "yoruba"}:
                kwargs["prompt"] = composed_prompt
            return _transcribe_with_retry(
                lambda: client.audio.transcriptions.create(**kwargs),
                label="gpt-4o-transcribe",
            )

        def _transcribe_whisper(chunk_bytes: bytes) -> dict:
            kwargs = {
                "model": "whisper-1",
                "file": ("chunk.wav", chunk_bytes),
                "response_format": "verbose_json",
            }
            if resolved_lang in {"yo", "yor", "yoruba"}:
                kwargs["language"] = "yo"
                kwargs["prompt"] = composed_prompt
            elif resolved_lang in {"en", "english"}:
                kwargs["language"] = "en"
            else:
                wl = _normalize_whisper_language(language)
                if wl:
                    kwargs["language"] = wl
            return _transcribe_with_retry(
                lambda: client.audio.transcriptions.create(**kwargs),
                label="whisper-1",
            )

        def _chunk_confidence(engine_fn, chunk_bytes: bytes, text: str, words: list) -> float:
            """Per-chunk confidence for an engine result (whisper uses real word probs)."""
            if words:
                return round(sum(w.get("confidence") or 0.5 for w in words) / len(words), 4)
            return 0.5

        chunk_results = []  # list of (chunk_start_sec, chunk_end_sec, text, word_dicts)
        used_engine = None
        try:
            # Normal pass: gpt-4o-transcribe on each chunk.
            for chunk_start, chunk_bytes in [c for c in _to_audio_chunks()]:
                response = _transcribe_gpt(chunk_bytes)
                words = _word_confidences_from_segments(getattr(response, "segments", None) or [])
                chunk_results.append((chunk_start / 16000.0, (len(chunk_bytes)) / 16000.0,
                                      response.text.strip(), words))
            used_engine = "gpt-4o-transcribe"
        except Exception as e:
            logger.warning("gpt-4o-transcribe failed, falling back to whisper-1: %s", e)
            chunk_results = []
            try:
                for chunk_start, chunk_bytes in [c for c in _to_audio_chunks()]:
                    response = _transcribe_whisper(chunk_bytes)
                    words = _word_confidences_from_segments(getattr(response, "segments", None) or [])
                    chunk_results.append((chunk_start / 16000.0, (len(chunk_bytes)) / 16000.0,
                                          response.text.strip(), words))
                used_engine = "whisper-1"
            except Exception as e2:
                # Re-raise the original gpt error if both fail
                raise e

        # Ensemble retry: on a low-confidence retry, run BOTH engines per chunk
        # and pick the higher-confidence transcript for each chunk. This is how
        # the two engines genuinely "work together" -- not just as fallbacks.
        if is_retry and used_engine == "gpt-4o-transcribe":
            try:
                ensemble_results = []
                engines_won = {"gpt-4o-transcribe": 0, "whisper-1": 0}
                for chunk_start, chunk_bytes in [c for c in _to_audio_chunks()]:
                    gpt_words = None
                    gpt_text = None
                    gpt_conf = None
                    try:
                        resp = _transcribe_gpt(chunk_bytes)
                        gw = _word_confidences_from_segments(getattr(resp, "segments", None) or [])
                        gpt_text = resp.text.strip()
                        gpt_words = gw
                        gpt_conf = _chunk_confidence(None, chunk_bytes, gpt_text, gw)
                    except Exception:
                        gpt_conf = None

                    try:
                        resp = _transcribe_whisper(chunk_bytes)
                        ww = _word_confidences_from_segments(getattr(resp, "segments", None) or [])
                        w_text = resp.text.strip()
                        w_conf = _chunk_confidence(None, chunk_bytes, w_text, ww)
                    except Exception:
                        w_text = None
                        w_conf = None

                    pick_gpt = True
                    if gpt_conf is not None and w_conf is not None:
                        pick_gpt = gpt_conf >= w_conf
                    elif gpt_conf is None and w_conf is None:
                        pick_gpt = True
                    elif w_conf is None:
                        pick_gpt = True  # whisper failed for this chunk
                    else:
                        pick_gpt = False  # gpt failed, whisper worked
                    engines_won["gpt-4o-transcribe" if pick_gpt else "whisper-1"] += 1

                    chosen_text = gpt_text if pick_gpt else w_text
                    chosen_words = gpt_words if pick_gpt else ww
                    if not chosen_text:
                        chosen_text = (w_text or gpt_text) or ""
                    ensemble_results.append((chunk_start / 16000.0, (len(chunk_bytes)) / 16000.0,
                                             chosen_text, chosen_words))

                if ensemble_results:
                    chunk_results = ensemble_results
                    if engines_won["whisper-1"] > 0:
                        used_engine = "gpt-4o-transcribe+whisper-1"
                    logger.info("Ensemble: engines per chunk %s", engines_won)
            except Exception as e:
                logger.warning("Ensemble retry failed, keeping primary result: %s", e)

        # Words passed to the merger use timestamps relative to each chunk;
        # merge expects (text, words). Rebuild that shape from chunk_results.
        merge_chunks = [(text, words) for _, _, text, words in chunk_results]
        text = _merge_chunk_texts(merge_chunks, use_timestamps=True).strip()
        if not text:
            raise RuntimeError("OpenAI transcription returned empty text")

        # Word confidences with timestamps offset to the full recording.
        word_confidences = []
        for chunk_start_sec, _end_sec, _text, words in chunk_results:
            for w in words:
                start = w.get("start")
                end = w.get("end")
                word_confidences.append({
                    "word": w["word"],
                    "confidence": w.get("confidence") or 0.9,
                    "start": round(chunk_start_sec + start, 3) if start is not None else None,
                    "end": round(chunk_start_sec + end, 3) if end is not None else None,
                })

        # For whisper-1 or the ensemble, word_confidences hold real probabilities
        # (whisper contributes genuine per-word confidences), so average them.
        # For a pure gpt pass, gpt's word confidences default to 0.9 (unreliable),
        # so fall back to the heuristic estimate instead.
        if used_engine in {"whisper-1", "gpt-4o-transcribe+whisper-1"}:
            avg_conf = 0.9 if not word_confidences else round(
                sum(w["confidence"] for w in word_confidences) / len(word_confidences), 4
            )
        else:
            avg_conf = _estimate_gpt_confidence(text, [])

        detected_lang = _resolve_language(resolved_lang, text)

        return {
            "text": text,
            "confidence": avg_conf,
            "word_confidences": word_confidences,
            "quality": quality,
            "engine": used_engine,
            "detected_language": detected_lang,
        }
    finally:
        if tmp_wav and os.path.exists(tmp_wav):
            os.remove(tmp_wav)
        if tmp_clean and os.path.exists(tmp_clean):
            os.remove(tmp_clean)


def transcribe_with_local_model(audio_path: str, content_type: str = "audio/wav") -> dict:
    """Transcribe using the local W2V-BERT Yoruba model.

    The local CTC model collapses/deletes words on long or fast continuous
    speech, so we segment the audio into manageable chunks and merge.
    """
    model = load_stt_model()

    needs_convert = _base_content_type(content_type) in NON_WAV_TYPES or not audio_path.lower().endswith(".wav")
    tmp_wav = None
    tmp_clean = None

    if needs_convert:
        tmp_wav = convert_to_wav(audio_path)
        path_to_load = tmp_wav
    else:
        path_to_load = audio_path

    try:
        # Load once for quality
        audio, sr = librosa.load(path_to_load, sr=16000)
        quality = analyze_audio_quality(audio, sr)

        tmp_clean = preprocess_audio_for_asr(path_to_load)
        clean_audio, clean_sr = librosa.load(tmp_clean, sr=16000)

        chunk_ranges = segment_audio_for_asr(clean_audio, clean_sr)
        logger.info("local w2v-bert chunked into %d segment(s)", len(chunk_ranges))

        chunk_texts = []
        for s, e in chunk_ranges:
            chunk = clean_audio[s:e]
            if len(chunk) == 0:
                continue
            result = model(chunk, generate_kwargs={"language": "yoruba", "task": "transcribe"})
            t = (result.get("text") or "").strip()
            if t:
                chunk_texts.append(t)

        text = _merge_chunk_texts([(t, None) for t in chunk_texts]).strip()

        return {
            "text": text,
            "confidence": 0.85,
            "word_confidences": [],
            "quality": quality,
            "engine": "w2v-bert-2.0-yoruba",
            "detected_language": "yo",
        }
    finally:
        if tmp_wav and os.path.exists(tmp_wav):
            os.remove(tmp_wav)
        if tmp_clean and os.path.exists(tmp_clean):
            os.remove(tmp_clean)


def transcribe_with_whisper_local(audio_path: str, content_type: str = "audio/wav", language: str = "yo") -> dict:
    """Transcribe using the local Yoruba Whisper model."""
    whisper = load_whisper_model()
    if whisper is None:
        raise ValueError("Local Whisper model not available")

    needs_convert = _base_content_type(content_type) in NON_WAV_TYPES or not audio_path.lower().endswith(".wav")
    tmp_wav = None
    tmp_clean = None

    if needs_convert:
        tmp_wav = convert_to_wav(audio_path)
        path_to_load = tmp_wav
    else:
        path_to_load = audio_path

    try:
        import torch
        audio, sr = librosa.load(path_to_load, sr=16000)
        quality = analyze_audio_quality(audio, sr)

        tmp_clean = preprocess_audio_for_asr(path_to_load)
        clean_audio, clean_sr = librosa.load(tmp_clean, sr=16000)

        chunk_ranges = segment_audio_for_asr(clean_audio, clean_sr)
        logger.info("local whisper chunked into %d segment(s)", len(chunk_ranges))

        chunk_texts = []
        for s, e in chunk_ranges:
            chunk = clean_audio[s:e]
            if len(chunk) == 0:
                continue
            input_features = whisper["processor"](chunk, sampling_rate=16000, return_tensors="pt")
            input_features = input_features.input_features.to(whisper["device"])

            with torch.no_grad():
                forced_decoder_ids = whisper["processor"].get_decoder_prompt_ids(
                    task="transcribe", language="yoruba" if language in {"yo", "yor", "yoruba"} else "english"
                )
                output = whisper["model"].generate(
                    input_features,
                    forced_decoder_ids=forced_decoder_ids,
                    max_new_tokens=448,
                )

            t = whisper["processor"].batch_decode(output, skip_special_tokens=True)[0].strip()
            if t:
                chunk_texts.append(t)

        text = _merge_chunk_texts([(t, None) for t in chunk_texts]).strip()

        return {
            "text": text,
            "confidence": 0.80,
            "word_confidences": [],
            "quality": quality,
            "engine": "whisper-local-yoruba",
            "detected_language": "yo",
        }
    finally:
        if tmp_wav and os.path.exists(tmp_wav):
            os.remove(tmp_wav)
        if tmp_clean and os.path.exists(tmp_clean):
            os.remove(tmp_clean)


def transcribe(audio_path: str, content_type: str = "audio/wav", language: str = "yo",
               custom_vocabulary: str = "", retry_if_low: bool = False, preferred_engine: str = "auto") -> dict:
    """Main transcribe function with cascading fallback chain.

    1. OpenAI gpt-4o-transcribe (best quality, tone-marked Yoruba)
    2. OpenAI whisper-1 (good fallback)
    3. Local W2V-BERT Yoruba model (offline)
    4. Local Whisper Yoruba model (offline)

    `custom_vocabulary` is an optional glossary hint (from user corrections) that
    is appended to the ASR prompt to help with words the user frequently corrects.

    `preferred_engine` lets a caller force a specific backend instead of the
    cascade: "auto" (default), "openai", "local-w2v", or "local-whisper".
    """
    if preferred_engine == "local-w2v":
        return transcribe_with_local_model(audio_path, content_type)
    if preferred_engine == "local-whisper":
        return transcribe_with_whisper_local(audio_path, content_type, language=language)
    if preferred_engine == "openai":
        if not OPENAI_API_KEY:
            logger.warning("OpenAI key missing; falling back to local W2V-BERT model")
            return transcribe_with_local_model(audio_path, content_type)
        result = transcribe_with_whisper(
            audio_path, content_type, language=language, custom_vocabulary=custom_vocabulary
        )
        if retry_if_low and result.get("confidence", 0) and _should_retry(result):
            logger.info("Low-confidence result (%.2f); retrying transcription", result.get("confidence", 0))
            result = transcribe_with_whisper(
                audio_path, content_type, language=language,
                custom_vocabulary=custom_vocabulary, is_retry=True
            )
        return result

    if OPENAI_API_KEY:
        try:
            result = transcribe_with_whisper(
                audio_path, content_type, language=language, custom_vocabulary=custom_vocabulary
            )
            # Confidence-gated retry: when the API result is very low confidence,
            # retry once with a slightly stronger prompt. Only when enabled and not
            # already retried (transcribe_with_whisper does not retry itself here).
            if retry_if_low and result.get("engine") in {"gpt-4o-transcribe", "whisper-1"} \
               and _should_retry(result):
                logger.info("Low-confidence result (%.2f); retrying transcription", result.get("confidence", 0))
                result = transcribe_with_whisper(
                    audio_path, content_type, language=language,
                    custom_vocabulary=custom_vocabulary, is_retry=True
                )
            return result
        except Exception as e:
            logger.warning("OpenAI Whisper API failed: %s", e)

    logger.info("Trying local W2V-BERT model")
    try:
        return transcribe_with_local_model(audio_path, content_type)
    except Exception as e:
        logger.warning("W2V-BERT model failed: %s", e)

    logger.info("Trying local Whisper model")
    try:
        return transcribe_with_whisper_local(audio_path, content_type, language=language)
    except Exception as e:
        logger.warning("Local Whisper model failed: %s", e)

    raise RuntimeError("All transcription engines failed")
