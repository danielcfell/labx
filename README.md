# Labx

**Plataforma de citas, turnos y facturación para consultorios, laboratorios y dentistas.**

Labx digitaliza el ciclo completo de un consultorio o laboratorio pequeño:
**agendar → atender → cobrar → facturar (SRI Ecuador) → ver los números** — con
recordatorios automáticos por WhatsApp que reducen inasistencias y una pantalla de
turnos en tiempo real para la sala de espera.

> Proyecto de portafolio con estándares de industria: clean architecture, arquitectura
> orientada a eventos, TDD en el dominio crítico, multi-tenant desde el día 1 y CI/CD.
> Pensado también para venderse a negocios reales en Ecuador.

---

## El problema

Consultorios médicos, dentistas y laboratorios clínicos pequeños en Ecuador hoy
agendan por teléfono y cuaderno. Los dolores reales, en orden:

1. **Inasistencias** — el paciente no llega = plata perdida. Los recordatorios por WhatsApp la recuperan.
2. **Agenda caótica** — doble-agendamiento, "¿quién sigue?" en la sala de espera.
3. **Cobros y facturación** — facturación electrónica SRI obligatoria, cuentas por cobrar sin control.
4. **Cero visibilidad financiera** — no saben cuánto entra, cuánto sale, ni qué servicio o doctor rinde más.
5. **Entrega de resultados (labs)** — papelitos físicos; el paciente debe volver a retirarlos.

---

## Arquitectura

Microservicios honestos: **dos servicios con una razón**, comunicados por eventos.

```
  React (panel web)      React Native (app doctores)     Pantalla de turnos (web)
        │                        │                              │ WebSocket
        ▼                        ▼                              ▼
  ┌──────────────────────────────────┐  eventos  ┌─────────────────────────────┐
  │  CORE — FastAPI (Python)          │ ────────► │  NOTIFY — Nest.js (Node/TS)  │
  │  · Citas, pacientes, agenda       │  Redis    │  · Consumidor de eventos     │
  │  · Finanzas: cobros, SRI, gastos  │  pub/sub  │  · WhatsApp (recordatorios)  │
  │  · Auth JWT + roles + multi-tenant│           │  · WebSockets (turnos live)  │
  │  · OpenAPI (docs automáticas)     │           │  · Scheduler (recordatorio 24h)│
  └──────────────────────────────────┘           └─────────────────────────────┘
             │                                            │
             ▼                                            │
     PostgreSQL (datos + SQL de reportería)               │
     AWS S3 (PDFs de resultados) ◄────────────────────────┘
```

**¿Por qué dos servicios?**

- El **core** es CRUD transaccional síncrono (citas, dinero) → **FastAPI**.
- Las **notificaciones y el tiempo real** son asíncronos por naturaleza (colas, scheduling, WebSockets) → **Nest.js**.
- Se comunican por **eventos (Redis pub/sub):** `cita.creada`, `cita.recordatorio`, `pago.recibido`, `resultado.listo`. El core no sabe cómo se notifica — desacoplamiento real.
- **No más servicios.** Dos con razón valen más que diez por moda.

### Clean architecture en el core

Capas estrictas, las dependencias apuntan **hacia adentro**:

```
core/app/
  api/            # rutas/controladores (FastAPI routers) — capa delgada
  services/       # casos de uso / lógica de aplicación
  domain/         # entidades y lógica de negocio PURA (sin FastAPI, sin SQL)
  repositories/   # acceso a datos (interfaz + implementación PostgreSQL)
  infrastructure/ # config, base de datos, SRI, S3, Redis
```

Regla de oro: `domain/` no importa nada de FastAPI ni SQLAlchemy — es testeable sin
infraestructura. Las rutas no contienen lógica de negocio: validan, delegan y responden.
Los servicios dependen de **interfaces** de repositorio (Repository pattern + Dependency
Injection), no de PostgreSQL.

---

## Stack

