FROM ghcr.io/mr-karan/logchef:v2.0.2@sha256:725350f03ec55777713656a20b5d37cb57484d7ab18e3134af7352de64c0bccf

USER root

RUN apk --no-cache add curl

COPY --chown=logchef:logchef config.toml /etc/logchef/railway.toml
COPY --chown=logchef:logchef provisioning.toml /etc/logchef/provisioning.toml
COPY --chown=logchef:logchef start-logchef.sh /usr/local/bin/start-logchef
RUN chmod 0555 /usr/local/bin/start-logchef

USER logchef
WORKDIR /data

EXPOSE 8125

ENTRYPOINT ["/usr/local/bin/start-logchef"]
