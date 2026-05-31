import os
from dotenv import load_dotenv

load_dotenv()

# ── Identity ─────────────────────────────────────────────────
ASSISTANT_NAME = os.getenv("ASSISTANT_NAME", "Alfred")
USER_NAME      = os.getenv("USER_NAME", "Master Wayne")

# ── API Keys ─────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY   = os.getenv("GROQ_API_KEY")

# ── Voice Input ──────────────────────────────────────────────
WHISPER_MODEL     = "base"
WHISPER_DEVICE    = "cpu"
WHISPER_LANGUAGE  = "en"
RECORD_SAMPLERATE = 16000
# Note: RECORD_DURATION removed — Phase D uses silence detection

# ── Voice Output ─────────────────────────────────────────────
TTS_VOICE  = "en-GB-RyanNeural"
TTS_RATE   = "+0%"
TTS_VOLUME = "+0%"

# ── Paths ────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.dirname(__file__))
MEMORY_DIR  = os.path.join(BASE_DIR, "memory")
MEMORY_FILE = os.path.join(MEMORY_DIR, "memory.json")
LOG_DIR     = os.path.join(BASE_DIR, "logs")
LOG_FILE    = os.path.join(LOG_DIR, "action_log.jsonl")

# ── System Monitoring ────────────────────────────────────────
LOW_BATTERY_THRESHOLD  = 20
HIGH_CPU_THRESHOLD     = 80
HIGH_RAM_THRESHOLD     = 85

# ── Internet Check ───────────────────────────────────────────
INTERNET_CHECK_HOST    = "8.8.8.8"
INTERNET_CHECK_PORT    = 53
INTERNET_CHECK_TIMEOUT = 3

# ── Runtime ──────────────────────────────────────────────────
TEXT_ONLY_MODE = False