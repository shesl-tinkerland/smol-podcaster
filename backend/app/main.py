from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.v1 import episodes, transcripts, processing, chapters
from app.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up...")
    yield
    # Shutdown
    print("Shutting down...")

app = FastAPI(
    title="Smol Podcaster API",
    description="API for podcast transcription and processing",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(episodes.router, prefix="/api/v1/episodes", tags=["episodes"])
app.include_router(transcripts.router, prefix="/api/v1/transcripts", tags=["transcripts"])
app.include_router(processing.router, prefix="/api/v1/processing", tags=["processing"])
app.include_router(chapters.router, prefix="/api/v1/chapters", tags=["chapters"])

@app.get("/")
async def root():
    return {"message": "Smol Podcaster API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}