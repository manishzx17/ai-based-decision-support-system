import sys
import os

# Ensure backend folder is on sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from init_db import init_db

from routes import auth, reports, recommendations, cost, travel, services

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API for 12C - AI-Based Medical Travel Decision Support System"
)

# Enable CORS for Frontend Development (Vite on port 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database schemas and seed datasets on startup
@app.on_event("startup")
def on_startup():
    init_db()

# Register API Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(reports.router, prefix=settings.API_V1_STR)
app.include_router(recommendations.router, prefix=settings.API_V1_STR)
app.include_router(cost.router, prefix=settings.API_V1_STR)
app.include_router(travel.router, prefix=settings.API_V1_STR)
app.include_router(services.router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "message": "Welcome to 12C - AI-Based Medical Travel Decision Support System API",
        "status": "online",
        "version": settings.VERSION,
        "docs_url": "/docs"
    }

@app.get("/api/health")
def healthcheck():
    return {
        "status": "healthy",
        "database": "connected",
        "ocr_engine": "active",
        "rag_engine": "active",
        "xgboost_cost_estimator": "active"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
