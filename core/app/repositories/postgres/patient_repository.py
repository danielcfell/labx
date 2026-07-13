"""Implementación PostgreSQL del repositorio de pacientes."""
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.entities.patient import Patient
from app.domain.exceptions import DomainError
from app.infrastructure.database import (
    PatientModel,
    patient_domain_to_dict,
    patient_model_to_domain,
)
from app.repositories.interfaces.patient_repository import PatientRepository


class PostgresPatientRepository(PatientRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, patient: Patient) -> Patient:
        data = patient_domain_to_dict(patient)
        model = PatientModel(**data)
        try:
            self._session.add(model)
            self._session.commit()
            self._session.refresh(model)
        except IntegrityError as exc:
            self._session.rollback()
            raise DomainError(
                f"Patient with email '{patient.email}' already exists for this tenant"
            ) from exc
        return patient_model_to_domain(model)

    def get_by_id(self, id: str, tenant_id: str) -> Optional[Patient]:
        stmt = select(PatientModel).where(
            PatientModel.id == id,
            PatientModel.tenant_id == tenant_id,
        )
        model = self._session.scalar(stmt)
        if model is None:
            return None
        return patient_model_to_domain(model)

    def list_by_tenant(
        self, tenant_id: str, limit: int = 100, offset: int = 0
    ) -> List[Patient]:
        stmt = (
            select(PatientModel)
            .where(PatientModel.tenant_id == tenant_id)
            .order_by(PatientModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        models = self._session.scalars(stmt).all()
        return [patient_model_to_domain(m) for m in models]

    def count_by_tenant(self, tenant_id: str) -> int:
        stmt = (
            select(func.count())
            .select_from(PatientModel)
            .where(PatientModel.tenant_id == tenant_id)
        )
        return int(self._session.scalar(stmt) or 0)

    def find_by_email(self, email: str, tenant_id: str) -> Optional[Patient]:
        stmt = select(PatientModel).where(
            PatientModel.email == email,
            PatientModel.tenant_id == tenant_id,
        )
        model = self._session.scalar(stmt)
        if model is None:
            return None
        return patient_model_to_domain(model)
