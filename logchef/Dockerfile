FROM ghcr.io/mr-karan/logchef:v2.4.0@sha256:b509000c91f7efc41a9430399310da2849a43ab60910391cc1616cbee0c1ac22

USER root

RUN apk --no-cache add curl su-exec

COPY --chown=logchef:logchef config.toml /etc/logchef/railway.toml
COPY --chown=logchef:logchef provisioning.toml /etc/logchef/provisioning.toml
COPY --chown=logchef:logchef start-logchef.sh /usr/local/bin/start-logchef
RUN chmod 0555 /usr/local/bin/start-logchef

WORKDIR /data

EXPOSE 8125

ENTRYPOINT ["/usr/local/bin/start-logchef"]
