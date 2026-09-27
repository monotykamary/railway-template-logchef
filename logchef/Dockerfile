FROM ghcr.io/mr-karan/logchef:v2.1.0@sha256:27f631a7a783c7f357efe954d4c9e023f87de10fd6bae51d781235e6c7ec9896

USER root

RUN apk --no-cache add curl su-exec

COPY --chown=logchef:logchef config.toml /etc/logchef/railway.toml
COPY --chown=logchef:logchef provisioning.toml /etc/logchef/provisioning.toml
COPY --chown=logchef:logchef start-logchef.sh /usr/local/bin/start-logchef
RUN chmod 0555 /usr/local/bin/start-logchef

WORKDIR /data

EXPOSE 8125

ENTRYPOINT ["/usr/local/bin/start-logchef"]
