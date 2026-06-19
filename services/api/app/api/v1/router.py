"""Aggregates all v1 routers under a single APIRouter."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.routes import health, ingestion, topics

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(ingestion.router, prefix="/ingestion", tags=["ingestion"])
api_router.include_router(topics.router, prefix="/topics", tags=["topics"])

# Future feature routers are registered here, e.g.:
# api_router.include_router(trends.router, prefix="/trends", tags=["trends"])
