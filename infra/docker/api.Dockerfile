# =============================================================================
# FastAPI service image
# Build context is the repo root; sources live under services/api.
# =============================================================================
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/usr/local

# uv: fast Python package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# ---- Dependency layer (cached unless lock/manifest changes) ----
COPY services/api/pyproject.toml services/api/uv.lock* ./
RUN uv sync --no-install-project --no-dev || uv sync --no-dev

# ---- Application source ----
COPY services/api/ ./

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
