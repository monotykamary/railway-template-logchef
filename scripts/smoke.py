#!/usr/bin/env python3
"""Strict Logchef API/persistence smoke. Pair with logchef-check-clickhouse.sh.

Boat: pass admin vars through --smoke-env and execute the SQL check inside the
owned clickhouse service using --exec, AFTER this smoke. The boot API query can
precede the SQL seed; later API queries must return exactly that durable marker.
No production HTTPS/secure-cookie setting is changed. Explicit cookie replay is
limited to worker-loopback HTTP; real HTTPS uses normal cookie policy.
"""
import hashlib
import http.cookiejar
import json
import os
from pathlib import Path
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = (os.environ.get('BASE_URL_LOGCHEF') or os.environ['BASE_URL']).rstrip('/')
PHASE = os.environ.get('SMOKE_PHASE', 'boot')
assert PHASE in ('boot', 'upgrade', 'redeploy'), 'unknown smoke phase'
EMAIL = os.environ['LOGCHEF_ADMIN_EMAIL']
PASSWORD = os.environ['LOGCHEF_ADMIN_PASSWORD']
MARKER = os.environ.get('LOGCHEF_SMOKE_MARKER', 'railway-logchef-validation-20261115')
assert MARKER.replace('-', '').isalnum(), 'marker must be alphanumeric/hyphen'
STATE_DIR = Path(os.environ.get('SMOKE_STATE_DIR', str(Path(__file__).resolve().parent / '.state')))
STATE = STATE_DIR / ('logchef-' + hashlib.sha256(BASE.encode()).hexdigest()[:20] + '.json')
COOKIES = http.cookiejar.CookieJar()
OPENER = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(COOKIES))
parsed = urllib.parse.urlsplit(BASE)
assert parsed.scheme == 'https' or (parsed.scheme == 'http' and parsed.hostname in ('127.0.0.1', 'localhost', '::1')), 'HTTP allowed only on worker loopback'


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def request(path, method='GET', payload=None, expected=(200,), authenticated=True):
    headers = {'Accept': 'application/json'}
    if payload is not None:
        headers['Content-Type'] = 'application/json'
    if authenticated and parsed.scheme == 'http':
        # requests/browser cookie jars correctly suppress secure cookies on HTTP.
        # Loopback-only API emulation must opt in explicitly; never weakens server.
        header = '; '.join(c.name + '=' + c.value for c in COOKIES)
        if header:
            headers['Cookie'] = header
    req = urllib.request.Request(BASE + path, method=method, headers=headers,
                                 data=None if payload is None else json.dumps(payload).encode())
    try:
        response = OPENER.open(req, timeout=60)
    except urllib.error.HTTPError as e:
        response = e
    with response:
        status = response.code
        raw = response.read(2 * 1024 * 1024)
    require(status in expected, f'{method} {path} unexpected status {status}')
    try:
        return json.loads(raw)
    except ValueError:
        require(status != 200, f'{path} did not return JSON')
        return None


def data(path, **kwargs):
    result = request(path, **kwargs)
    require(isinstance(result, dict) and 'data' in result, f'{path} missing API data')
    return result['data']


require(data('/api/v1/health', authenticated=False).get('status') == 'ok', 'health payload')
request('/api/v1/me', expected=(401,), authenticated=False)
request('/api/v1/auth/local/login', method='POST', payload={'email': EMAIL, 'password': 'wrong-' + PASSWORD}, expected=(401,), authenticated=False)
login = data('/api/v1/auth/local/login', method='POST', payload={'email': EMAIL, 'password': PASSWORD}, authenticated=False)
uid = login['user']['id']
require(any(c.name == 'session_id' for c in COOKIES), 'login returned no session cookie')
sources = data('/api/v1/admin/sources')
source = next((x for x in sources if x['name'] == 'Railway ClickHouse'), None)
require(source is not None and source.get('is_connected'), 'provisioned ClickHouse source missing/disconnected')

if STATE.exists():
    seed = json.loads(STATE.read_text())
    require(seed['marker'] == MARKER, 'marker does not match persisted test state')
else:
    require(PHASE == 'boot', 'missing persisted test state; refusing to reseed after boot')
    # Upstream team names are limited to 50 bytes; retain a stable short suffix.
    name = 'Railway validation ' + hashlib.sha256(MARKER.encode()).hexdigest()[:12]
    teams = data('/api/v1/admin/teams')
    team = next((x for x in teams if x['name'] == name), None)
    if team is None:
        team = data('/api/v1/admin/teams', method='POST', expected=(201,), payload={'name': name, 'description': 'Durable Railway validation record'})
    tid = team['id']
    members = data(f'/api/v1/teams/{tid}/members')
    if not any(x['user_id'] == uid for x in members):
        request(f'/api/v1/teams/{tid}/members', method='POST', expected=(200, 201), payload={'user_id': uid, 'role': 'admin'})
    attached = data(f'/api/v1/teams/{tid}/sources')
    if not any(x['id'] == source['id'] for x in attached):
        request(f'/api/v1/teams/{tid}/sources', method='POST', expected=(200, 201), payload={'source_id': source['id']})
    seed = {'team_id': tid, 'source_id': source['id'], 'user_id': uid, 'marker': MARKER, 'created_at': time.time()}
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    temporary = STATE.with_suffix('.tmp')
    temporary.write_text(json.dumps(seed))
    temporary.chmod(0o600)
    temporary.replace(STATE)

require(seed['user_id'] == uid, 'bootstrap user identity changed')
require(seed['source_id'] == source['id'], 'provisioned source identity changed')
tid = seed['team_id']
require(any(x['id'] == tid for x in data('/api/v1/admin/teams')), 'seeded team missing')
require(any(x['user_id'] == uid and x['role'] == 'admin' for x in data(f'/api/v1/teams/{tid}/members')), 'seeded membership missing')
require(any(x['id'] == source['id'] for x in data(f'/api/v1/teams/{tid}/sources')), 'seeded team source missing')


def query(expression, expected=(200,)):
    return request(f'/api/v1/teams/{tid}/sources/{source["id"]}/logchefql/query', method='POST', expected=expected,
                   payload={'query': expression,
                            'start_time': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(seed['created_at'] - 300)),
                            'end_time': time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time() + 60)),
                            'timezone': 'UTC', 'limit': 100})

result = query('body~"' + MARKER + '"')
require(isinstance(result, dict) and isinstance(result.get('data'), dict), 'query response shape')
rows = result['data'].get('logs') or result['data'].get('data') or []
if PHASE != 'boot':
    require(any(MARKER == x.get('body') for x in rows), 'durable ClickHouse marker missing through Logchef API')
query('body=', expected=(400,))
print(json.dumps({'ok': True, 'phase': PHASE, 'team_persisted': True, 'source_association_persisted': True,
                  'clickhouse_marker_via_api': PHASE != 'boot', 'boot_sql_seed_required': PHASE == 'boot',
                  'reachability': 'worker-local-http' if parsed.scheme == 'http' else 'public-https'}))
