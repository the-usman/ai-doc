# AI-Doc

A multi-application developer platform with shared single sign-on, PostgreSQL, and a React platform shell. Phase 1 delivers authentication, Docker, CI, and living documentation inside the product.

## Stack

- **Frontend:** React 18, Vite, TypeScript
- **Backend:** FastAPI, psycopg
- **Data:** PostgreSQL (pgvector image), Redis
- **Ops:** Docker Compose, GitHub Actions, Dokploy (production)

## Run locally

1. Copy `.env.example` to `.env` and set database credentials plus Google OAuth values.
2. Register OAuth redirect URI: `http://localhost:3000/api/auth/callback/google`
3. From the project root:

```bash
docker compose up --build
```

4. Open [http://localhost:3000](http://localhost:3000) and sign in.

API only (no UI): [http://localhost:8000/health](http://localhost:8000/health)

## Tests

```bash
docker compose run --rm api pytest
docker compose run --rm web npm test
```

## Deploy

Use `docker/docker-compose.prod.yml` in Dokploy with secrets from the panel. Build image from root `Dockerfile`.

## Documentation

- Programme overview: `00-overview.md`
- Phase guides: `01-phase-1-foundations.md`, …
- ADRs: `docs/adr/`
- In-app Docs application: Architecture, Decisions, Runbook

## Platform applications (Phase 1)

| App  | Path    | Sub-pages                          |
|------|---------|------------------------------------|
| Home | `/`     | Overview, Settings               |
| Docs | `/docs` | Architecture, Decisions, Runbook, API Reference |

Register new apps in `frontend/src/platform/appRegistry.ts`.
