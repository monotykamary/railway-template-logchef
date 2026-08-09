import assert from "node:assert/strict";

const baseUrl = process.env.LOGCHEF_URL?.replace(/\/$/, "");
const email = process.env.LOGCHEF_ADMIN_EMAIL;
const password = process.env.LOGCHEF_ADMIN_PASSWORD;
const marker = process.env.LOGCHEF_QUERY_MARKER || "railway-logchef-smoke";
const teamName = process.env.LOGCHEF_SMOKE_TEAM || "Railway validation";
assert.ok(baseUrl, "LOGCHEF_URL is required");
assert.ok(email, "LOGCHEF_ADMIN_EMAIL is required");
assert.ok(password, "LOGCHEF_ADMIN_PASSWORD is required");

async function request(pathname, options = {}, cookie = "") {
  const headers = new Headers(options.headers || {});
  if (options.body && !headers.has("content-type")) headers.set("content-type", "application/json");
  if (cookie) headers.set("cookie", cookie);
  return fetch(`${baseUrl}${pathname}`, { ...options, headers, redirect: "manual" });
}

async function json(response) {
  const text = await response.text();
  let body;
  try { body = JSON.parse(text); } catch { throw new Error(`${response.status} returned non-JSON: ${text.slice(0, 200)}`); }
  return body;
}

const healthResponse = await request("/api/v1/health");
assert.equal(healthResponse.status, 200);
const health = await json(healthResponse);
assert.equal(health.data.status, "ok");

const homepageResponse = await request("/");
assert.equal(homepageResponse.status, 200);
const homepage = await homepageResponse.text();
assert.match(homepage, /<title>[^<]*Logchef/i);
const assetPath = homepage.match(/(?:src|href)="(\/assets\/[^"]+\.(?:js|css))"/)?.[1];
assert.ok(assetPath, "homepage did not reference a built asset");
assert.equal((await request(assetPath)).status, 200);

const metaResponse = await request("/api/v1/meta");
assert.equal(metaResponse.status, 200);
const meta = await json(metaResponse);
assert.equal(meta.data.local_auth_enabled, true);

assert.equal((await request("/api/v1/me")).status, 401);
const invalidLogin = await request("/api/v1/auth/local/login", {
  method: "POST",
  body: JSON.stringify({ email, password: "not-the-generated-password" })
});
assert.equal(invalidLogin.status, 401);

const loginResponse = await request("/api/v1/auth/local/login", {
  method: "POST",
  body: JSON.stringify({ email, password })
});
assert.equal(loginResponse.status, 200);
const login = await json(loginResponse);
const user = login.data.user;
assert.equal(user.email, email.toLowerCase());
const cookie = loginResponse.headers.get("set-cookie")?.split(";", 1)[0];
assert.ok(cookie?.startsWith("session_id="), "login did not set a session cookie");

const meResponse = await request("/api/v1/me", {}, cookie);
assert.equal(meResponse.status, 200);

const sourcesResponse = await request("/api/v1/admin/sources", {}, cookie);
assert.equal(sourcesResponse.status, 200);
const sources = (await json(sourcesResponse)).data;
const source = sources.find((candidate) => candidate.name === "Railway ClickHouse");
assert.ok(source, "provisioned ClickHouse source was not found");
assert.equal(source.source_type, "clickhouse");
assert.equal(source.is_connected, true);

const teamsResponse = await request("/api/v1/admin/teams", {}, cookie);
assert.equal(teamsResponse.status, 200);
let team = (await json(teamsResponse)).data.find((candidate) => candidate.name === teamName);
let createdTeam = false;
if (!team) {
  const createResponse = await request("/api/v1/admin/teams", {
    method: "POST",
    body: JSON.stringify({ name: teamName, description: `Persistence marker: ${marker}` })
  }, cookie);
  assert.equal(createResponse.status, 201);
  team = (await json(createResponse)).data;
  createdTeam = true;
}

const membersResponse = await request(`/api/v1/teams/${team.id}/members`, {}, cookie);
assert.equal(membersResponse.status, 200);
const members = (await json(membersResponse)).data;
if (!members.some((member) => member.user_id === user.id)) {
  const addMember = await request(`/api/v1/teams/${team.id}/members`, {
    method: "POST",
    body: JSON.stringify({ user_id: user.id, role: "admin" })
  }, cookie);
  assert.ok([200, 201].includes(addMember.status), `adding team member returned ${addMember.status}`);
}

const teamSourcesResponse = await request(`/api/v1/teams/${team.id}/sources`, {}, cookie);
assert.equal(teamSourcesResponse.status, 200);
const teamSources = (await json(teamSourcesResponse)).data;
if (!teamSources.some((candidate) => candidate.id === source.id)) {
  const addSource = await request(`/api/v1/teams/${team.id}/sources`, {
    method: "POST",
    body: JSON.stringify({ source_id: source.id })
  }, cookie);
  assert.ok([200, 201].includes(addSource.status), `adding team source returned ${addSource.status}`);
}

const now = Date.now();
const queryTime = (value) => new Date(value).toISOString().replace("T", " ").slice(0, 19);
const queryResponse = await request(`/api/v1/teams/${team.id}/sources/${source.id}/logchefql/query`, {
  method: "POST",
  body: JSON.stringify({
    query: `body~"${marker}"`,
    start_time: queryTime(now - 3_600_000),
    end_time: queryTime(now + 60_000),
    timezone: "UTC",
    limit: 100
  })
}, cookie);
const query = await json(queryResponse);
assert.equal(queryResponse.status, 200, `query failed: ${JSON.stringify(query)}`);
const rows = query.data.logs || query.data.data || [];
assert.ok(rows.some((row) => String(row.body).includes(marker)), "LogChef query did not return the seeded marker");

const badQueryResponse = await request(`/api/v1/teams/${team.id}/sources/${source.id}/logchefql/query`, {
  method: "POST",
  body: JSON.stringify({
    query: "body=",
    start_time: queryTime(now - 3_600_000),
    end_time: queryTime(now + 60_000),
    timezone: "UTC",
    limit: 10
  })
}, cookie);
assert.equal(badQueryResponse.status, 400);

console.log(JSON.stringify({
  health: health.data.status,
  buildInfo: health.data.buildInfo,
  sourceId: source.id,
  sourceConnected: source.is_connected,
  teamId: team.id,
  teamCreated: createdTeam,
  queryRows: rows.length,
  marker
}));
