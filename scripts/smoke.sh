#!/bin/sh
set -eu

root="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
cd "$root"

if docker compose version >/dev/null 2>&1; then
  compose="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
  compose="docker-compose"
else
  echo "Docker Compose is required" >&2
  exit 1
fi

export COMPOSE_BAKE="${COMPOSE_BAKE:-false}"
export CLICKHOUSE_PASSWORD="${CLICKHOUSE_PASSWORD:-$(openssl rand -hex 24)}"
export LOGCHEF_ADMIN_EMAIL="${LOGCHEF_ADMIN_EMAIL:-admin@example.test}"
export LOGCHEF_ADMIN_PASSWORD="${LOGCHEF_ADMIN_PASSWORD:-$(openssl rand -base64 30 | tr -d '\n')}"
export LOGCHEF_API_TOKEN_SECRET="${LOGCHEF_API_TOKEN_SECRET:-$(openssl rand -hex 32)}"
export LOGCHEF_QUERY_MARKER="${LOGCHEF_QUERY_MARKER:-railway-logchef-smoke-$(date +%s)}"
export LOGCHEF_URL="${LOGCHEF_URL:-http://127.0.0.1:18125}"

cleanup() {
  $compose down --volumes --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

cleanup
$compose up --detach --build

attempt=1
while [ "$attempt" -le 120 ]; do
  if $compose exec -T logchef wget --quiet --spider http://127.0.0.1:8125/api/v1/health >/dev/null 2>&1; then
    break
  fi
  if [ "$attempt" -eq 120 ]; then
    $compose logs
    echo "LogChef did not become healthy" >&2
    exit 1
  fi
  attempt=$((attempt + 1))
  sleep 2
done

$compose exec -T clickhouse clickhouse-client \
  --user logchef \
  --password "$CLICKHOUSE_PASSWORD" \
  --query "INSERT INTO default.logs FORMAT JSONEachRow" <<EOF
{"timestamp":"$(date -u +%Y-%m-%dT%H:%M:%S.000)","severity_text":"INFO","severity_number":9,"service_name":"template-smoke","namespace":"railway","body":"${LOGCHEF_QUERY_MARKER}","log_attributes":{"test":"local"}}
EOF

$compose run --build --rm --no-deps -T smoke
$compose restart logchef >/dev/null

attempt=1
while [ "$attempt" -le 60 ]; do
  if $compose exec -T logchef wget --quiet --spider http://127.0.0.1:8125/api/v1/health >/dev/null 2>&1; then
    break
  fi
  if [ "$attempt" -eq 60 ]; then
    $compose logs logchef
    echo "LogChef did not recover after restart" >&2
    exit 1
  fi
  attempt=$((attempt + 1))
  sleep 2
done

$compose run --build --rm --no-deps -T smoke
