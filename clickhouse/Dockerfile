FROM clickhouse/clickhouse-server:26.8.7@sha256:583e76e9d9316e221ab649f964575f250797ae2e45e61295103e4328642457e0

COPY init.sql /docker-entrypoint-initdb.d/001-logchef.sql

EXPOSE 8123 9000
