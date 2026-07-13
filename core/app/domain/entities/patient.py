"""Entidad de dominio Patient (pura: sin FastAPI ni SQLAlchemy)."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from pydantic import BaseModel, EmailStr, Field


class Patient(BaseModel):
    id: Optional[str] = None
    tenant_id: str
    name: str = Field(..., min_length=1)
    email: EmailStr
    phone: Optional[str] = None
    identification: Optional[str] = None
    created_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        *,
        tenant_id: str,
        name: str,
        email: str,
        phone: Optional[str] = None,
        identification: Optional[str] = None,
        id: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ) -> Patient:
        return cls(
            id=id or str(uuid4()),
            tenant_id=tenant_id,
            name=name,
            email=email,
            phone=phone,
            identification=identification,
            created_at=created_at or datetime.now(),
        )

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()
