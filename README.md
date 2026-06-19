# MetricTide

> Discover emerging technology and startup trends before they go mainstream.

MetricTide is a platform that ingests signals from public sources (Reddit first),
clusters them into topics, detects rising trends, and produces AI-generated reports.

This repository is a **monorepo** containing the web frontend, the API/backend
service, and the infrastructure needed to run everything locally with Docker.

> **Status:** Scaffolding only. No business logic is implemented yet. The structure
> is designed to support upcoming features: Reddit ingestion, topic clustering,
> trend detection, and AI reporting.

---

## Tech Stack

| Layer            | Technology                                  |
| ---------------- | ------------------------------------------- |
| Frontend         | Next.js 15 (App Router), TypeScript, Tailwind |
| Backend / API    | FastAPI, Python 3.12, clean architecture    |
| Database         | PostgreSQL 16 + `pgvector`                  |
| Cache / queue    | Redis 7                                     |
| Streaming        | Kafka *(deferred — placeholder only)*       |
| Packaging (JS)   | pnpm workspaces                             |
| Packaging (Py)   | uv                                          |
| Containerization | Docker + Docker Compose                     |

---

## Repository Layout

```
MetricTide/
├── apps/
│   └── web/                  # Next.js 15 frontend
├── services/
│   └── api/                  # FastAPI backend (clean architecture)
├── infra/
│   ├── docker/               # Dockerfiles
│   └── postgres/             # DB init scripts (pgvector extension)
├── docs/
│   ├── adr/                  # Architecture Decision Records
│   └── superpowers/specs/    # Design specs
├── .github/workflows/        # CI pipelines
├── docker-compose.yml        # Local dev orchestration
├── pnpm-workspace.yaml
├── .env.example              # Root env template (see Environment section)
└── Makefile                  # Common dev shortcuts
```

See [`apps/web/README.md`](apps/web/README.md) and
[`services/api/README.md`](services/api/README.md) for service-specific details.

---

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) + Docker Compose v2
- [Node.js](https://nodejs.org/) 20+ and [pnpm](https://pnpm.io/) 9+ (for local web dev)
- [uv](https://docs.astral.sh/uv/) (for local API dev)
- `make` (optional, for the shortcuts below)

---

## Quick Start (Docker)

```bash
# 1. Create your local env file from the template
cp .env.example .env

# 2. Start the full stack (web + api + postgres + redis)
docker compose up --build

# 3. Verify the services are healthy
curl http://localhost:8000/api/v1/health   # FastAPI
curl http://localhost:3000/health          # Next.js
```

| Service  | URL                          |
| -------- | ---------------------------- |
| Web      | http://localhost:3000        |
| API      | http://localhost:8000        |
| API docs | http://localhost:8000/docs   |
| Postgres | localhost:5432               |
| Redis    | localhost:6379               |

---

## Local Development (without Docker)

### Frontend

```bash
pnpm install              # from repo root (installs all workspaces)
pnpm --filter web dev
```

### Backend

```bash
cd services/api
uv sync                   # create venv + install deps
uv run uvicorn app.main:app --reload
```

---

## Make Shortcuts

```bash
make up          # docker compose up --build
make down        # docker compose down
make logs        # tail all service logs
make web-dev     # run Next.js dev server locally
make api-dev     # run FastAPI dev server locally
make test        # run all tests (web + api)
make lint        # lint everything
make fmt         # format everything
```

---

## Environment Variables

All configuration is driven by environment variables. The root
[`.env.example`](.env.example) documents every variable used by Docker Compose.
Each service also ships its own template:

- [`apps/web/.env.example`](apps/web/.env.example)
- [`services/api/.env.example`](services/api/.env.example)

**Never commit real secrets.** `.env` files are git-ignored.

---

## Testing

- **Web:** Vitest + Testing Library — `pnpm --filter web test`
- **API:** pytest — `cd services/api && uv run pytest`

---

## Roadmap

This scaffold is built to grow into:

1. **Reddit ingestion** — pull signals from public subreddits.
2. **Topic clustering** — group signals using `pgvector` embeddings.
3. **Trend detection** — surface rising topics over time.
4. **AI reporting** — generate digestible trend reports.

Kafka will be introduced when ingestion volume justifies a streaming pipeline
(see [`docs/adr/0001-defer-kafka.md`](docs/adr/0001-defer-kafka.md)).
