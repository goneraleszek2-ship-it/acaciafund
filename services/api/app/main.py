import os
import sys
import time
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator

from . import db


def parse_origins(raw: str) -> List[str]:
    return [o.strip() for o in raw.split(",") if o.strip()]


APP_NAME = "AcaciaFund API"
DEBUG = os.environ.get("ACACIA_DEBUG", "false").lower() == "true"
HOST = os.environ.get("ACACIA_HOST", "0.0.0.0")
PORT = int(os.environ.get("ACACIA_PORT", "8000"))
ALLOWED_ORIGINS = parse_origins(
    os.environ.get(
        "ACACIA_CORS_ORIGINS",
        "http://localhost:1313,http://127.0.0.1:1313,https://www.acaciafund.org",
    )
)

app = FastAPI(title=APP_NAME, version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "app": APP_NAME}


@app.get("/ping")
async def ping():
    return {"ping": "pong"}


@app.get("/info")
async def info():
    return {"app": APP_NAME, "debug": DEBUG, "cors_origins": ALLOWED_ORIGINS}


@app.on_event("startup")
def startup():
    db.init_db()


class ProgressPayload(BaseModel):
    url: str
    done: Optional[bool] = False
    score: Optional[int] = Field(0, ge=0, le=100)
    ts: Optional[int] = None

    @validator("url")
    def url_must_be_path(cls, v: str) -> str:
        if not v.startswith("/"):
            raise ValueError("url must be a site-local path starting with '/'")
        return v


@app.post("/progress")
async def set_progress(payload: ProgressPayload):
    ts = int(payload.ts or time.time())
    db.upsert_progress(payload.url, bool(payload.done), int(payload.score), ts)
    return {"ok": True}


@app.get("/progress")
async def get_progress(url: str):
    p = db.get_progress(url)
    return {"result": p}
