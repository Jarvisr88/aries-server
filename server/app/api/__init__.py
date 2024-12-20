"""
API router initialization
Version: 2024-12-20_00-24
"""
from fastapi import APIRouter
from .v1 import api_router as api_v1_router

router = APIRouter()

# Register API versions
router.include_router(api_v1_router, prefix="/api")
