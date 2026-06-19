# ADR 0001: Defer Kafka

- **Status:** Accepted
- **Date:** 2026-06-19

## Context

MetricTide will eventually ingest a high volume of signals (Reddit first, more
sources later) and run a multi-stage pipeline: ingestion → clustering → trend
detection → reporting. A streaming platform like Kafka is a natural fit for
decoupling these stages at scale.

However, at the current stage we have no ingestion volume, no consumers, and no
business logic. Introducing Kafka now would add operational complexity (broker,
topics, consumer groups, schema management) with no payoff and would slow down
local development.

## Decision

Defer Kafka. For now:

- The `web`, `api`, `postgres`, and `redis` services run via Docker Compose.
- A Kafka service definition exists in `docker-compose.yml` but is **commented
  out**.
- `app/infrastructure/messaging/` exists as the seam where a Kafka producer /
  consumer adapter will live, but contains no implementation.
- Redis can absorb lightweight queuing / task needs in the interim.

## Consequences

- **Positive:** Simpler local setup, faster iteration, fewer moving parts while
  the domain is still being shaped.
- **Negative:** When ingestion volume grows we will need to introduce Kafka and
  refactor synchronous flows into producers/consumers.
- **Revisit when:** ingestion runs on a schedule across multiple sources, stages
  need independent scaling, or we need durable replayable event history.
