"""Serve Godot at the origin root and proxy reviewed native Companion routes."""
import argparse
import gzip
import json
import sys
import time
import mimetypes
import os
import re
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlsplit, unquote
from urllib.request import HTTPRedirectHandler, Request, build_opener, ProxyHandler

PROJECT = Path(__file__).resolve().parents[1]
READS = re.compile(r'^/(health|characters(?:/[a-zA-Z0-9_-]+(?:/action-manifest|/notes)?)?|workspace(?:/(?:ledger|maps))?|sessions(?:/[0-9]+)?|scenes(?:/[0-9]+)?|combat/effects|rolls|roll-requests|gm/actions/describe|gm/prep/(?:drafts|context|sessions)|gm/workspace/monster-catalog|npcs|gm/workspace/items|gm/compendium/(?:items|spells)|combat/attacks/pending|gm/combat/tokens/[^/]{1,200}/action-proposals|workspace/tokens/[^/]{1,200}/commerce|workspace/terrain/[a-z0-9_-]{1,40}|media/(?:zz_media|companion-assets)/[^?#]+)$')
WRITES = {'/workspace/heartbeat', '/workspace/messages', '/rolls', '/workspace/loot/collect'}
SESSION_STATUS = re.compile(r'^/gm/(?:sessions/[0-9]+/status|scenes/[0-9]+/selection-on-table)$')
ATTACKS = re.compile(r'^/(?:characters/[a-zA-Z0-9_-]+/(?:attacks/resolve|techniques/[a-zA-Z0-9_-]{1,80})|gm/combat/tokens/[^/]{1,200}/attacks/resolve|combat/attacks/[^/]{1,200}/confirm)$')
MOVES = re.compile(r'^/workspace/maps/[^/]{1,200}/(?:move|grid)$')
COMMERCE = re.compile(r'^/commerce/(?:[^/]{1,200}/quotes|quotes/[^/]{1,200}/confirm)$')
PATCHES = {'/gm/workspace/maps/active', '/gm/workspace/table-mode'}
DISPOSITION = re.compile(r'^/gm/workspace/tokens/[^/]{1,200}/disposition$')
# GM pin edits during play: reveal/hide and HP only; removal by DELETE.
TOKEN_EDIT = re.compile(r'^/gm/workspace/tokens/[^/]{1,200}$')
POSITION = re.compile(r'^/gm/workspace/tokens/[^/]{1,200}/position$')
TOKEN_EDIT_KEYS = {'visible_to_players', 'current_hp', 'maximum_hp', 'name', 'conditions', 'sheet'}
# GM library: scene cast/elements and item grants (the backend still requires the Master token).
NOTES = re.compile(r'^/characters/[a-zA-Z0-9_-]+/notes$')
DEFINITION = re.compile(r'^/gm/characters/[a-zA-Z0-9_-]+/definition$')
CHAR_ACTIONS = re.compile(r'^/characters/(?:[a-zA-Z0-9_-]+/actions|vezemir/vines)$')
ROLLS = re.compile(r'^/(?:characters/[a-zA-Z0-9_-]+/rolls|gm/roll-requests|roll-requests/[0-9]+/complete|gm/rolls/[0-9]+/void)$')
LIBRARY = re.compile(r'^/gm/(?:scenes/[0-9]+/(?:participants|elements)|workspace/items/grant|workspace/items|prep/generate|prep/drafts/[0-9]+/(?:discard|applied|apply-map)|prep/sessions/[0-9]+/plan/generate|sessions)$')
# Preparar sessão: the outline and the session record are long texts edited by the GM.
PREP_PUT = re.compile(r'^/gm/prep/(?:context|sessions/[0-9]+/(?:plan|record))$')
MONSTER_SHEET_LIMIT = 64000
# Map editor: the whole edited terrain (tiles, heights, props) of one map.
TERRAIN = re.compile(r'^/gm/workspace/terrain/[a-z0-9_-]{1,40}$')
TERRAIN_LIMIT = 600000


COMPRESSIBLE = {'.wasm', '.js', '.pck', '.html', '.json', '.webmanifest'}
_GZIP_CACHE = {}
_GZIP_LOCK = threading.Lock()


def gzipped(file_path):
    """Compressed bytes cached per (path, mtime, size); the Web export is ~4x smaller."""
    stat = os.stat(file_path)
    key = (str(file_path), stat.st_mtime_ns, stat.st_size)
    with _GZIP_LOCK:
        cached = _GZIP_CACHE.get(str(file_path))
        if cached and cached[0] == key:
            return cached[1]
        data = gzip.compress(Path(file_path).read_bytes(), compresslevel=6, mtime=0)
        _GZIP_CACHE[str(file_path)] = (key, data)
        return data


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        return None


