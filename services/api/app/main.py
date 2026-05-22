from fastapi import FastAPI
from pydantic import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AcaciaFund API"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    class Config:
        env_file = ".env"


settings = Settings()


app = FastAPI(title=settings.app_name, version="0.1.0")


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
