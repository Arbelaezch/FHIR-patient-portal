"""
Main FastAPI application.
Initializes the app, middleware, and routes.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager

from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    print("🚀 Starting FHIR Patient Portal API...")
    yield
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

# Session middleware must be added before CORS
# Uses SECRET_KEY to sign cookies so they can't be tampered with
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie="fhir_session",
    max_age=3600,        # 1 hour
    same_site="lax",
    https_only=False,    # Set to True in production
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health endpoints
@app.get("/", tags=["Health"])
async def root():
    return {
        "message": "FHIR Patient Portal API",
        "version": "1.0.0",
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}


# Routers
from app.routes.auth import smart
from app.routes.fhir import proxy

app.include_router(smart.router, prefix="/auth", tags=["Auth"])
app.include_router(proxy.router, prefix="/fhir", tags=["FHIR"])