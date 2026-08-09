import assert from "node:assert/strict";
import { readFile, readdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const read = (name) => readFile(path.join(root, name), "utf8");

const files = [];
async function walk(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    if (entry.name === ".git" || entry.name === "node_modules") continue;
    const full = path.join(directory, entry.name);
    if (entry.isDirectory()) await walk(full);
    else files.push(full);
  }
}
await walk(root);

const logchefDockerfile = await read("logchef/Dockerfile");
const clickhouseDockerfile = await read("clickhouse/Dockerfile");
assert.match(logchefDockerfile, /logchef:v2\.0\.2@sha256:[a-f0-9]{64}/);
assert.match(clickhouseDockerfile, /clickhouse-server:26\.3\.17\.110@sha256:[a-f0-9]{64}/);
assert.doesNotMatch(`${logchefDockerfile}\n${clickhouseDockerfile}`, /:latest(?:@|\s|$)/m);

for (const service of ["logchef", "clickhouse"]) {
  const config = JSON.parse(await read(`${service}/railway.json`));
  assert.equal(config.build.builder, "DOCKERFILE");
  assert.equal(config.deploy.restartPolicyType, "ON_FAILURE");
  assert.ok(config.deploy.healthcheckPath.startsWith("/"));
  assert.ok(config.deploy.healthcheckTimeout >= 300);
}

const provisioning = await read("logchef/provisioning.toml");
assert.match(provisioning, /host = "clickhouse\.railway\.internal:9000"/);
assert.match(provisioning, /secret_ref = "LOGCHEF_CLICKHOUSE_PASSWORD"/);
assert.doesNotMatch(provisioning, /password\s*=/);

const compose = await read("docker-compose.yml");
assert.match(compose, /clickhouse-data:\/var\/lib\/clickhouse/);
assert.match(compose, /logchef-data:\/data/);

const allText = (await Promise.all(files
  .filter((file) => !file.endsWith(".png") && !file.endsWith("LICENSE"))
  .map((file) => readFile(file, "utf8")))).join("\n");
assert.doesNotMatch(allText, /\.up\.railway\.app/);
assert.doesNotMatch(allText, /-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/);

const readme = await read("README.md");
for (const marker of ["Logchef v2.0.2", "ClickHouse 26.3.17.110 LTS", "Important limitations", "Post-deploy setup"]) {
  assert.ok(readme.includes(marker), `README is missing ${marker}`);
}

console.log(`static checks passed (${files.length} files scanned)`);
