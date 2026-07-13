"""Tests del health check con Dependency Injection override (sin Postgres real)."""
from collections.abc import Generator
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.main import app


def _override_get_db_ok() -> Generator[Session, None, None]:
    session = MagicMock(spec=Session)
    session.execute.return_value = None
    yield session


def _override_get_db_fail() -> Generator[Session, None, None]:
    session = MagicMock(spec=Session)
    session.execute.side_effect = RuntimeError("connection refused")
    yield session


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_health_ok_when_database_responds(client: TestClient) -> None:
    app.dependency_overrides[get_db] = _override_get_db_ok

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "labx-core"
    assert body["database"] == "up"


def test_health_503_when_database_down(client: TestClient) -> None:
    app.dependency_overrides[get_db] = _override_get_db_fail

    response = client.get("/api/v1/health")

    assert response.status_code == 503
