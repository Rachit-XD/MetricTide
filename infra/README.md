# Infrastructure

Local development infrastructure for MetricTide.

## Contents

| Path                          | Purpose                                              |
| ----------------------------- | ---------------------------------------------------- |
| `docker/api.Dockerfile`       | FastAPI service image (uv-based, Python 3.12).       |
| `docker/web.Dockerfile`       | Next.js 15 image (multi-stage, standalone output).   |
| `postgres/init/`              | SQL run on first DB boot (enables `pgvector`).       |

All services are orchestrated from the repo-root [`docker-compose.yml`](../docker-compose.yml).

## Notes

- Build contexts are the **repo root** so the images can access workspace files.
- Postgres uses the official `pgvector/pgvector:pg16` image; the init script only
  needs to run `CREATE EXTENSION`.
- Kafka is intentionally deferred — see [`docs/adr/0001-defer-kafka.md`](../docs/adr/0001-defer-kafka.md).
