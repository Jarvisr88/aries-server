"""
API Router Configuration
Version: 2024-12-19_13-27
"""
from fastapi import APIRouter
from app.api.v1.endpoints import insurance

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(insurance.router)
