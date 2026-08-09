#!/bin/sh
set -eu

if [ -z "${LOGCHEF_CLICKHOUSE_PASSWORD:-}" ]; then
  echo "LOGCHEF_CLICKHOUSE_PASSWORD must not be empty" >&2
  exit 1
fi

health_url="${LOGCHEF_CLICKHOUSE_HEALTH_URL:-http://clickhouse.railway.internal:8123/ping}"
attempt=1
max_attempts="${LOGCHEF_CLICKHOUSE_WAIT_ATTEMPTS:-150}"

case "$max_attempts" in
  ''|*[!0-9]*)
    echo "LOGCHEF_CLICKHOUSE_WAIT_ATTEMPTS must be a positive integer" >&2
    exit 1
    ;;
esac
if [ "$max_attempts" -lt 1 ]; then
  echo "LOGCHEF_CLICKHOUSE_WAIT_ATTEMPTS must be a positive integer" >&2
  exit 1
fi

while [ "$attempt" -le "$max_attempts" ]; do
  response="$(wget -q -O - \
    --header="X-ClickHouse-User: logchef" \
    --header="X-ClickHouse-Key: ${LOGCHEF_CLICKHOUSE_PASSWORD}" \
    "$health_url" 2>/dev/null || true)"
  if [ "$response" = "Ok." ]; then
    exec /usr/local/bin/logchef -config /etc/logchef/railway.toml
  fi
  if [ "$attempt" -eq 1 ] || [ $((attempt % 15)) -eq 0 ]; then
    echo "Waiting for ClickHouse readiness (attempt ${attempt}/${max_attempts})"
  fi
  attempt=$((attempt + 1))
  sleep 2
done

echo "ClickHouse did not become ready before the startup deadline" >&2
exit 1
