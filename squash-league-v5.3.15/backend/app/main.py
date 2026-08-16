from fastapi import FastAPI
from sqlalchemy import text
from .config import settings
from .database import engine

app = FastAPI(title=settings.app_name, version="5.3.15")

@app.get("/api/health", tags=["system"])
def health():
    return {"status": "ok", "version": app.version}

@app.get("/api/ready", tags=["system"])
def ready():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ready"}
