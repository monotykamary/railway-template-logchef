#!/usr/bin/env python3
"""Remote-only regression tests for strict smoke state handling, NOT product proof."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading

model = {'team': False, 'member': False, 'source': False, 'marker': False}
marker = 'railway-logchef-validation-20261115'
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass
    def respond(self, status, data, cookie=False):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        if cookie:
            self.send_header('Set-Cookie', 'session_id=fixture-only; Secure; HttpOnly; Path=/')
        self.end_headers()
        self.wfile.write(json.dumps({'data': data}).encode())
    def do_GET(self):
        if self.path == '/api/v1/health':
            return self.respond(200, {'status': 'ok'})
        if self.path == '/api/v1/me':
            return self.respond(401, {})
        if 'session_id=fixture-only' not in self.headers.get('Cookie', ''):
            return self.respond(401, {})
        if self.path == '/api/v1/admin/sources':
            return self.respond(200, [{'id': 1, 'name': 'Railway ClickHouse', 'is_connected': True}])
        if self.path == '/api/v1/admin/teams':
            return self.respond(200, [{'id': 3, 'name': model['team_name']}] if model['team'] else [])
        if self.path.endswith('/members'):
            return self.respond(200, [{'user_id': 2, 'role': 'admin'}] if model['member'] else [])
        if self.path.endswith('/sources'):
            return self.respond(200, [{'id': 1}] if model['source'] else [])
        return self.respond(404, {})
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get('Content-Length', '0'))))
        if self.path == '/api/v1/auth/local/login':
            if body['password'] != 'fixture-password':
                return self.respond(401, {})
            return self.respond(200, {'user': {'id': 2}}, cookie=True)
        if 'session_id=fixture-only' not in self.headers.get('Cookie', ''):
            return self.respond(401, {})
        if self.path == '/api/v1/admin/teams':
            if not 2 <= len(body.get('name', '').encode()) <= 50:
                return self.respond(400, {})
            model['team_name'] = body['name']
            model['team'] = True
            return self.respond(201, {'id': 3})
        if self.path.endswith('/members'):
            model['member'] = True
            return self.respond(201, None)
        if self.path.endswith('/sources'):
            model['source'] = True
            return self.respond(201, None)
        if self.path.endswith('/logchefql/query'):
            if body['query'] == 'body=':
                return self.respond(400, {})
            return self.respond(200, {'logs': [{'body': marker}] if model['marker'] else []})
        return self.respond(404, {})

server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
try:
    with tempfile.TemporaryDirectory() as td:
        env = {**os.environ, 'BASE_URL': f'http://127.0.0.1:{server.server_port}', 'LOGCHEF_ADMIN_EMAIL': 'fixture@example.test',
               'LOGCHEF_ADMIN_PASSWORD': 'fixture-password', 'SMOKE_STATE_DIR': td}
        def run(phase, success):
            result = subprocess.run([sys.executable, sys.argv[1]], env={**env, 'SMOKE_PHASE': phase}, capture_output=True, text=True, timeout=30)
            assert (result.returncode == 0) == success, f'{phase}: expected success={success}, rc={result.returncode}, out={result.stdout}, err={result.stderr}'
        run('boot', True)
        run('boot', True)  # existing state verifies instead of duplicating
        run('upgrade', False)  # marker was not SQL-seeded yet
        model['marker'] = True
        run('upgrade', True)
        run('redeploy', True)
        model['team'] = False
        run('upgrade', False)
        model['team'] = True
        model['member'] = False
        run('upgrade', False)
        model['member'] = True
        for path in Path(td).iterdir():
            path.unlink()
        run('upgrade', False)
    print(json.dumps({'ok': True, 'synthetic_smoke_regressions': 8, 'product_evidence': False}))
finally:
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)
