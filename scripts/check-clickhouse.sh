#!/bin/sh
# Run inside exact owned ClickHouse container via harness --exec.
# No data is recreated after boot. Fixed marker must match logchef-smoke.py.
set -eu
marker=railway-logchef-validation-20261115
query() {
  clickhouse-client --user "$CLICKHOUSE_USER" --password "$CLICKHOUSE_PASSWORD" --query "$1"
}
count=$(query "SELECT count() FROM default.logs WHERE body = '$marker'")
if [ "${SMOKE_PHASE:?}" = boot ] && [ "$count" = 0 ]; then
  query "INSERT INTO default.logs (timestamp, severity_text, severity_number, service_name, namespace, body, log_attributes) VALUES (now64(3), 'INFO', 9, 'railway-validation', 'validation', '$marker', map('validation', 'durable'))"
fi
count=$(query "SELECT count() FROM default.logs WHERE body = '$marker'")
[ "$count" = 1 ] || { echo 'durable marker missing or duplicated' >&2; exit 1; }
echo '{"ok":true,"durable_marker_sql":true}'
