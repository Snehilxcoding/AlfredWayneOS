# ============================================================
# Alfred Wayne OS - Voice Input V2 (Production)
# PyAudio + Faster Whisper
# Device 7 (Stereo Mix Realtek) — confirmed working
# avg volume 3926 when speaking, threshold set to 2000
# ============================================================

import os
import tempfile
import wave
import time
import audioop
import pyaudio

from config.settings import (
    WHISPER_MODEL,
    WHISPER_DEVICE,
    WHISPER_LANGUAGE,
)

# ── Audio settings ────────────────────────────────────────────
RATE         = 16000
CHANNELS     = 1
FORMAT       = pyaudio.paInt16
CHUNK        = 512
INPUT_DEVICE = 7       # Device 7 = Stereo Mix Realtek — confirmed working

# ── VAD settings ──────────────────────────────────────────────
THRESHOLD       = 2000  # avg=3926 when speaking, so 2000 is safe
SILENCE_SECONDS = 1.0
MAX_SECONDS     = 15

_model = None


def _get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        print("[Alfred] Loading Whisper...")
        _model = WhisperModel(
            WHISPER_MODEL,
            device=WHISPER_DEVICE,
            compute_type="int8",
        )
    return _model


def record_audio() -> bytes:
    """
    Records audio using PyAudio on Device 7.
    Starts when voice detected above threshold.
    Stops when silence follows speech.
    Returns raw audio bytes.
    """
    p = pyaudio.PyAudio()

    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        input_device_index=INPUT_DEVICE,
        frames_per_buffer=CHUNK,
    )

    print("[Alfred] Listening... (speak now)")

    frames        = []
    recording     = False
    silence_start = None
    start_time    = None

    try:
        while True:
            data   = stream.read(CHUNK, exception_on_overflow=False)
            volume = audioop.rms(data, 2)

            if not recording:
                if volume > THRESHOLD:
                    print(f"[Alfred] Speech detected (volume: {volume})")
                    recording  = True
                    start_time = time.time()
                    frames.append(data)
            else:
                frames.append(data)

                if volume < THRESHOLD:
                    if silence_start is None:
                        silence_start = time.time()
                    elif time.time() - silence_start > SILENCE_SECONDS:
                        print("[Alfred] Silence detected — stopping.")
                        break
                else:
                    silence_start = None

                if time.time() - start_time > MAX_SECONDS:
                    print("[Alfred] Max recording time reached.")
                    break

    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

    return b"".join(frames)


def transcribe(audio_bytes: bytes) -> str:
    """Transcribes raw audio bytes using Faster Whisper."""
    if not audio_bytes:
        return ""

    model = _get_model()
    fd, path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)

    try:
        wf = wave.open(path, "wb")
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(pyaudio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(audio_bytes)
        wf.close()

        segments, _ = model.transcribe(
            path,
            language=WHISPER_LANGUAGE,
            beam_size=5,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 300},
        )
        return " ".join(s.text for s in segments).strip()

    finally:
        try:
            os.unlink(path)
        except Exception:
            pass


def listen() -> str:
    """
    Main entry point.
    Records until silence after speech, transcribes, returns text.
    """
    try:
        t0    = time.perf_counter()
        audio = record_audio()
        t1    = time.perf_counter()

        if not audio:
            return ""

        text = transcribe(audio)
        t2   = time.perf_counter()

        print(
            f"[Alfred] Record: {t1-t0:.1f}s | "
            f"Transcribe: {t2-t1:.1f}s | "
            f"Total: {t2-t0:.1f}s"
        )

        if text:
            print(f"[You] {text}")
            return text

        return ""

    except Exception as e:
        print(f"[Voice Error] {e}")
        return ""


def recalibrate():
    """Prints current device and threshold info."""
    print(f"[Alfred] Device: {INPUT_DEVICE} | Threshold: {THRESHOLD}")
    print("[Alfred] Adjust INPUT_DEVICE or THRESHOLD in voice_input_v2.py if needed.")