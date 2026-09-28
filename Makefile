.PHONY: up down dev-db migrate seed admin backend backend-test backend-lint frontend frontend-check e2e test

up:            ## Full stack in Docker (http://localhost:3000)
	docker compose up --build -d
	docker compose exec backend python -m scripts.seed

down:
	docker compose down

dev-db:        ## Only Postgres + Redis (+ MinIO) for local development
	docker compose up -d db redis minio

migrate:
	cd backend && uv run alembic upgrade head

seed:
	cd backend && uv run python -m scripts.seed

admin:         ## make admin EMAIL=you@example.com PASSWORD=secret123
	cd backend && uv run python -m scripts.create_admin $(EMAIL) $(PASSWORD)

backend:
	cd backend && uv run uvicorn app.main:app --reload --port 8000

backend-test:
	cd backend && uv run pytest

backend-lint:
	cd backend && uv run ruff check . && uv run ruff format --check .

frontend:
	cd frontend && npm run dev

frontend-check:
	cd frontend && npm run lint && npm run typecheck && npm run test

e2e:           ## needs a running stack: backend with AI_PROVIDER=fake + seed + admin, and the frontend
	cd frontend && npx playwright test

test: backend-lint backend-test frontend-check
