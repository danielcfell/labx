# Labx — Core API (FastAPI)

Servicio central: citas, pacientes, agenda, finanzas y auth. Clean architecture.

## Estructura (clean architecture)

```
app/
  api/            # rutas/controladores (routers) — capa delgada
  services/       # casos de uso / lógica de aplicación
  domain/         # entidades y lógica de negocio PURA (sin FastAPI, sin SQL)
  repositories/   # acceso a datos (interfaz + implementación PostgreSQL)
  infrastructure/ # config, SRI, S3, Redis
```

Regla de oro: las dependencias apuntan hacia adentro. `domain/` no importa nada de
FastAPI ni SQLAlchemy. Las rutas no contienen lógica de negocio.

## Correr con Docker (desde la raíz del repo)

```bash
cp .env.example .env
docker compose up --build
```

- API: http://localhost:8000
- Docs OpenAPI: http://localhost:8000/docs
- Health check: http://localhost:8000/api/v1/health (incluye ping a Postgres)

## Migraciones (Alembic)

Desde la raíz del repo, con los contenedores arriba:

```bash
docker compose exec api alembic upgrade head
```

Crear una nueva revisión (cuando haya modelos ORM):

```bash
docker compose exec api alembic revision --autogenerate -m "describe el cambio"
docker compose exec api alembic upgrade head
```

Si corres Alembic en el host (sin Docker), apunta `DATABASE_URL` a `localhost` en lugar de `postgres`.

## Correr en local (sin Docker)

```bash
cd core
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Tests

```bash
cd core
pytest
```
