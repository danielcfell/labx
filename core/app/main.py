"""Punto de entrada de la Core API (FastAPI).

Capa de composición: crea la app, monta routers y expone OpenAPI en /docs.
No contiene lógica de negocio — solo ensambla.
"""
from fastapi import FastAPI

from app.api.v1.router import api_router
from app.infrastructure.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Labx Core API",
    version="0.1.0",
    description="Citas, pacientes, agenda y finanzas para consultorios y laboratorios.",
    docs_url="/docs",
    openapi_url="/api/v1/openapi.json",
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {"service": "labx-core", "docs": "/docs"}
