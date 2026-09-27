# Deploy and Host Logchef on Railway

Logchef is an open-source log exploration, dashboarding, alerting, and access-control workspace for ClickHouse and VictoriaLogs. This template deploys a pinned Logchef release with built-in email/password authentication and a private ClickHouse LTS service, giving a new installation durable metadata, durable log storage, and a preconfigured datasource without requiring an external identity provider.

## About Hosting Logchef

Hosting Logchef provides a shared query and visualization layer over structured logs. The public Logchef service serves the browser application and API over Railway HTTPS. Its SQLite control-plane database stores users, sessions, teams, sources, dashboards, alerts, and saved queries on a dedicated volume. A separate ClickHouse service stores log events on its own volume and is reachable only through Railway private networking.

The first administrator is created idempotently from `LOGCHEF_AUTH__LOCAL__ADMIN_EMAIL` and the generated `LOGCHEF_AUTH__LOCAL__ADMIN_PASSWORD`. The template also generates the API-token hashing secret and ClickHouse password. After signing in, create a team, add the administrator, and assign the preconfigured `Railway ClickHouse` source.

## Common Use Cases

- Search structured application and infrastructure logs with LogchefQL or SQL
- Build operational dashboards over ClickHouse log data
- Save and share incident queries across teams
- Configure scheduled email or webhook alerts
- Apply team-based access control to log sources
- Add AI-assisted query generation with an optional external model provider

## Dependencies for Logchef Hosting

- Logchef v2.1.0
- ClickHouse 26.3.17.110 LTS
- One Railway volume for Logchef metadata
- One Railway volume for ClickHouse data
- A log collector such as Vector, OpenTelemetry Collector, or Fluent Bit

### Deployment Dependencies

- [Logchef documentation](https://logchef.app/)
- [Logchef source and AGPLv3 license](https://github.com/mr-karan/logchef)
- [Logchef v2.1.0 release](https://github.com/mr-karan/logchef/releases/tag/v2.1.0)
- [ClickHouse documentation](https://clickhouse.com/docs)
- [Template source repository](https://github.com/monotykamary/railway-template-logchef)

### Implementation Details

The Logchef wrapper replaces the release image's development-oriented configuration with a minimal production configuration, enables local authentication, stores SQLite under `/data`, waits for authenticated ClickHouse readiness, and declaratively provisions the private datasource. The ClickHouse wrapper uses the current `26.3` LTS image and initializes a MergeTree log table with a 30-day TTL and common OpenTelemetry-style fields. Both base images are pinned by tag and digest.

Railway exposes only Logchef on port `8125`. ClickHouse remains private on HTTP port `8123` and native port `9000`. Generated service references keep the ClickHouse password synchronized without serializing a real secret. Both volumes receive daily backups, and both services use explicit health checks and restart policies. Live validation observed approximately 1.7 GB of idle ClickHouse memory and 20 MB for Logchef; allow at least 2 GB before adding a production log workload.

Logchef does not ingest logs itself. Deploy a collector in the same project and target `clickhouse.railway.internal`, or connect Logchef to another ClickHouse or VictoriaLogs source after deployment. Public UDP is unavailable on Railway, so use TCP or HTTP ingestion for cloud collectors.

### Why Deploy Logchef on Railway?

Railway provides reproducible source builds, private service discovery, public HTTPS, generated secrets, health checks, persistent volumes, backups, deployment logs, and controlled redeployments. This template turns those primitives into a compact two-service logging workspace while keeping ClickHouse off the public internet and preserving deliberate, pinned upgrades.
