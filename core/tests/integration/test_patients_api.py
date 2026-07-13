"""Tests de integración del API de pacientes (SQLite en memoria + rollback)."""
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.infrastructure.database import Base, get_db
from app.main import app


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
        session.rollback()
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_create_patient_returns_201(client: TestClient) -> None:
    response = client.post(
        "/api/v1/patients/",
        json={"name": "Ana Pérez", "email": "ana@example.com", "phone": "099"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Ana Pérez"
    assert body["email"] == "ana@example.com"
    assert body["tenant_id"] == "default"
    assert body["id"]


def test_list_patients_returns_paginated_200(client: TestClient) -> None:
    client.post("/api/v1/patients/", json={"name": "A", "email": "a@example.com"})
    client.post("/api/v1/patients/", json={"name": "B", "email": "b@example.com"})

    response = client.get("/api/v1/patients/?page=1&size=1")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["page"] == 1
    assert body["size"] == 1
    assert body["pages"] == 2
    assert len(body["items"]) == 1


def test_get_patient_by_id_returns_200(client: TestClient) -> None:
    created = client.post(
        "/api/v1/patients/",
        json={"name": "Ana", "email": "ana2@example.com"},
    ).json()

    response = client.get(f"/api/v1/patients/{created['id']}")
    assert response.status_code == 200
    assert response.json()["email"] == "ana2@example.com"


def test_create_duplicate_email_returns_409(client: TestClient) -> None:
    payload = {"name": "Ana", "email": "dup@example.com"}
    assert client.post("/api/v1/patients/", json=payload).status_code == 201
    response = client.post("/api/v1/patients/", json=payload)
    assert response.status_code == 409
