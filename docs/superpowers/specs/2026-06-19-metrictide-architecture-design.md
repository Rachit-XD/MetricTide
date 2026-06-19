# MetricTide — Architecture & Scaffolding Design

- **Date:** 2026-06-19
- **Status:** Approved (scaffolding scope)

## Goal

Stand up a production-grade, modular monorepo for MetricTide — a platform that
discovers emerging technology and startup trends before they go mainstream.
This document covers the **scaffolding only**: structure, configuration, Docker,
environment management, logging, and testing support. No business logic.

## Decisions

| Decision         | Choice            | Rationale                                          |
| ---------------- | ----------------- | -------------------------------------------------- |
| Repo layout      | Single monorepo   | Atomic cross-stack changes, simple local Docker.   |
| Python packaging | uv                | Fast, reproducible, great Docker layer caching.    |
| JS tooling       | pnpm workspaces   | Fast, disk-efficient; room to add Turborepo later. |
| Streaming        | Kafka deferred    | No volume yet; see ADR 0001.                       |

## Top-level layout

```
apps/web/          Next.js 15 frontend
services/api/      FastAPI backend (clean architecture)
infra/             Dockerfiles + Postgres init
docs/              ADRs + specs
docker-compose.yml web + api + postgres(pgvector) + redis
```

## Backend: clean architecture

Dependency rule points inward (`api → application → domain`, with
`infrastructure` implementing domain ports):

- **domain** — entities + repository interfaces (ports). No external deps.
- **application** — use cases, grouped by feature: `ingestion`, `clustering`,
  `trend_detection`, `reporting` (placeholders for now).
- **infrastructure** — SQLAlchemy (async) + Alembic, Redis, pgvector, messaging
  (Kafka seam).
- **api** — FastAPI routers + Pydantic schemas. HTTP only.
- **core** — settings (pydantic-settings), structured logging (structlog),
  lifespan, request-id middleware.

`main.py` is the composition root.

## Frontend

Next.js 15 App Router, TypeScript (strict), Tailwind v4, feature-sliced `src/`
(`app/`, `components/ui/`, `features/`, `lib/`, `config/`). Typed env via zod.
Vitest + Testing Library for tests.

## Infrastructure & dev environment

- Docker Compose runs `web`, `api`, `postgres` (pgvector image), `redis`, all
  with healthchecks and named volumes.
- Single root `.env.example` documents every variable; each service ships its
  own template. Secrets never committed.

## Health checks

Trivial `/health` (web route handler) and `/api/v1/health` (FastAPI) endpoints
prove routing, Docker networking, and startup. No dependency checks yet.

## Testing

- API: pytest + httpx ASGI client (`tests/unit`, `tests/integration`).
- Web: Vitest + Testing Library.

## Out of scope (this pass)

No business logic, no real endpoints beyond health, no domain models, no auth,
no running Kafka service, no dependency installation, no container runs.

## Roadmap

Reddit ingestion → topic clustering (pgvector) → trend detection → AI reporting.
Kafka introduced when ingestion volume justifies it (ADR 0001).
