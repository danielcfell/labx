"""Conexión a PostgreSQL y sesión por request (Dependency Injection).

Vive en infrastructure: conoce SQLAlchemy. domain/ no importa esto.
"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.infrastructure.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base declarativa para modelos ORM (futuras tablas)."""


def get_db() -> Generator[Session, None, None]:
    """Inyecta una sesión SQLAlchemy por request y la cierra al terminar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
