FROM node:22-bookworm-slim AS frontend-builder

WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
ENV NEXT_TELEMETRY_DISABLED=1 \
    BACKEND_URL=http://127.0.0.1:8000
RUN npm run build

FROM python:3.12-slim AS backend-builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /build/backend
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    NEXT_TELEMETRY_DISABLED=1 \
    BACKEND_URL=http://127.0.0.1:8000 \
    PORT=8080 \
    PATH="/app/backend/.venv/bin:$PATH"

RUN apt-get update \
    && apt-get install -y --no-install-recommends nginx nodejs ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=backend-builder /build/backend/.venv /app/backend/.venv
COPY backend/ /app/backend/
COPY --from=frontend-builder /build/frontend/.next/standalone /app/frontend/
COPY --from=frontend-builder /build/frontend/.next/static /app/frontend/.next/static
COPY --from=frontend-builder /build/frontend/public /app/frontend/public
COPY deploy/nginx.conf /etc/nginx/nginx.conf
COPY deploy/start.sh /app/start.sh

RUN chmod +x /app/start.sh
EXPOSE 8080
CMD ["/app/start.sh"]
