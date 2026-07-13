"""Router HTTP de pacientes — capa delgada: valida, delega y responde."""
from datetime import datetime
from math import ceil
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.domain.entities.patient import Patient
from app.domain.exceptions import ConflictError, NotFoundError
from app.infrastructure.database import get_db
from app.repositories.interfaces.patient_repository import PatientRepository
from app.repositories.postgres.patient_repository import PostgresPatientRepository
from app.services.patient_service import DEFAULT_TENANT_ID, PatientService

router = APIRouter(prefix="/patients", tags=["patients"])


class PatientCreate(BaseModel):
    name: str = Field(..., min_length=1)
    email: EmailStr
    phone: Optional[str] = None
    identification: Optional[str] = None


class PatientResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    email: EmailStr
    phone: Optional[str] = None
    identification: Optional[str] = None
    created_at: Optional[datetime] = None

    @classmethod
    def from_domain(cls, patient: Patient) -> "PatientResponse":
        return cls(
            id=patient.id or "",
            tenant_id=patient.tenant_id,
            name=patient.name,
            email=patient.email,
            phone=patient.phone,
            identification=patient.identification,
            created_at=patient.created_at,
        )


class PatientListResponse(BaseModel):
    items: List[PatientResponse]
    total: int
    page: int
    size: int
    pages: int


def get_patient_repository(
    db: Session = Depends(get_db),
) -> PatientRepository:
    return PostgresPatientRepository(db)


@router.post("/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
def create_patient(
    body: PatientCreate,
    repo: Annotated[PatientRepository, Depends(get_patient_repository)],
) -> PatientResponse:
    service = PatientService(repo)
    try:
        patient = service.create_patient(body.model_dump())
        return PatientResponse.from_domain(patient)
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/", response_model=PatientListResponse)
def list_patients(
    repo: Annotated[PatientRepository, Depends(get_patient_repository)],
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
) -> PatientListResponse:
    service = PatientService(repo)
    try:
        items, total = service.list_patients(DEFAULT_TENANT_ID, page=page, size=size)
        pages = ceil(total / size) if total else 0
        return PatientListResponse(
            items=[PatientResponse.from_domain(p) for p in items],
            total=total,
            page=page,
            size=size,
            pages=pages,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{id}", response_model=PatientResponse)
def get_patient(
    id: str,
    repo: Annotated[PatientRepository, Depends(get_patient_repository)],
) -> PatientResponse:
    service = PatientService(repo)
    try:
        patient = service.get_patient(id, DEFAULT_TENANT_ID)
        return PatientResponse.from_domain(patient)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
