# MetricTide Web

Next.js 15 (App Router) frontend for MetricTide.

> Scaffolding only — structure and tooling are in place; no features yet.

## Layout

```
src/
├── app/                # App Router: layout, page, /health route handler
├── components/ui/      # presentational components (placeholder)
├── features/           # feature-sliced modules (placeholder)
├── lib/                # api client, utils
└── config/             # typed env access (zod)
```

## Scripts

```bash
pnpm --filter web dev          # dev server (http://localhost:3000)
pnpm --filter web build        # production build (standalone output)
pnpm --filter web lint         # ESLint
pnpm --filter web typecheck    # tsc --noEmit
pnpm --filter web test         # Vitest
pnpm --filter web format       # Prettier
```

## Environment

Copy `.env.example` to `.env.local`. Client-exposed variables must be prefixed
`NEXT_PUBLIC_`. Env is validated at load time in [`src/config/env.ts`](src/config/env.ts).

## Health check

`GET /health` returns `{ "status": "ok", "service": "web" }` — used to verify
routing and container startup.
