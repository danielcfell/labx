# Labx — Plataforma de citas, turnos y facturación para consultorios, laboratorios y dentistas

> **Documento:** especificación de producto + guía para Claude Code.
> **Naturaleza del proyecto:** proyecto de portafolio serio con estándares de industria, diseñado para (a) demostrar dominio backend y de arquitectura en el CV, y (b) poder venderse a negocios locales reales (consultorios, laboratorios, dentistas) en Ecuador.

---

## 0. MODO APRENDIZAJE (prioridad máxima sobre cualquier otra instrucción)

Este proyecto es **100% educativo**: el objetivo principal no es solo el código, es que el desarrollador (**mid-level, fortaleciendo backend**) entienda y pueda **defender cada decisión en una entrevista técnica**. La velocidad de entrega es secundaria frente a la comprensión.

**Antes de implementar cualquier tarea:**

- Explicar en lenguaje claro **QUÉ** se va a hacer, **POR QUÉ** de esa forma, y **qué alternativas razonables se descartaron** (y por qué).
- Si la tarea involucra un **patrón de diseño**, **principio SOLID** o concepto de **arquitectura**, nombrarlo explícitamente y dar una explicación breve, con una analogía si ayuda.
- Esperar **confirmación** antes de escribir código en tareas no triviales.

**Durante la implementación:**

- Trabajar en **pasos pequeños**: nunca generar más de **2-3 archivos** sin detenerse a explicar lo hecho.
- Comentar el código **solo donde la intención no sea obvia**; la explicación principal va en la conversación, no en comentarios ruidosos.

**Después de implementar:**

- Resumir qué archivos se crearon/modificaron y **qué papel cumple cada pieza dentro de la arquitectura** (a qué capa pertenece y por qué).
- Hacer **1-2 preguntas de verificación** al desarrollador para confirmar que entendió (ej: *"¿por qué crees que el servicio recibe la interfaz del repositorio y no la implementación?"*).
- Si el desarrollador acepta código repetidamente sin preguntar nada, **preguntarle tú si entendió** las decisiones antes de continuar.

**Reglas permanentes:**

- Si el desarrollador pregunta **"¿por qué?"**, la explicación tiene prioridad sobre seguir programando.
- Cuando el desarrollador escriba código propio y pida revisión, actuar como un **senior en code review**: señalar nombres, diseño, edge cases y mejoras, con **crudeza constructiva**.
- Al cerrar cada tarea, sugerir **1-3 líneas** para que el desarrollador anote en **`LEARNING.md`** (bitácora de conceptos aprendidos, escrita en sus propias palabras).
- Usar **español claro**; términos técnicos en inglés cuando sean el estándar de la industria (*repository, middleware*, etc.), explicados la primera vez.

---

## 1. Visión en una frase

Labx digitaliza el ciclo completo de un consultorio o laboratorio pequeño: **agendar → atender → cobrar → facturar (SRI Ecuador) → ver los números** — con recordatorios automáticos por WhatsApp que reducen inasistencias y una pantalla de turnos en tiempo real para la sala de espera.

---

## 2. El problema y el cliente

**Cliente objetivo:** consultorios médicos, dentistas y laboratorios clínicos pequeños/medianos en ciudades pequeñas de Ecuador, que hoy agendan por teléfono y cuaderno.

**Dolores reales (en orden):**

1. **Inasistencias** — pacientes que no llegan = plata perdida. Los recordatorios por WhatsApp la recuperan.
2. **Agenda caótica** — cuaderno, doble-agendamiento, "¿quién sigue?" en la sala de espera.
3. **Cobros y facturación** — facturación electrónica SRI obligatoria, cobros pendientes sin control.
4. **Cero visibilidad financiera** — no saben cuánto entra, cuánto sale, ni qué servicio/doctor genera más.
5. **Entrega de resultados (labs)** — papelitos físicos; el paciente debe volver a retirarlos.

---

## 3. Módulos funcionales

