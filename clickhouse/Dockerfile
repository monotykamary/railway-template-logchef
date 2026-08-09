FROM clickhouse/clickhouse-server:26.3.17.110@sha256:2ef11bbe2e44ab7022f37ff3019b3f2125ed09e919ea6194660be6130b7ca4b7

COPY init.sql /docker-entrypoint-initdb.d/001-logchef.sql

EXPOSE 8123 9000
