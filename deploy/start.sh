#!/usr/bin/env bash
# Starts the API and nginx in one container (the shape PaaS hosts expect: one port, one process tree).
set -euo pipefail

export PORT="${PORT:-8080}"

# Which request header carries the real client IP? Leave CLIENT_IP_HEADER unset unless your host's
# edge overwrites it (e.g. Cloudflare-fronted hosts: cf-connecting-ip). Wrongly trusting a header
# lets visitors dodge the rate limiter by inventing addresses.
if [ -n "${CLIENT_IP_HEADER:-}" ]; then
  header_var="http_$(printf '%s' "$CLIENT_IP_HEADER" | tr 'A-Z-' 'a-z_')"
  export CLIENT_IP_EXPR="\$${header_var}"
else
  export CLIENT_IP_EXPR='$remote_addr'
fi

mkdir -p /tmp/nginx
envsubst '${PORT} ${CLIENT_IP_EXPR}' < /etc/nginx/nginx.conf.template > /tmp/nginx/nginx.conf

# Only nginx (on localhost) talks to uvicorn, so trusting its forwarded headers is safe.
uvicorn app.main:app --host 127.0.0.1 --port 8000 --proxy-headers --forwarded-allow-ips=127.0.0.1 &
api_pid=$!
nginx -e /dev/stderr -c /tmp/nginx/nginx.conf -g 'daemon off;' &
web_pid=$!

trap 'kill "$api_pid" "$web_pid" 2>/dev/null || true' TERM INT

# If either process dies, stop the other and exit non-zero so the platform restarts the container.
wait -n "$api_pid" "$web_pid" || true
kill "$api_pid" "$web_pid" 2>/dev/null || true
exit 1
