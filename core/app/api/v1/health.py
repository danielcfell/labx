"""Endpoint de health check (incluye ping a PostgreSQL)."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    service: str
    database: str


@router.get("/health", response_model=HealthResponse)
def health(db: Annotated[Session, Depends(get_db)]) -> HealthResponse:
    """Verifica que la Core API y PostgreSQL responden."""
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "degraded", "service": "labx-core", "database": "down"},
        ) from exc

    return HealthResponse(status="ok", service="labx-core", database="up")
