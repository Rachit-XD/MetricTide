# MetricTide API

FastAPI backend for MetricTide, organized with **clean architecture**.

> Scaffolding only — the layers exist and are wired together, but contain no
> business logic yet.

## Architecture

The dependency rule points **inward**. Outer layers depend on inner layers,
never the reverse:

```
   api  ──▶  application  ──▶  domain  ◀──  infrastructure
 (HTTP)      (use cases)     (entities,      (DB, cache,
                              ports)          vector, messaging)
```

| Layer            | Package                  | Responsibility                                            | May import          |
| ---------------- | ------------------------ | --------------------------------------------------------- | ------------------- |
| **Domain**       | `app/domain`             | Entities and repository interfaces (ports). Pure Python.  | nothing internal    |
| **Application**  | `app/application`        | Use cases / orchestration. Depends on domain ports only.  | `domain`            |
| **Infrastructure** | `app/infrastructure`   | Concrete adapters: SQLAlchemy, Redis, pgvector, messaging.| `domain`            |
| **API**          | `app/api`                | HTTP routers + request/response schemas.                  | `application`, `core` |
| **Core**         | `app/core`               | Cross-cutting: settings, logging, app lifespan.           | —                   |

`main.py` is the **composition root**: it wires routers, middleware, logging,
and the lifespan together.

## Layout

```
app/
├── main.py                  # app factory / composition root
├── core/                    # config, logging, lifespan
├── api/v1/                  # routers + schemas (HTTP only)
├── domain/                  # entities + repository ports
├── application/             # use cases (ingestion, clustering, ...)
└── infrastructure/          # db, cache, vector, messaging adapters
migrations/                  # Alembic
tests/                       # pytest (unit + integration)
```

The `application/use_cases/` package contains empty placeholders for the
planned features: `ingestion`, `clustering`, `trend_detection`, `reporting`.

## Local development

```bash
uv sync                                       # create venv + install deps
cp .env.example .env                          # configure
uv run uvicorn app.main:app --reload          # http://localhost:8000
```

API docs: http://localhost:8000/docs · Health: http://localhost:8000/api/v1/health

## Quality

```bash
uv run ruff check .       # lint
uv run ruff format .      # format
uv run mypy app           # type-check
uv run pytest             # tests
```

## Migrations

Alembic is configured but ships with **no migrations yet**.

```bash
uv run alembic revision --autogenerate -m "message"
uv run alembic upgrade head
```
