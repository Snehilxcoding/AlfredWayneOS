# ============================================================
# Alfred Wayne OS - Voice Input (Final)
# Uses PEAK-based detection instead of RMS.
# Your mic: RMS noise > RMS voice, but peak voice >> peak noise.
# Peak detection perfectly handles this situation.
# ============================================================

import os
import tempfile
import numpy as np

from config.settings import (
    WHISPER_MODEL,
    WHISPER_DEVICE,
    WHISPER_LANGUAGE,
)

# ── Device & audio settings ───────────────────────────────────
INPUT_DEVICE   = 7
PEAK_THRESHOLD = 0.0003
SAMPLE_RATE    = 16000
CHUNK_DURATION = 0.3

# ── VAD settings ──────────────────────────────────────────────
MAX_RECORD_SECS      = 15
MIN_SPEECH_SECS      = 0.5
SILENCE_AFTER_SPEECH = 1.5

# ── Peak detection thresholds ────────────────────────────────
# Your peak noise level ≈ 0.05 (background)
# Your peak voice level ≈ 0.21 (when speaking)
# Threshold sits between them
PEAK_THRESHOLD       = 0.05
_model = None


def _get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        print("[Alfred] Loading Whisper... (first time only)")
        _model = WhisperModel(
            WHISPER_MODEL,
            device=WHISPER_DEVICE,
            compute_type="int8"
        )
    return _model


def _peak(chunk: np.ndarray) -> float:
    """Peak amplitude of an audio chunk."""
    return float(np.max(np.abs(chunk.astype(np.float32))))


def _record_chunk(samples: int) -> np.ndarray:
    import sounddevice as sd
    chunk = sd.rec(
        samples,
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
        device=INPUT_DEVICE,
    )
    sd.wait()
    return chunk.flatten()


def record_until_silence() -> np.ndarray:
    chunk_samples     = int(SAMPLE_RATE * CHUNK_DURATION)
    max_chunks        = int(MAX_RECORD_SECS / CHUNK_DURATION)
    silence_needed    = int(SILENCE_AFTER_SPEECH / CHUNK_DURATION)
    min_speech_chunks = int(MIN_SPEECH_SECS / CHUNK_DURATION)

    print(f"[Alfred] Listening... (speak now) [threshold: {PEAK_THRESHOLD}]")

    all_audio      = []
    silence_count  = 0
    speech_chunks  = 0
    speech_started = False

    for _ in range(max_chunks):
        try:
            chunk = _record_chunk(chunk_samples)
        except Exception as e:
            print(f"[Voice] Chunk error: {e}")
            break

        all_audio.append(chunk)
        level = _peak(chunk)

        if level >= PEAK_THRESHOLD:
            speech_started = True
            speech_chunks += 1
            silence_count  = 0
        else:
            if speech_started:
                silence_count += 1
                if (silence_count >= silence_needed and
                        speech_chunks >= min_speech_chunks):
                    break

    if not all_audio:
        return np.zeros(chunk_samples, dtype=np.float32)

    audio    = np.concatenate(all_audio)
    duration = len(audio) / SAMPLE_RATE
    print(
        f"[Alfred] Recorded {duration:.1f}s | "
        f"Speech chunks: {speech_chunks} | "
        f"Peak threshold: {PEAK_THRESHOLD}"
    )
    return audio


def transcribe(audio: np.ndarray) -> str:
    import scipy.io.wavfile as wav
    model = _get_model()

    fd, path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)

    try:
        wav.write(
            path,
            SAMPLE_RATE,
            (audio * 32767).astype(np.int16)
        )
        segments, _ = model.transcribe(
            path,
            language=WHISPER_LANGUAGE,
            beam_size=5,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 300},
        )
        return " ".join([s.text for s in segments]).strip()
    finally:
        try:
            os.unlink(path)
        except Exception:
            pass


def listen() -> str:
    try:
        audio = record_until_silence()

        if _peak(audio) < 0.05:
            print("[Alfred] No speech detected.")
            return ""

        text = transcribe(audio)

        if text:
            print(f"[You] {text}")
            return text

        return ""

    except Exception as e:
        print(f"[Voice Error] {e}")
        return ""


def recalibrate():
    """No-op — peak detection needs no calibration."""
    print(f"[Alfred] Peak threshold is {PEAK_THRESHOLD}. "
          f"Adjust PEAK_THRESHOLD in voice_input.py if needed.")