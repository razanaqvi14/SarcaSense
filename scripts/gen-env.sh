#!/usr/bin/env bash
# Creates .env with freshly generated secrets. Refuses to overwrite an existing one.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -e .env ]; then
  echo ".env already exists; leaving it untouched." >&2
  exit 1
fi

umask 077
sed -e "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$(openssl rand -hex 24)|" \
    -e "s|^SECRET_KEY=.*|SECRET_KEY=$(openssl rand -hex 32)|" \
    .env.example > .env
echo "Created .env (COOKIE_SECURE=false for local http; set true behind HTTPS)."
