import os
import secrets
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

BASE_DIR = Path(__file__).resolve().parent

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost:5432/bami_soro")
DATABASE_URL_SYNC = os.getenv("DATABASE_URL_SYNC", "postgresql+psycopg://postgres:password@localhost:5432/bami_soro")

# Free serverless Postgres (e.g. Neon) caps concurrent connections and suspends
# when idle, so keep the pool small by default. Raise these for a real database.
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "5"))

_JWT_SECRET_ENV = os.getenv("JWT_SECRET")
if not _JWT_SECRET_ENV:
    JWT_SECRET = secrets.token_hex(32)
    print(
        "WARNING: JWT_SECRET is not set in backend/.env. A random secret was "
        "generated for this process, so all existing sessions will be invalidated "
        "and logins reset every restart. Set JWT_SECRET in backend/.env to a fixed "
        "random value (e.g. `python -c \"import secrets; print(secrets.token_hex(32))\"`).",
        file=sys.stderr,
    )
else:
    JWT_SECRET = _JWT_SECRET_ENV
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24

ML_MODEL_PATH = str(BASE_DIR.parent / "yoruba_model")
UPLOAD_DIR = str(BASE_DIR / "uploads")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
NLLB_MODEL = os.getenv("NLLB_MODEL", "facebook/nllb-200-distilled-600M")

# Comma-separated list of allowed browser origins. Set CORS_ORIGINS in .env to
# your deployed frontend URL, otherwise only local dev is allowed.
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    if origin.strip()
]

ALLOWED_AUDIO_TYPES = ["audio/wav", "audio/mpeg", "audio/mp3", "audio/m4a", "audio/x-m4a", "audio/webm", "audio/ogg", "audio/flac", "audio/mp4", "audio/x-wav", "application/octet-stream"]
MAX_UPLOAD_SIZE_MB = 25
MAX_TRANSLATION_CHARS = 2000
