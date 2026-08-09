FROM node:22.18.0-alpine3.22

WORKDIR /workspace

COPY package.json ./
COPY scripts/api-smoke.mjs scripts/api-smoke.mjs

CMD ["node", "scripts/api-smoke.mjs"]
