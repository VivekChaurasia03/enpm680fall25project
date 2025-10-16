from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import auth, vehicles, reservations, chatbot, users

app = FastAPI(
    title=settings.APP_NAME,
    description="Fleet Management System for ENPM680 Project",
    version="1.0.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(vehicles.router)
app.include_router(reservations.router)
app.include_router(chatbot.router)
app.include_router(users.router)

@app.get("/")
async def root():
    return {
        "message": "FleetWise API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}