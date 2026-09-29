#!/bin/sh
set -eu

cd /app/backend
alembic upgrade head
python -m scripts.seed
uvicorn app.main:app --host 127.0.0.1 --port 8000 --proxy-headers --forwarded-allow-ips='*' &

cd /app/frontend
HOSTNAME=127.0.0.1 PORT=3000 node server.js &

exec nginx -g 'daemon off;'
