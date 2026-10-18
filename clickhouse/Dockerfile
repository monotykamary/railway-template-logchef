FROM clickhouse/clickhouse-server:26.9.21.9@sha256:fd4652f708ecfc2239d08c828f5a51dfcc92a1e4a57269b1837c4dbe2dbe33a2

COPY init.sql /docker-entrypoint-initdb.d/001-logchef.sql

EXPOSE 8123 9000
