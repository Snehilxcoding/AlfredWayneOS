# ============================================================
# Alfred Wayne OS - Voice Output (Phase D)
# Fixed: greeting no longer blocks startup.
# TTS runs in background thread — print appears instantly.
# ============================================================

import asyncio
import os
import tempfile
import threading
from config.settings import TTS_VOICE, TTS_RATE, TTS_VOLUME, ASSISTANT_NAME


async def _speak_async(text: str):
    """Async edge-tts synthesis and playback."""
    import edge_tts
    comm = edge_tts.Communicate(text, TTS_VOICE, rate=TTS_RATE, volume=TTS_VOLUME)
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        path = f.name
    try:
        await comm.save(path)
        _play(path)
    finally:
        if os.path.exists(path):
            os.unlink(path)


def _play(path: str):
    """Plays an MP3 file using pygame."""
    try:
        import pygame
        pygame.mixer.init()
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
        pygame.mixer.quit()
    except ImportError:
        os.startfile(path)


def _speak_worker(text: str):
    """Runs TTS in its own thread with its own event loop."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_speak_async(text))
        loop.close()
    except Exception as e:
        print(f"[Alfred] Voice error: {e}")


def speak(text: str, silent: bool = False, background: bool = False):
    """
    Main speak function.

    Args:
        text:       Text Alfred should say.
        silent:     Print only, no audio.
        background: If True, speak in background thread
                    so caller returns immediately.
                    Use for greetings and non-blocking responses.
    """
    print(f"[{ASSISTANT_NAME}] {text}")

    if silent:
        return

    if background:
        # Fire and forget — doesn't block
        t = threading.Thread(target=_speak_worker, args=(text,), daemon=True)
        t.start()
        return

    # Blocking — waits for speech to finish before returning
    try:
        _speak_worker(text)
    except Exception as e:
        print(f"[Alfred] Voice error: {e}")