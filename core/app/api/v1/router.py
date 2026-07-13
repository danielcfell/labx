"""Agregador de routers de la versión v1 de la API."""
from fastapi import APIRouter

from app.api.v1 import health, patients

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(patients.router)
