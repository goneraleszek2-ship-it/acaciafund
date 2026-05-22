from fastapi import FastAPI, HTTPException
from pydantic import BaseSettings
from fastapi.middleware.cors import CORSMiddleware
from . import db
import time


class Settings(BaseSettings):
    app_name: str = "AcaciaFund API"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    class Config:
        env_file = ".env"


settings = Settings()


app = FastAPI(title=settings.app_name, version="0.1.0")

# Allow cross-origin requests from the static site (adjust in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
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
async def set_progress(payload: dict):
    """Accepts {url, done, score, ts} and stores into SQLite."""
    try:
        url = payload["url"]
        done = bool(payload.get("done", False))
        score = int(payload.get("score", 0))
        ts = int(payload.get("ts", time.time()))
    except Exception:
        raise HTTPException(status_code=400, detail="invalid payload")
    db.upsert_progress(url, done, score, ts)
    return {"ok": True}


@app.get("/progress")
async def get_progress(url: str):
    p = db.get_progress(url)
    return {"result": p}
