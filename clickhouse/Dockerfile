FROM clickhouse/clickhouse-server:26.9.4.3@sha256:317c280a2334651a54b3e07201c2de4c09588b8e66e64f719cee26d0f434ca81

COPY init.sql /docker-entrypoint-initdb.d/001-logchef.sql

EXPOSE 8123 9000
