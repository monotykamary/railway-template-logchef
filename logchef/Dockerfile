FROM ghcr.io/mr-karan/logchef:v2.5.0@sha256:98b95c75503e60ae70da8bdca421b6544db7009b96f49ea4d591eb99a794d9ce

USER root

RUN apk --no-cache add curl su-exec

COPY --chown=logchef:logchef config.toml /etc/logchef/railway.toml
COPY --chown=logchef:logchef provisioning.toml /etc/logchef/provisioning.toml
COPY --chown=logchef:logchef start-logchef.sh /usr/local/bin/start-logchef
RUN chmod 0555 /usr/local/bin/start-logchef

WORKDIR /data

EXPOSE 8125

ENTRYPOINT ["/usr/local/bin/start-logchef"]
