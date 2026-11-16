# Deploy and Host Logchef on Railway

Logchef is an open-source log exploration, dashboarding, alerting, and access-control workspace for ClickHouse and VictoriaLogs. This template deploys a pinned Logchef release with built-in email/password authentication and a private ClickHouse service, giving a new installation durable metadata, durable log storage, and a preconfigured datasource without requiring an external identity provider.

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

- Logchef v2.7.0
- ClickHouse 26.10.2.103 (the existing template pin is retained)
- One Railway volume for Logchef metadata
- One Railway volume for ClickHouse data
- A log collector such as Vector, OpenTelemetry Collector, or Fluent Bit

### Deployment Dependencies

- [Logchef documentation](https://logchef.app/)
- [Logchef source and AGPLv3 license](https://github.com/mr-karan/logchef)
- [Logchef v2.7.0 release](https://github.com/mr-karan/logchef/releases/tag/v2.7.0)
- [ClickHouse documentation](https://clickhouse.com/docs)
- [Template source repository](https://github.com/monotykamary/railway-template-logchef)

### Implementation Details

The Logchef wrapper replaces the release image's development-oriented configuration with a minimal production configuration, enables local authentication, stores SQLite under `/data`, waits for authenticated ClickHouse readiness, and declaratively provisions the private datasource. The ClickHouse wrapper retains the existing `26.10.2.103` image and initializes a MergeTree log table with a 30-day TTL and common OpenTelemetry-style fields. Both base images are pinned by tag and digest.

Railway exposes only Logchef on port `8125`. ClickHouse remains private on HTTP port `8123` and native port `9000`. Generated service references keep the ClickHouse password synchronized without serializing a real secret. Both volumes receive daily backups, and both services use explicit health checks and restart policies. Budget at least 2 GB for ClickHouse before adding a production log workload, and measure memory requirements under your actual ingestion and query load.

Logchef does not ingest logs itself. Deploy a collector in the same project and target `clickhouse.railway.internal`, or connect Logchef to another ClickHouse or VictoriaLogs source after deployment. Public UDP is unavailable on Railway, so use TCP or HTTP ingestion for cloud collectors.

### Upgrading to v2.7

Back up the SQLite metadata database and keep both existing volumes and authentication secrets. Logchef v2.7 applies migrations 000039–000041, adding dashboard revisions and classifying collection links. Save open dashboard edits and reload browser tabs after the update. API clients must send the current dashboard `revision`: omitted revisions return 428 and stale revisions return 409. Review **Library → All queries → Links that lost delegation** after migration; this maintenance validation does not certify delegated-link conversion.

The ClickHouse version and data schema are not changed by this update. Local authentication, original team/source/dashboard state, database query results and revision-conflict rejection are the core validation scope. Optional OIDC, SMTP/webhook delivery, external ingestion collectors and AI providers need separate operator configuration and testing.

### Why Deploy Logchef on Railway?

Railway provides reproducible source builds, private service discovery, public HTTPS, generated secrets, health checks, persistent volumes, backups, deployment logs, and controlled redeployments. This template turns those primitives into a compact two-service logging workspace while keeping ClickHouse off the public internet and preserving deliberate, pinned upgrades.
