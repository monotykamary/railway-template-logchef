FROM clickhouse/clickhouse-server:26.10.2.103@sha256:b2bfa4d8399ee9973868cc5c1754cb506a6f4b86fbddc41010cc090beb55c85e

COPY init.sql /docker-entrypoint-initdb.d/001-logchef.sql

EXPOSE 8123 9000
