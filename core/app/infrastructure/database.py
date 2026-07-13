"""Conexión a PostgreSQL y sesión por request (Dependency Injection).

Vive en infrastructure: conoce SQLAlchemy. domain/ no importa esto.
"""
from collections.abc import Generator
from typing import Any, Dict

from sqlalchemy import DateTime, String, UniqueConstraint, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, mapped_column, sessionmaker

from app.domain.entities.patient import Patient
from app.infrastructure.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base declarativa para modelos ORM (futuras tablas)."""


class PatientModel(Base):
    __tablename__ = "patients"
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_patients_tenant_email"),
    )

    # Sin Mapped[T | None]: SQLAlchemy 2.0.36 + Python 3.14 falla al parsear unions.
    id = mapped_column(String(36), primary_key=True)
    tenant_id = mapped_column(String(64), nullable=False, index=True)
    name = mapped_column(String(255), nullable=False)
    email = mapped_column(String(255), nullable=False)
    phone = mapped_column(String(50), nullable=True)
    identification = mapped_column(String(64), nullable=True)
    created_at = mapped_column(DateTime, nullable=False)


def patient_model_to_domain(model: PatientModel) -> Patient:
    return Patient(
        id=model.id,
        tenant_id=model.tenant_id,
        name=model.name,
        email=model.email,
        phone=model.phone,
        identification=model.identification,
        created_at=model.created_at,
    )


def patient_domain_to_dict(patient: Patient) -> Dict[str, Any]:
    return patient.to_dict()


def get_db() -> Generator[Session, None, None]:
    """Inyecta una sesión SQLAlchemy por request y la cierra al terminar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
