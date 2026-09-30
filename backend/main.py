import os
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import logging
logger = logging.getLogger(__name__)

from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from config import CORS_ORIGINS
from database import init_db
from routes.auth import router as auth_router
from routes.profile import router as profile_router
from routes.transcribe import router as transcribe_router
from routes.translate import router as translate_router
from routes.history import router as history_router
from routes.admin import router as admin_router
from routes.corrections import router as corrections_router
from routes.translate_stream import router as translate_stream_router
from routes.tts import router as tts_router
from middleware.rate_limit import RateLimitMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    import threading
    def _preload():
        try:
            from common.nllb import load_nllb
            load_nllb()
            logger.info("NLLB model preloaded")
        except Exception as e:
            logger.warning("NLLB preload failed: %s", e)
    threading.Thread(target=_preload, daemon=True).start()
    yield


app = FastAPI(
    title="Bámi-Sọ̀rọ̀ API",
    description="Yoruba Speech-to-Text & Translation API",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RateLimitMiddleware)

app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(transcribe_router)
app.include_router(translate_router)
app.include_router(translate_stream_router)
app.include_router(history_router)
app.include_router(admin_router)
app.include_router(corrections_router)
app.include_router(tts_router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}
