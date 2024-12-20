"""
API v1 router
Version: 2024-12-20_00-24
"""
from fastapi import APIRouter
from .authorization import router as authorization_router

api_router = APIRouter()

# Register routers
api_router.include_router(authorization_router)