- **Agenda y citas:** calendarios por doctor/recurso, disponibilidad, agendamiento, reprogramación, estados (agendada → confirmada → atendida → no asistió).
- **Pacientes:** ficha básica, historial de citas, datos de contacto y facturación.
- **Turnos en tiempo real:** pantalla pública en sala de espera (WebSockets) con el turno actual por consultorio.
- **Notificaciones WhatsApp:** confirmación al agendar, recordatorio 24h antes, aviso de resultados listos, recordatorio de pago pendiente.
- **Módulo financiero:**
  - Catálogo de servicios con precios (consulta, limpieza, examen de sangre...).
  - Cobros ligados a la cita: método de pago, pagos parciales/abonos, cuentas por cobrar.
  - Facturación electrónica SRI Ecuador (experiencia previa de Foody reutilizable).
  - Egresos: gastos del negocio (arriendo, insumos, sueldos, servicios).
  - Dashboard: ingresos vs egresos por período, ingresos por doctor/servicio, pendientes de cobro, tasa de inasistencia.
- **Resultados de laboratorio:** subir PDF (AWS S3), el paciente recibe un link seguro por WhatsApp.
- **Usuarios y roles:** admin (dueño), recepcionista, doctor. JWT propio.

**Multi-tenant desde el día 1:** cada tabla lleva `tenant_id` (el consultorio/lab). Un despliegue puede servir a varios negocios.

---

## 4. Arquitectura (microservicios honestos: 2 servicios + eventos)

```
  React (panel web)      React Native (app doctores)     Pantalla de turnos (web)
        │                        │                              │ WebSocket
        ▼                        ▼                              ▼
  ┌──────────────────────────────────┐        ┌─────────────────────────────┐
  │  CORE — FastAPI (Python)          │ eventos │  NOTIFY — Nest.js (Node/TS) │
  │  · Citas, pacientes, agenda       │ ──────► │  · Consumidor de eventos     │
  │  · Finanzas: cobros, SRI, gastos  │  Redis  │  · WhatsApp (recordatorios)  │
  │  · Auth JWT + roles + multi-tenant│ pub/sub │  · WebSockets (turnos live)  │
  │  · OpenAPI (docs automáticas)     │        │  · Scheduler (recordatorio 24h)│
  └──────────────────────────────────┘        └─────────────────────────────┘
             │                                          │
             ▼                                          │
     PostgreSQL (datos + SQL de reportería)             │
     AWS S3 (PDFs de resultados) ◄──────────────────────┘

  Docker + docker-compose (orquestación local) · GitHub Actions (CI/CD) · Deploy: Render/Cloud Run + Vercel
```

**Por qué DOS servicios (justificación defendible en entrevista):**

- El **core** es CRUD transaccional síncrono (citas, dinero) → **FastAPI**.
- Las **notificaciones y el tiempo real** son asíncronos por naturaleza (colas, scheduling, WebSockets) → **Nest.js**.
- Se comunican por **eventos (Redis pub/sub):** `cita.creada`, `cita.recordatorio`, `pago.recibido`, `resultado.listo`. El core no sabe ni le importa cómo se notifica — desacoplamiento real.
- **NO más servicios.** Dos con razón > diez por moda. (Kafka y Kubernetes son el mismo patrón a escala masiva; aquí Redis y docker-compose son la escala correcta.)

---

## 5. Stack definitivo

| Pieza | Tecnología | Rol |
|---|---|---|
| Core API | Python + FastAPI | Citas, pacientes, finanzas, auth |
| Servicio de notificaciones | Node + Nest.js (TypeScript) | Eventos, WhatsApp, WebSockets, scheduler |
| Mensajería | Redis pub/sub | Comunicación entre servicios (patrón event-driven) |
| Panel web | React + TypeScript (Vite) | Recepción y administración |
| App móvil | React Native | Agenda del doctor (fase posterior) |
| Base de datos | PostgreSQL | Datos + reportería SQL avanzada |
| Archivos | AWS S3 | PDFs de resultados de laboratorio |
| Auth | JWT propio (access + refresh, roles) | Sin BaaS: implementación manual para aprender |
| Docs API | OpenAPI (automático en FastAPI) | Contratos claros |
| Contenedores | Docker + docker-compose | Todo el sistema con un comando |
| CI/CD | GitHub Actions | Lint + tests + build + deploy |
| Despliegue | Render o Google Cloud Run (servicios) + Vercel (web) | Tiers gratuitos |
| WhatsApp | WhatsApp Cloud API (Meta) o Twilio | Recordatorios y links |

