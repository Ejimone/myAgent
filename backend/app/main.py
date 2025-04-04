from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os

from app.core.config import settings
from app.core.database import get_db, engine, Base
from app.routes import auth, classroom, assignments

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.PROJECT_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth")
app.include_router(classroom.router, prefix=f"{settings.API_V1_STR}/classroom")
app.include_router(assignments.router, prefix=f"{settings.API_V1_STR}/assignments")

# Include the Google OAuth callback route at the root level
# This is needed because Google redirects to this specific URL path
from app.routes.auth import google_callback_get
app.add_route("/accounts/google/login/callback/", google_callback_get, methods=["GET"])

@app.get("/")
def read_root():
    """Root endpoint"""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "description": settings.PROJECT_DESCRIPTION
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )