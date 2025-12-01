"""
Main FastAPI application.
Initializes the app, middleware, and routes.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    Initializes database on startup.
    """
    # Startup
    print("🚀 Starting FHIR Patient Portal API...")
    await init_db()
    print("✅ Database initialized")
    
    yield
    
    # Shutdown
    print("👋 Shutting down FHIR Patient Portal API...")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="A FHIR R4-compliant patient portal API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root endpoint
@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API health check."""
    return {
        "message": "FHIR Patient Portal API",
        "version": "1.0.0",
        "status": "healthy",
        "environment": settings.ENVIRONMENT
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Import and include routers
# TODO: Add routers as we build them
# from app.routes.fhir import patient, observation, medication, condition
# app.include_router(patient.router, prefix="/fhir", tags=["FHIR - Patient"])
# app.include_router(observation.router, prefix="/fhir", tags=["FHIR - Observation"])