**Explícitamente fuera:** Django (redundante con FastAPI), Kafka (Redis cubre el patrón), Kubernetes (docker-compose cubre el concepto), Azure/Nuxt/Vue (solo conocimiento conversacional), cualquier BaaS para auth (el JWT se implementa a mano, es parte del aprendizaje).

---

## 6. Estándares de ingeniería (el corazón del aprendizaje)

### Clean architecture (en el core FastAPI)

Capas estrictas, dependencias apuntando hacia adentro:

```
app/
  api/            # rutas/controladores (FastAPI routers) — capa delgada
  services/       # casos de uso / lógica de aplicación
  domain/         # entidades y lógica de negocio PURA (sin FastAPI, sin SQL)
  repositories/   # acceso a datos (interfaz + implementación PostgreSQL)
  infrastructure/ # SRI, S3, Redis, config
```

- Las rutas **NO** contienen lógica de negocio; solo validan, delegan y responden.
- `domain/` no importa nada de FastAPI ni SQLAlchemy — testeable sin infraestructura.

### SOLID y patrones de diseño (aplicados, no decorativos)

- **Repository pattern:** el servicio depende de una interfaz, no de PostgreSQL.
- **Dependency Injection:** vía el sistema de dependencias de FastAPI.
- **Strategy:** canales de notificación (WhatsApp hoy, email/SMS mañana) tras una interfaz común.
- **Factory** para la generación de comprobantes SRI.
- Cada patrón se usa donde resuelve un problema real; ninguno "por poner".

### Programación funcional

- La lógica de dominio (cálculo de disponibilidad, totales, estados de cuenta) se escribe con **funciones puras sobre datos inmutables** → entrada → salida, sin efectos.
- Efectos secundarios (BD, red, S3) viven solo en repositorios/infraestructura.
- En React: estado inmutable, transformaciones con `map`/`filter`/`reduce`.

### TDD / BDD

- **TDD estricto en el dinero y la disponibilidad:** test primero para cálculo de totales, abonos, saldos, solapamiento de citas, cambios de estado. Un bug aquí destruye la confianza del cliente.
- **BDD ligero:** las reglas de negocio críticas se documentan como escenarios Given/When/Then (pytest-bdd o docstrings estructurados). Ej: *Dado un paciente con cita mañana a las 10h, cuando pasan las 10h del día anterior, entonces se emite el evento `cita.recordatorio`.*
- **Cobertura objetivo:** dominio y servicios ≥ 80%. Las rutas se cubren con tests de integración.

### API REST + OpenAPI + JWT

- Recursos y verbos correctos (`GET /appointments`, `POST /payments`), códigos de estado apropiados, paginación, versionado (`/api/v1`).
- **OpenAPI como contrato:** modelos Pydantic completos → `/docs` impecable.
- **JWT implementado a mano:** access token corto + refresh token, roles en claims, middleware de autorización por rol y por tenant.

### SQL de reportería (gimnasio de SQL)

Consultas escritas en **SQL real** (no solo ORM) para:

- Ingresos vs egresos por período (agregaciones por mes/semana).
- Ingresos por doctor y por servicio (JOINs + GROUP BY + window functions).
- Tasa de inasistencia por doctor y franja horaria.
- Ocupación de agenda (huecos vs citas) — CTEs y `generate_series`.
- Cuentas por cobrar con antigüedad de saldos.

### CI/CD (GitHub Actions)

- En cada push a PR: lint (ruff / eslint) + tests de ambos servicios.
- En merge a main: build de imágenes Docker + deploy automático a Render/Cloud Run + deploy del panel a Vercel.

### Metodología ágil (aplicada al propio desarrollo)

- Tablero en GitHub Projects: backlog → sprint → done.
- Sprints de 1-2 semanas con objetivo demoable.
- Cada fase del roadmap = un "release" etiquetado.

---

## 7. Modelo de datos (entidades núcleo)

> Todas las tablas de negocio incluyen `tenant_id` + `created_at`.

