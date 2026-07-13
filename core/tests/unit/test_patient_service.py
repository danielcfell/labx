"""Tests unitarios de PatientService con repositorio mockeado."""
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from app.domain.entities.patient import Patient
from app.domain.exceptions import ConflictError, NotFoundError
from app.services.patient_service import PatientService


@pytest.fixture
def repo() -> MagicMock:
    return MagicMock()


@pytest.fixture
def service(repo: MagicMock) -> PatientService:
    return PatientService(repo)


def _sample_patient(**overrides) -> Patient:
    data = {
        "id": "p-1",
        "tenant_id": "default",
        "name": "Ana Pérez",
        "email": "ana@example.com",
        "phone": "0999999999",
        "identification": "1712345678",
        "created_at": datetime(2026, 1, 1, 12, 0, 0),
    }
    data.update(overrides)
    return Patient(**data)


def test_create_patient_success(service: PatientService, repo: MagicMock) -> None:
    repo.find_by_email.return_value = None
    created = _sample_patient()
    repo.save.return_value = created

    result = service.create_patient(
        {"name": "Ana Pérez", "email": "ana@example.com", "phone": "0999999999"}
    )

    assert result.email == "ana@example.com"
    repo.find_by_email.assert_called_once_with("ana@example.com", "default")
    repo.save.assert_called_once()


def test_create_patient_duplicate_email_raises_conflict(
    service: PatientService, repo: MagicMock
) -> None:
    repo.find_by_email.return_value = _sample_patient()

    with pytest.raises(ConflictError):
        service.create_patient({"name": "Ana", "email": "ana@example.com"})

    repo.save.assert_not_called()


def test_get_patient_success(service: PatientService, repo: MagicMock) -> None:
    expected = _sample_patient()
    repo.get_by_id.return_value = expected

    result = service.get_patient("p-1", "default")

    assert result.id == "p-1"
    repo.get_by_id.assert_called_once_with("p-1", "default")


def test_get_patient_not_found_raises(service: PatientService, repo: MagicMock) -> None:
    repo.get_by_id.return_value = None

    with pytest.raises(NotFoundError):
        service.get_patient("missing", "default")


def test_list_patients_pagination(service: PatientService, repo: MagicMock) -> None:
    patients = [_sample_patient(id="p-1"), _sample_patient(id="p-2", email="b@example.com")]
    repo.list_by_tenant.return_value = patients
    repo.count_by_tenant.return_value = 42

    items, total = service.list_patients("default", page=2, size=10)

    assert items == patients
    assert total == 42
    repo.list_by_tenant.assert_called_once_with("default", limit=10, offset=10)
    repo.count_by_tenant.assert_called_once_with("default")
