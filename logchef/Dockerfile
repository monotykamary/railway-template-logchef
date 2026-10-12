FROM ghcr.io/mr-karan/logchef:v2.3.2@sha256:a91a13d1d232f6890808dceeafa7e21a361f82591d316ecacc67882584d5808d

USER root

RUN apk --no-cache add curl su-exec

COPY --chown=logchef:logchef config.toml /etc/logchef/railway.toml
COPY --chown=logchef:logchef provisioning.toml /etc/logchef/provisioning.toml
COPY --chown=logchef:logchef start-logchef.sh /usr/local/bin/start-logchef
RUN chmod 0555 /usr/local/bin/start-logchef

WORKDIR /data

EXPOSE 8125

ENTRYPOINT ["/usr/local/bin/start-logchef"]
