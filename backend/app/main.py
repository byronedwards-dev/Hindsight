"""Hindsight Economics - FastAPI Application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Hindsight Economics",
    description="A forecasting prediction game that tests users' economic intuition",
    version="1.0.0",
)

# CORS middleware for frontend
allowed_origins = [
    "http://localhost:3000",  # Next.js dev server
    "http://127.0.0.1:3000",
]

# Add production frontend URL if configured
if settings.app_base_url and settings.app_base_url not in allowed_origins:
    allowed_origins.append(settings.app_base_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")


@app.get("/")
def root():
    return {
        "name": "Hindsight Economics API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


