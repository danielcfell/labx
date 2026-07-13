"""Casos de uso de pacientes. Depende de la interfaz del repositorio, no de Postgres."""
from math import ceil
from typing import Dict, List, Tuple

from app.domain.entities.patient import Patient
from app.domain.exceptions import ConflictError, DomainError, NotFoundError
from app.repositories.interfaces.patient_repository import PatientRepository

DEFAULT_TENANT_ID = "default"


class PatientService:
    def __init__(self, repository: PatientRepository) -> None:
        self._repository = repository

    def create_patient(self, data: Dict) -> Patient:
        tenant_id = data.get("tenant_id") or DEFAULT_TENANT_ID
        email = data["email"]

        if self._repository.find_by_email(email, tenant_id) is not None:
            raise ConflictError(f"Email '{email}' is already registered for this tenant")

        patient = Patient.create(
            tenant_id=tenant_id,
            name=data["name"],
            email=email,
            phone=data.get("phone"),
            identification=data.get("identification"),
        )
        try:
            return self._repository.save(patient)
        except DomainError as exc:
            raise ConflictError(str(exc)) from exc

    def get_patient(self, id: str, tenant_id: str) -> Patient:
        patient = self._repository.get_by_id(id, tenant_id)
        if patient is None:
            raise NotFoundError(f"Patient '{id}' was not found")
        return patient

    def list_patients(
        self, tenant_id: str, page: int = 1, size: int = 20
    ) -> Tuple[List[Patient], int]:
        if page < 1:
            raise ValueError("page must be >= 1")
        if size < 1:
            raise ValueError("size must be >= 1")

        offset = (page - 1) * size
        items = self._repository.list_by_tenant(tenant_id, limit=size, offset=offset)
        total = self._repository.count_by_tenant(tenant_id)
        return items, total

    @staticmethod
    def pages_for(total: int, size: int) -> int:
        if size <= 0:
            return 0
        return ceil(total / size) if total else 0
