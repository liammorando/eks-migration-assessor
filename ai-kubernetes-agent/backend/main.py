from contextlib import asynccontextmanager

from core.config import get_settings
from core.logging import logger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AI Kubernetes Agent backend...")
    logger.info(f"Using model: {settings.openrouter_model}")
    yield
    logger.info("Shutting down AI Kubernetes Agent backend...")


app = FastAPI(
    title="AI Kubernetes Agent",
    description="AI-powered Kubernetes troubleshooting agent",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ai-kubernetes-agent",
    }


from api.routes import router as api_router

app.include_router(api_router, prefix="/api/v1")