- **tenant** — el consultorio/laboratorio (nombre, tipo, config SRI).
- **user** — con rol: admin, receptionist, doctor (hash de contraseña, JWT propio).
- **doctor** — perfil profesional ligado a user (especialidad, color de agenda).
- **patient** — ficha del paciente (datos de contacto, identificación para facturar).
- **service** — catálogo con precios (consulta, limpieza, examen...).
- **schedule** — disponibilidad por doctor (día de semana, franjas).
- **appointment** — cita (`doctor_id`, `patient_id`, `service_id`, inicio/fin, estado: scheduled/confirmed/attended/no_show/cancelled).
- **queue_ticket** — turno del día para la pantalla en vivo (número, estado).
- **charge** — cobro ligado a cita o venta directa (líneas de servicio, total).
- **payment** — pagos/abonos sobre un charge (método, monto, fecha) → saldo = total − Σ pagos.
- **invoice** — factura electrónica SRI (estado de autorización, XML/clave de acceso).
- **expense** — egresos (categoría, monto, fecha, descripción).
- **lab_result** — resultado (`patient_id`, archivo S3, estado, token de acceso público).
- **notification_log** — registro de notificaciones enviadas (tipo, canal, estado).
- **event_outbox** — eventos pendientes de publicar (patrón outbox para consistencia).

---

## 8. Roadmap por fases (cada fase termina demoable)

1. **Fase 1 — Core de citas (FastAPI):** clean architecture montada, JWT + roles, multi-tenant, CRUD de doctores/pacientes/servicios, agenda con detección de solapamientos (TDD), OpenAPI completo, docker-compose (api + postgres), CI con tests. Deploy en Render desde la semana 1.
2. **Fase 2 — Eventos + Notificaciones (Nest.js + Redis):** publicar eventos desde el core (outbox), servicio Nest.js consumidor, WhatsApp (confirmación + recordatorio 24h con scheduler), pantalla de turnos con WebSockets.
3. **Fase 3 — Módulo financiero:** cobros, pagos parciales, cuentas por cobrar, facturación SRI, egresos, dashboard financiero con la reportería SQL avanzada.
4. **Fase 4 — Resultados de laboratorio + AWS:** subida de PDFs a S3, links seguros por WhatsApp, descarga del paciente.
5. **Fase 5 — App móvil (React Native):** agenda del día del doctor, notificaciones push.

**Transversal:** CD completo, seed de datos demo realistas, README de calidad con capturas y diagrama.

---

## 9. Guía para Claude Code (cómo trabajar en este repo)

- **Monorepo** con `core/` (FastAPI), `notify/` (Nest.js), `web/` (React), `mobile/` (React Native, fase 5), `docker-compose.yml` en la raíz.
- **Trabaja por fases y por sprints.** No empieces una fase sin terminar y probar la anterior. Cada PR pequeño y con propósito.
- **TDD en dominio y dinero:** para lógica de disponibilidad, totales, saldos y estados: primero el test, luego la implementación.
- **Respeta las capas:** nada de SQL en rutas, nada de FastAPI en `domain/`. Si una dependencia apunta hacia afuera, está mal.
- **Multi-tenant siempre:** ninguna consulta sin `tenant_id`. Tests que lo verifiquen.
- **Eventos con patrón outbox** para no perder notificaciones si Redis está caído.
- **SQL de reportes en archivos `.sql` o funciones dedicadas** — visibles y revisables, no escondidos en el ORM.
- **Secretos por variables de entorno,** `.env.example` versionado, secretos reales jamás en el repo.
- **Datos demo:** script de seed con un consultorio ficticio realista (3 doctores, 200 pacientes, 3 meses de citas y cobros) para que la demo y los reportes luzcan.
- **README primero-clase:** qué es, diagrama de arquitectura, cómo levantar con `docker compose up`, capturas. El README es la carta de presentación del CV.
- **Antes de decisiones grandes de arquitectura, propón y espera confirmación.**

---

## 10. Criterio de éxito

- `docker compose up` levanta todo el sistema en cualquier máquina.
- La suite de tests pasa en CI y cubre el dominio crítico.
- Demo desplegada y navegable con datos ficticios (link en el CV).
- El README permite a un reclutador técnico entender la arquitectura en 2 minutos.
- **(Bonus de negocio)** Un consultorio o laboratorio real de la zona lo prueba.

---

> **Norte:** Labx existe para demostrar ingeniería de nivel profesional — arquitectura limpia, eventos, tests, CI/CD — sobre un problema real de tu ciudad. **Profundidad sobre amplitud:** cada fase terminada vale más que tres a medias.
