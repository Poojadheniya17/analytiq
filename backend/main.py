# backend/main.py
# Analytiq — Production-grade FastAPI application

import os
import time
from dotenv import load_dotenv
load_dotenv()
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from database.connection import init_db, check_db_connection
from core.logger import api_logger
from routers import auth, clients, analysis, ai, export, forecast, dashboard, simulator

# ── Init database ─────────────────────────────────────────────
init_db()

IS_PROD = os.environ.get("ENV") == "production"

app = FastAPI(
    title       = "Analytiq API",
    version     = "2.0.0",
    description = "AI-powered analytics platform API",
    docs_url    = None if IS_PROD else "/docs",
    redoc_url   = None
)

# ── CORS ──────────────────────────────────────────────────────
ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS", "http://localhost:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins     = ALLOWED_ORIGINS,
    allow_credentials = True,
    allow_methods     = ["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers     = ["Content-Type", "Authorization"],
)

# ── Request logging + timing middleware ───────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = round((time.time() - start) * 1000, 2)

    api_logger.info(
        f"{request.method} {request.url.path} "
        f"→ {response.status_code} ({duration}ms)"
    )

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"]         = "DENY"
    response.headers["X-XSS-Protection"]        = "1; mode=block"
    response.headers["Referrer-Policy"]          = "strict-origin-when-cross-origin"
    if IS_PROD:
        response.headers["Strict-Transport-Security"] = "max-age=31536000"

    return response

# ── Global error handler ──────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    api_logger.error(f"Unhandled error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Something went wrong. Our team has been notified."}
    )

# ── Static files ──────────────────────────────────────────────
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
os.makedirs(DATA_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=DATA_DIR), name="static")

# ── Routers ───────────────────────────────────────────────────
app.include_router(auth.router,       prefix="/api/auth",      tags=["Auth"])
app.include_router(clients.router,    prefix="/api/clients",   tags=["Clients"])
app.include_router(analysis.router,   prefix="/api/analysis",  tags=["Analysis"])
app.include_router(ai.router,         prefix="/api/ai",        tags=["AI"])
app.include_router(export.router,     prefix="/api/export",    tags=["Export"])
app.include_router(forecast.router,   prefix="/api/forecast",  tags=["Forecast"])
app.include_router(dashboard.router,  prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(simulator.router,  prefix="/api/simulator", tags=["Simulator"])

# ── Health check ──────────────────────────────────────────────
@app.get("/health", tags=["System"])
def health():
    db_ok = check_db_connection()
    status = "ok" if db_ok else "degraded"

    return {
        "status":   status,
        "version":  "2.0.0",
        "env":      os.environ.get("ENV", "development"),
        "database": "connected" if db_ok else "unreachable",
    }

@app.get("/", tags=["System"])
def root():
    return {"status": "Analytiq API running", "version": "2.0.0"}
