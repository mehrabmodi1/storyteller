"""
FastAPI Application Entry Point

Main application with CORS configuration, route registration,
and startup/shutdown event handlers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    
    Startup:
    - Initialize any global resources
    - Validate configuration
    
    Shutdown:
    - Clean up resources
    """
    # Startup
    print("=" * 60)
    print("Storyteller Backend Starting...")
    print(f"   API Host: {settings.api_host}:{settings.api_port}")
    print(f"   Auth Mode: {settings.auth_mode}")
    print(f"   Chat Model: {settings.chat_model}")
    print(f"   Image Model: {settings.image_model}")
    print("=" * 60)
    
    yield
    
    # Shutdown
    print("=" * 60)
    print("Storyteller Backend Shutting Down...")
    print("=" * 60)


# Create FastAPI app
app = FastAPI(
    title="Storyteller API",
    description="Backend API for AI-powered interactive storytelling",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers
from api.routes import stories, personas, corpuses, journeys

app.include_router(stories.router, prefix="/api", tags=["stories"])
app.include_router(personas.router, prefix="/api", tags=["personas"])
app.include_router(corpuses.router, prefix="/api", tags=["corpuses"])
app.include_router(journeys.router, prefix="/api", tags=["journeys"])


@app.get("/")
async def root():
    """Root endpoint - API health check."""
    return {
        "status": "healthy",
        "service": "Storyteller Backend",
        "version": "2.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "api_host": settings.api_host,
        "api_port": settings.api_port,
        "auth_mode": settings.auth_mode,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
    )

