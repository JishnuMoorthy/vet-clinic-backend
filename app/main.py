"""FastAPI Application Entry Point"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.database import init_db
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="RESTful API for Veterinary Clinic Management System",
    version="1.0.0"
)

# Add CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "Vet Clinic VMS API is running",
        "version": "1.0.0"
    }


# Application startup event
@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("🚀 Starting Vet Clinic VMS Backend")
    db_status = await init_db()
    if db_status:
        logger.info("✅ Application started successfully")
    else:
        logger.warning("⚠️ Database not initialized. Run migrations first.")


# Application shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("🛑 Shutting down Vet Clinic VMS Backend")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "docs": "/docs",
        "health": "/health"
    }


# Placeholder for route includes (will be added in next phase)
# app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
# app.include_router(pets.router, prefix="/api/v1/pets", tags=["pets"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
