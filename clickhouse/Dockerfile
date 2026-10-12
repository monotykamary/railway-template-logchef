FROM clickhouse/clickhouse-server:26.9.17.8@sha256:387ebbcca253026def04dc79e83d2323ac7d97bf309ddd090a8a3c702573e01a

COPY init.sql /docker-entrypoint-initdb.d/001-logchef.sql

EXPOSE 8123 9000
