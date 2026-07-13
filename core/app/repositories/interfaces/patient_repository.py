"""Contrato del repositorio de pacientes (sin detalle de Postgres)."""
from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entities.patient import Patient


class PatientRepository(ABC):
    @abstractmethod
    def save(self, patient: Patient) -> Patient:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, id: str, tenant_id: str) -> Optional[Patient]:
        raise NotImplementedError

    @abstractmethod
    def list_by_tenant(
        self, tenant_id: str, limit: int = 100, offset: int = 0
    ) -> List[Patient]:
        raise NotImplementedError

    @abstractmethod
    def count_by_tenant(self, tenant_id: str) -> int:
        raise NotImplementedError

    @abstractmethod
    def find_by_email(self, email: str, tenant_id: str) -> Optional[Patient]:
        raise NotImplementedError
