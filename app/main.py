"""FastAPI Application Entry Point"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings, validate_settings
from app.database import init_db

# Fail fast on insecure config (insecure JWT secret, missing service role key, etc.)
validate_settings()
from app.routes import auth as auth_router
from app.routes import owners as owners_router
from app.routes import pets as pets_router
from app.routes import staff as staff_router
from app.routes import appointments as appointments_router
from app.routes import inventory as inventory_router
from app.routes import invoices as invoices_router
from app.routes import dashboard as dashboard_router
from app.routes import medical_records as medical_records_router
from app.routes import services as services_router
from app.routes import feedback as feedback_router
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
    allow_origins=settings.cors_origins,  # configured via FRONTEND_ORIGINS env
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


app.include_router(auth_router.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(owners_router.router, prefix="/api/v1/owners", tags=["Pet Owners"])
app.include_router(pets_router.router, prefix="/api/v1/pets", tags=["Pets"])
app.include_router(staff_router.router, prefix="/api/v1/staff", tags=["Staff"])
app.include_router(appointments_router.router, prefix="/api/v1/appointments", tags=["Appointments"])
app.include_router(inventory_router.router, prefix="/api/v1/inventory", tags=["Inventory"])
app.include_router(invoices_router.router, prefix="/api/v1/invoices", tags=["Invoices & Billing"])
app.include_router(dashboard_router.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(medical_records_router.router, prefix="/api/v1/medical-records", tags=["Medical Records"])
app.include_router(services_router.router, prefix="/api/v1/services", tags=["Services"])
app.include_router(feedback_router.router, prefix="/api/v1/feedback", tags=["Feedback"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
