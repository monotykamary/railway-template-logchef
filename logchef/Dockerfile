FROM ghcr.io/mr-karan/logchef:v2.2.0@sha256:b18be3219cd8ca4fa1cef0189ea99ea11492db8a0599326c42efae44e2ae4bd0

USER root

RUN apk --no-cache add curl su-exec

COPY --chown=logchef:logchef config.toml /etc/logchef/railway.toml
COPY --chown=logchef:logchef provisioning.toml /etc/logchef/provisioning.toml
COPY --chown=logchef:logchef start-logchef.sh /usr/local/bin/start-logchef
RUN chmod 0555 /usr/local/bin/start-logchef

WORKDIR /data

EXPOSE 8125

ENTRYPOINT ["/usr/local/bin/start-logchef"]