| Pieza | Tecnología | Rol |
|---|---|---|
| Core API | Python + FastAPI | Citas, pacientes, finanzas, auth |
| Notificaciones | Node + Nest.js (TypeScript) | Eventos, WhatsApp, WebSockets, scheduler |
| Mensajería | Redis pub/sub | Comunicación entre servicios (event-driven) |
| Base de datos | PostgreSQL | Datos + reportería SQL avanzada |
| Migraciones | Alembic | Versionado del esquema |
| Panel web | React + TypeScript (Vite) | Recepción y administración |
| App móvil | React Native | Agenda del doctor (fase posterior) |
| Archivos | AWS S3 | PDFs de resultados de laboratorio |
| Auth | JWT propio (access + refresh, roles) | Implementación manual, sin BaaS |
| Docs API | OpenAPI (automático en FastAPI) | Contratos claros |
| Contenedores | Docker + docker-compose | Todo el sistema con un comando |
| CI/CD | GitHub Actions | Lint + tests + build + deploy |

---

## Cómo levantarlo

Requisitos: Docker y Docker Compose.

```bash
git clone https://github.com/danielcfell/labx.git
cd labx
cp .env.example .env
docker compose up --build
```

Luego aplica las migraciones (con los contenedores arriba):

```bash
docker compose exec api alembic upgrade head
```

| | |
|---|---|
| API | http://localhost:8000 |
| Docs OpenAPI | http://localhost:8000/docs |
| Health check | http://localhost:8000/api/v1/health (incluye ping a Postgres) |

### Sin Docker (solo el core)

```bash
cd core
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Tests

```bash
cd core
pytest
```

---

## Estado del proyecto

Fase 1 (core de citas) en progreso. Estado real, sin humo:

**Ya funciona**
- [x] Scaffold de clean architecture en el core (FastAPI)
- [x] PostgreSQL + Alembic (migraciones versionadas)
- [x] Multi-tenant desde el esquema (`tenant_id` en las tablas de negocio)
- [x] CRUD de **pacientes** completo por capas (domain → repository → service → API)
- [x] Health check con ping a la base de datos
- [x] OpenAPI automático en `/docs`
- [x] Tests unitarios (servicio) e integración (API)
- [x] `docker compose up` levanta API + Postgres

**En camino (Fase 1)**
- [ ] Auth JWT propio (access + refresh) + roles + autorización por tenant
- [ ] CRUD de doctores y servicios
- [ ] Agenda con detección de solapamientos (TDD)
- [ ] CI con tests en GitHub Actions
- [ ] Deploy en Render

### Roadmap por fases

| Fase | Objetivo demoable |
|---|---|
| **1 — Core de citas** | Clean architecture, JWT + roles, multi-tenant, CRUD, agenda con solapamientos, OpenAPI, docker-compose, CI |
| **2 — Eventos + Notificaciones** | Outbox en el core, servicio Nest.js consumidor, WhatsApp (confirmación + recordatorio 24h), pantalla de turnos con WebSockets |
| **3 — Módulo financiero** | Cobros, pagos parciales, cuentas por cobrar, facturación SRI, egresos, dashboard con reportería SQL |
| **4 — Resultados de laboratorio** | Subida de PDFs a S3, links seguros por WhatsApp, descarga del paciente |
| **5 — App móvil** | Agenda del día del doctor (React Native), notificaciones push |

---

## Estándares de ingeniería

- **Clean architecture** con dependencias hacia adentro; el dominio no conoce la infraestructura.
- **SOLID y patrones aplicados, no decorativos:** Repository, Dependency Injection, Strategy (canales de notificación), Factory (comprobantes SRI).
- **Programación funcional** en el dominio: funciones puras sobre datos inmutables; los efectos viven en repositorios/infraestructura.
- **TDD estricto en el dinero y la disponibilidad:** test primero para totales, abonos, saldos y solapamiento de citas.
- **Multi-tenant siempre:** ninguna consulta sin `tenant_id`.
- **Eventos con patrón outbox** para no perder notificaciones si Redis está caído.
- **SQL de reportería en archivos/funciones dedicadas**, no escondido en el ORM.

---

## Estructura del repositorio

```
labx/
  core/              # Core API (FastAPI) — citas, pacientes, finanzas, auth
  notify/            # Servicio de notificaciones (Nest.js) — fase 2
  web/               # Panel web (React) — fase posterior
  mobile/            # App móvil (React Native) — fase 5
  docker-compose.yml # Orquestación local (api + postgres)
```

---

## Licencia

Proyecto de portafolio. Todos los derechos reservados por el autor.
