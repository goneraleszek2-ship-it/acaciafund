from fastapi import FastAPI, HTTPException
from pydantic import BaseSettings, BaseModel, Field, validator
from fastapi.middleware.cors import CORSMiddleware
from . import db
import time
from typing import List, Optional


class Settings(BaseSettings):
    app_name: str = "AcaciaFund API"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    # Allowed origins for CORS — set to your site origin in production
    allowed_origins: List[str] = Field(default_factory=lambda: ["http://localhost:1313", "http://127.0.0.1:1313"])

    class Config:
        env_file = ".env"


settings = Settings()


app = FastAPI(title=settings.app_name, version="0.1.0")

# Allow cross-origin requests from configured origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    """Simple health endpoint for orchestration checks."""
    return {"status": "ok", "app": settings.app_name}


@app.get("/ping")
async def ping():
    return {"ping": "pong"}


@app.get("/info")
async def info():
    """Expose basic runtime info useful for debugging in development."""
    return {"app": settings.app_name, "debug": settings.debug}


@app.on_event("startup")
def startup():
    # Ensure DB exists
    db.init_db()


@app.post("/progress")
class ProgressPayload(BaseModel):
    url: str
    done: Optional[bool] = False
    score: Optional[int] = Field(0, ge=0, le=100)
    ts: Optional[int] = None

    @validator("url")
    def url_must_be_path(cls, v: str) -> str:
        # Require a relative path (site-local) to avoid arbitrary external URLs
        if not v.startswith("/"):
            raise ValueError("url must be a site-local path starting with '/'")
        return v


@app.post("/progress")
async def set_progress(payload: ProgressPayload):
    """Accepts {url, done, score, ts} and stores into SQLite.

    Validation: url must be a site-local path (start with '/'), score is 0..100.
    """
    ts = int(payload.ts or time.time())
    db.upsert_progress(payload.url, bool(payload.done), int(payload.score), ts)
    return {"ok": True}


@app.get("/progress")
async def get_progress(url: str):
    p = db.get_progress(url)
    return {"result": p}
