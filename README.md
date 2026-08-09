# Logchef on Railway

A production-oriented Railway template for [Logchef](https://logchef.app/), the open-source log workspace for ClickHouse and VictoriaLogs. It deploys Logchef with local authentication and a private, persistent ClickHouse log store.

> The Deploy on Railway button is added only after the published marketplace route is verified.

## What this deploys

| Service | Version | Exposure | Persistence |
| --- | --- | --- | --- |
| Logchef | Logchef v2.0.2 | Public HTTPS on port `8125` | SQLite metadata at `/data` |
| ClickHouse | ClickHouse 26.3.17.110 LTS | Private ports `8123` and `9000` | Data at `/var/lib/clickhouse` |

Both images are pinned by release and registry digest. The template provisions a `Railway ClickHouse` datasource and a 30-day OpenTelemetry-style `default.logs` table. ClickHouse is intentionally private.

## Post-deploy setup

1. Open the generated Logchef domain.
2. Sign in with `LOGCHEF_AUTH__LOCAL__ADMIN_EMAIL` and `LOGCHEF_AUTH__LOCAL__ADMIN_PASSWORD` from the Logchef service variables.
3. Under **Access → Teams**, create a team, add the administrator, and assign the preconfigured `Railway ClickHouse` source.
4. Send logs from a collector in the same Railway project to `clickhouse.railway.internal` using the generated ClickHouse credentials.
5. Run a query from **Explore**. The initialized schema uses `timestamp`, `severity_text`, `severity_number`, `service_name`, `namespace`, `body`, and `log_attributes`.

Logchef is a query and control plane, not a log shipper. Vector, OpenTelemetry Collector, Fluent Bit, or another collector must ingest logs into ClickHouse.

## Variables

### Logchef

| Variable | Purpose |
| --- | --- |
| `LOGCHEF_AUTH__LOCAL__ADMIN_EMAIL` | Bootstrap administrator email. |
| `LOGCHEF_AUTH__LOCAL__ADMIN_PASSWORD` | Generated bootstrap administrator password. |
| `LOGCHEF_AUTH__API_TOKEN_SECRET` | Generated key used to hash Logchef API tokens. |
| `LOGCHEF_CLICKHOUSE_PASSWORD` | Reference to the generated ClickHouse password; do not replace it with an unrelated value. |
| `LOGCHEF_SERVER__FRONTEND_URL` | Public HTTPS origin used for links and browser configuration. |

### ClickHouse

| Variable | Purpose |
| --- | --- |
| `CLICKHOUSE_USER` | Private database user, fixed to `logchef`. |
| `CLICKHOUSE_PASSWORD` | Generated database password shared through a service reference. |
| `CLICKHOUSE_DB` | Initialized database, fixed to `default`. |

## Persistence and backups

The Logchef and ClickHouse volumes are independent; Railway does not share a volume between services. The marketplace template enables daily backups for both volumes. Logchef applies SQLite migrations automatically at startup, and ClickHouse preserves the initialized table across redeployments.

## Important limitations

- The template deploys one Logchef replica because SQLite is the default metadata store. Use PostgreSQL and review Logchef's alert-manager caveat before attempting multiple replicas.
- ClickHouse is single-node and not highly available. Size memory and storage for the workload; ClickHouse will dominate resource use.
- No ingestion endpoint is exposed publicly. Prefer a collector in the same Railway project. If public ingestion is necessary, secure it explicitly rather than exposing an unauthenticated ClickHouse service.
- Railway has no public UDP support. UDP-only syslog inputs require a separate gateway or a TCP/HTTP collector path.
- The datasource depends on the service name `clickhouse`; renaming that service breaks `clickhouse.railway.internal` until the provisioning file is updated.
- The initialized table retains logs for 30 days. Change its ClickHouse TTL deliberately if a different retention period is required.
- OIDC, SMTP delivery, and AI query generation are optional post-deploy integrations and are not preconfigured.

## Local validation

Docker is required:

```bash
npm test
npm run smoke
```

The smoke test builds both pinned wrappers, checks health and static assets, verifies safe authentication failures, signs in, provisions team access, inserts and queries a real log through Logchef, restarts Logchef, and confirms metadata persistence.

## Updating

1. Resolve stable upstream releases and immutable image digests.
2. Update both `FROM` lines and the version documentation together.
3. Re-run static, local integration, Railway live, persistence, redeploy, and delayed log-soak tests.
4. Publish only after the rendered Railway route shows the expected source, versions, and service topology.

## Upstream and license

- [Logchef source](https://github.com/mr-karan/logchef)
- [Logchef documentation](https://logchef.app/)
- [Logchef v2.0.2](https://github.com/mr-karan/logchef/releases/tag/v2.0.2)
- [ClickHouse source](https://github.com/ClickHouse/ClickHouse)
- [ClickHouse 26.3.17.110 LTS](https://github.com/ClickHouse/ClickHouse/releases/tag/v26.3.17.110-lts)

This repository preserves Logchef's GNU AGPLv3 license and attribution. See [`LICENSE`](LICENSE) and [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