class Preview(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, '.wasm': 'application/wasm', '.webmanifest': 'application/manifest+json'}

    def log_message(self, _format, *_args):
        pass  # No credentials, bodies or access URLs in local logs.

    def end_headers(self):
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('X-Content-Type-Options', 'nosniff')
        super().end_headers()

    @staticmethod
    def _put_body_ok(path, payload):
        if TERRAIN.fullmatch(path):
            return set(payload) == {'tiles', 'heights', 'props', 'expected_version'}
        if path.endswith('/plan'):
            return set(payload) == {'outline', 'version'}
        if path.endswith('/record'):
            return 'version' in payload and set(payload) <= {'version', 'title', 'status', 'public_summary', 'gm_summary', 'public_chronicle'}
        return set(payload) == {'content', 'version'}

    def _error(self, status, message):
        # Diagnostics only: method, path (no query string, no headers/credentials), status and reason.
        sys.stderr.write('%s %s %s %d %s\n' % (time.strftime('%H:%M:%S'), self.command, urlsplit(self.path).path, status, message))
        sys.stderr.flush()
        data = json.dumps({'detail': message}).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _proxy(self):
        parsed = urlsplit(self.path)
        query = parse_qs(parsed.query)
        if set(query) - {'limit', 'read_only', 'map_id', 'preview_size', 'ref', 'q', 'target_token_ids', 'character_id', 'category', 'session_id', 'since'}:
            self._error(400, 'Parâmetro indisponível')
            return
        if parsed.path.startswith('/media/'):
            decoded = unquote(unquote(parsed.path))
            if '..' in decoded or '\\' in decoded or ':' in decoded or query.get('preview_size') not in (['128'], ['768']):
                self._error(400, 'Mídia indisponível')
                return
        if self.command == 'GET' and not READS.fullmatch(parsed.path):
            self._error(404, 'Rota indisponível nesta prévia')
            return
        if self.command == 'DELETE' and not TOKEN_EDIT.fullmatch(parsed.path) and not TERRAIN.fullmatch(parsed.path):
            self._error(405, 'Comando indisponível nesta prévia')
            return
        if self.command == 'PUT' and not NOTES.fullmatch(parsed.path) and not PREP_PUT.fullmatch(parsed.path) and not TERRAIN.fullmatch(parsed.path):
            self._error(405, 'Comando indisponível nesta prévia')
            return
        if self.command == 'PATCH' and parsed.path not in PATCHES and not DISPOSITION.fullmatch(parsed.path) and not TOKEN_EDIT.fullmatch(parsed.path) and not POSITION.fullmatch(parsed.path) and not DEFINITION.fullmatch(parsed.path):
            self._error(405, 'Comando indisponível nesta prévia')
            return
        if self.command == 'POST' and parsed.path not in WRITES | {'/gm/combat/effects', '/combat/next-turn', '/gm/workspace/tokens'} and not MOVES.fullmatch(parsed.path) and not SESSION_STATUS.fullmatch(parsed.path) and not ATTACKS.fullmatch(parsed.path) and not COMMERCE.fullmatch(parsed.path) and not LIBRARY.fullmatch(parsed.path) and not ROLLS.fullmatch(parsed.path) and not CHAR_ACTIONS.fullmatch(parsed.path):
            self._error(405, 'Comando indisponível nesta prévia')
            return
        token = self.headers.get('X-Omnisvera-Token', '')
        if not token or len(token) > 4096:
            self._error(401, 'Informe seu acesso')
            return
        if parsed.path.startswith('/characters'):
            query['read_only'] = ['true']
        route = parsed.path + ('?' + urlencode(query, doseq=True) if query else '')
        headers = {'X-Omnisvera-Token': token, 'Accept': 'application/json'}
        body = None
        if self.command in ('POST', 'PATCH', 'PUT'):
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 <= length <= (TERRAIN_LIMIT if TERRAIN.fullmatch(parsed.path) else MONSTER_SHEET_LIMIT if parsed.path == '/gm/workspace/tokens' or PREP_PUT.fullmatch(parsed.path) or NOTES.fullmatch(parsed.path) else 12000):
                    raise ValueError()
                body = self.rfile.read(length)
                payload = json.loads(body) if body else {}
                if not isinstance(payload, dict):
                    raise ValueError()
            except (ValueError, json.JSONDecodeError):
                self._error(400, 'Corpo inválido')
                return
            # Spell rules, costs and targets are validated by the backend (GM token required there too).
            if parsed.path == '/gm/combat/effects' and payload.get('action') not in {'start', 'end', 'next_turn', 'dorn_guard', 'dorn_vanguard', 'dorn_diagnose', 'dorn_spell_cast'}:
                self._error(405, 'Ação indisponível nesta versão')
                return
            if (parsed.path == '/gm/workspace/maps/active' and set(payload) != {'map_id'}) or (
                    parsed.path == '/gm/workspace/table-mode' and (set(payload) != {'table_mode'} or payload['table_mode'] not in {'digital', 'physical'})) or (DISPOSITION.fullmatch(parsed.path) and set(payload) != {'disposition'}) or (POSITION.fullmatch(parsed.path) and set(payload) != {'latitude', 'longitude'}) or (
                    self.command == 'PATCH' and TOKEN_EDIT.fullmatch(parsed.path) and (not payload or not set(payload) <= TOKEN_EDIT_KEYS)) or (
                    self.command == 'PUT' and not self._put_body_ok(parsed.path, payload)) or (
                    DEFINITION.fullmatch(parsed.path) and (not set(payload) <= {'fields', 'reason'} or not isinstance(payload.get('fields'), dict)
                                                       or not payload['fields'] or not set(payload['fields']) <= {'level', 'experience'})):
                self._error(400, 'Corpo inválido')
                return
            if parsed.path == '/gm/workspace/tokens' and not (
                    (payload.get('token_type') == 'character' and payload.get('character_id') in {'dorn7','vezemir','raziel','morthak','varkh'})
                    or (payload.get('token_type') == 'monster' and not payload.get('image_data_base64'))
                    or (payload.get('token_type') == 'location' and isinstance(payload.get('sheet'), dict)
                        and payload['sheet'].get('kind') == 'city' and not payload.get('image_data_base64'))):
                self._error(405, 'Cadastro indisponível nesta versão')
                return
            headers['Content-Type'] = 'application/json'
        request = Request(self.server.backend + route, data=body, headers=headers, method=self.command)
        opener = build_opener(ProxyHandler({}), NoRedirect())
        try:
            response = opener.open(request, timeout=15)
        except HTTPError as error:
            response = error
            sys.stderr.write('%s %s %s upstream %d\n' % (time.strftime('%H:%M:%S'), self.command, parsed.path, error.code))
            sys.stderr.flush()
        except (URLError, TimeoutError, OSError):
            self._error(502, 'Backend indisponível')
            return
        with response:
            data = response.read(5 * 1024 * 1024 + 1)
            if len(data) > 5 * 1024 * 1024:
                self._error(502, 'Resposta acima do limite')
                return
            self.send_response(response.code)
            self.send_header('Content-Type', response.headers.get('Content-Type', 'application/json'))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    def do_GET(self):
        path = urlsplit(self.path).path
        if READS.fullmatch(path):
            self._proxy()
        elif path.startswith(('/workspace', '/characters', '/combat', '/gm', '/player', '/sessions', '/media')):
            self._error(404, 'Rota indisponível nesta prévia')
        else:
            self._static(path)

    def _static(self, path):
        """Static export with gzip, ETag and revalidation (no re-download after the first load)."""
        local = Path(self.translate_path(path))
        if local.is_dir():
            local = local / 'index.html'
        if not local.is_file():
            super().do_GET()
            return
        stat = local.stat()
        etag = '"%x-%x"' % (stat.st_mtime_ns, stat.st_size)
        compress = local.suffix in COMPRESSIBLE and 'gzip' in self.headers.get('Accept-Encoding', '')
        if compress:
            etag = etag[:-1] + '-gz"'
        if self.headers.get('If-None-Match') == etag:
            self.send_response(304)
            self.send_header('ETag', etag)
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            return
        data = gzipped(local) if compress else local.read_bytes()
        self.send_response(200)
        content_type = self.extensions_map.get(local.suffix) or mimetypes.guess_type(local.name)[0] or 'application/octet-stream'
        self.send_header('Content-Type', content_type)
        if compress:
            self.send_header('Content-Encoding', 'gzip')
        self.send_header('Vary', 'Accept-Encoding')
        self.send_header('ETag', etag)
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        self._proxy()

    def do_PATCH(self):
        self._proxy()

    def do_DELETE(self):
        self._proxy()

    def do_PUT(self):
        self._proxy()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--backend', default='http://127.0.0.1:8787')
    parser.add_argument('--port', type=int, default=8872)
    parser.add_argument('--directory', type=Path, default=PROJECT / 'build/web')
    args = parser.parse_args()
    url = urlsplit(args.backend)
    if (url.scheme != 'http' or url.hostname not in {'127.0.0.1', 'localhost'}
            or url.username or url.password or url.path or url.query or url.fragment):
        parser.error('Use apenas a origem HTTP do backend local')
    if not (args.directory / 'index.html').is_file():
        parser.error('Exporte o preset Web antes de iniciar a prévia')
    handler = partial(Preview, directory=str(args.directory.resolve()))
    server = ThreadingHTTPServer(('127.0.0.1', args.port), handler)
    server.backend = args.backend.rstrip('/')
    print(f'Companion 3.0 em http://127.0.0.1:{args.port}/', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
