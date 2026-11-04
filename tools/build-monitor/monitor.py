"""Loopback-only library viewer with explicit existing-app launch and settings actions."""
import argparse
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import time
from urllib.parse import parse_qsl, urlsplit


LABELS = {
    'build nx_extract': 'Préparer l’extracteur',
    'extract': 'Extraire le jeu et sa mise à jour',
    'rewrite': 'Adapter le code au Mac',
    'shader split': 'Extraire les shaders',
    'Mac shaders': 'Compiler les shaders Metal',
    'Mac host': 'Construire le moteur Mac',
    'Mac app': 'Assembler l’application',
    'pipeline archive': 'Préparer les pipelines graphiques',
}
# shortcut: reads human-readable stage lines, use JSON events if upstream changes their format.
EVENT = re.compile(r'^\[(\d{2}:\d{2}:\d{2})\] (?:(✓|✗) )?\[(\d+)/(\d+)\] (.+)$')


def seconds(value):
    result = 0
    for part in value.split(':'):
        result = result * 60 + int(part)
    return result


def parse(text, now, start, running):
    stages = {}
    total = current = 0
    eta = eta_at = None
    last_at = None
    failed = False
    previous_clock = -1
    day = datetime.fromtimestamp(start).replace(hour=0, minute=0, second=0, microsecond=0)
    for line in text.splitlines():
        event = EVENT.match(line)
        if not event:
            continue
        clock, mark, index, count, detail = event.groups()
        clock = seconds(clock)
        if clock < previous_clock:
            day += timedelta(days=1)
        previous_clock = clock
        at = day.timestamp() + clock
        index, count = int(index), int(count)
        total, current = count, index
        name = next((label for key, label in LABELS.items() if detail.lower().startswith(key.lower())), 'Étape de construction')
        old = stages.get(index)
        started = old['started'] if old else at
        stages[index] = {'index': index, 'name': name, 'status': 'done' if mark == '✓' else 'error' if mark == '✗' else 'current', 'started': started, 'duration': max(0, int(at - started)) if mark else None}
        failed = failed or mark == '✗'
        # ETA describes this stage only, never the total remaining build time.
        estimate = re.search(r'ETA (\d+(?::\d+){1,2})', detail)
        eta = seconds(estimate.group(1)) if estimate and not mark else None
        eta_at = at if eta is not None else None
        last_at = at
    complete = bool(total and current == total and stages[current]['status'] == 'done')
    state = 'done' if complete else 'error' if failed else 'running' if running else 'stopped'
    age = max(0, int(now - last_at)) if last_at else None
    # Expired estimates are discarded rather than displaying a false zero.
    remaining = eta - (now - eta_at) if eta is not None else None
    return {'state': state, 'current': current, 'total': total, 'stages': list(stages.values()), 'elapsed': max(0, int((last_at if state != 'running' and last_at else now) - start)), 'stage_eta': int(remaining) if remaining is not None and remaining > 0 and age <= 60 else None, 'updated_age': age, 'checked_at': now}


def alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def parse_json(text, now, start, state, finished=None):
    stages = {}
    current = total = 0
    eta = event_at = None
    fraction = None
    last_at = start
    for line in text.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        kind = event.get('ev')
        if kind not in ('stage', 'stage_end', 'step', 'progress'):
            continue
        last_at = event.get('t', start)
        index = event.get('k', current)
        total = event.get('n', total)
        if kind == 'stage':
            current = index
            name = next((label for key, label in LABELS.items() if event.get('name', '').lower().startswith(key.lower())), 'Étape de construction')
            stages[index] = {'index': index, 'name': name, 'status': 'current', 'started': last_at, 'duration': None}
            eta = event_at = fraction = None
        elif kind == 'stage_end' and index in stages:
            stages[index].update(status='done' if event.get('ok') else 'error', duration=event.get('elapsed', 0))
            eta = event_at = fraction = None
        elif kind == 'step':
            eta = event_at = fraction = None
        elif kind == 'progress' and index == current:
            eta, event_at, fraction = event.get('eta'), last_at, event.get('frac')
    remaining = eta - max(0, now - event_at) if isinstance(eta, (int, float)) and event_at else None
    end = finished if finished is not None else now if state == 'running' else last_at
    return {'state': state, 'current': current, 'total': total, 'stages': list(stages.values()), 'elapsed': max(0, int(end - start)), 'stage_eta': int(remaining) if state == 'running' and remaining is not None and remaining > 0 and now - event_at < 60 else None, 'stage_frac': fraction if state == 'running' else None, 'updated_age': max(0, int(now - last_at)), 'checked_at': now}


# shortcut: fixed upstream path; a missing file or renamed section yields an empty catalogue.
GAMES_README = Path(__file__).resolve().parents[2] / 'source/dm/games/README.md'


def catalog(text):
    """Parse upstream's '## Games' table into one dict per referenced profile."""
    games = []
    in_games = table = False
    for line in text.splitlines():
        if line.lstrip().startswith('#'):
            in_games, table = line.strip() == '## Games', False
            continue
        if not in_games or not line.lstrip().startswith('|'):
            if table:
                break  # the Games table ended
            continue
        table = True
        cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
        if len(cells) != 6:
            continue
        link = re.fullmatch(r'\[(.+)\]\([^()]*\)', cells[0])
        game = {'name': (link.group(1) if link else cells[0]).strip('`'), 'title_id': cells[1].strip('`'), 'build': cells[2].strip('`'), 'sdk': cells[3].strip('`'), 'engine': cells[4].strip('`'), 'graphics': cells[5].strip('`')}
        if game['name'] and re.fullmatch(r'[0-9A-Fa-f]{16}', game['title_id']):
            games.append(game)
    return games


HOSTS = ('127.0.0.1:8767', 'localhost:8767')
SLUG = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*')
CSP = "default-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'"

MAX_ART = 8 << 20
ART_ID = re.compile(r'/art/catalog/([0-9A-F]{16})\.jpg')


def handler(status, play=None, settings=None, save_settings=None):
    page = Path(__file__).with_name('index.html')
    base = page.parent
    protos = base / 'protos'
    # Explicit routes only: no directory is ever served.
    assets = {'/art/' + name + '.jpg': (base / 'art' / (name + '.jpg'), 'image/jpeg') for name in ('stardew', 'stardew-scene', 'zelda', 'pokemon', 'mario', 'n64')}
    assets['/nx-components.js'] = (base / 'nx-components.js', 'text/javascript; charset=utf-8')
    assets['/nx-shared.css'] = (protos / 'nx-shared.css', 'text/css; charset=utf-8')
    for route, name in (('stardew-logo', 'stardew-logo'), ('avatar', 'avatar'), ('stardew-hero', 'hero-background')):
        assets[f'/art/{route}.png'] = (protos / 'cinema-block-1-assets' / (name + '.png'), 'image/png')

    for tid in ('01004B3023412000', '0100C9A00ECE6000', '010018E011D92000'):
        assets[f'/art/library/{tid}.jpg'] = (base / 'art' / 'library' / f'{tid}.jpg', 'image/jpeg')

    covers = base.resolve() / 'art' / 'catalog'

    def safe(path, limit):
        # Real file directly inside art/catalog, small enough; re-checked on every request so late files appear without restart.
        try:
            return not path.is_symlink() and path.is_file() and path.resolve().parent == covers and path.stat().st_size <= limit
        except OSError:
            return False

    def profiles():
        try:
            return catalog(GAMES_README.read_text())
        except OSError:
            return []

    def kinds():
        path = base / 'art' / 'catalog' / 'sources.json'
        try:
            data = json.loads(path.read_text()) if safe(path, 1 << 20) else {}
        except (OSError, ValueError):
            data = {}
        return data if isinstance(data, dict) else {}

    def asset(route):
        path, kind = assets[route]
        # The file and every parent must stay inside the monitor directory (no symlink out).
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(base.resolve()):
            return None
        return path.read_bytes(), kind

    class Handler(BaseHTTPRequestHandler):
        def reply(self, code, body, kind):
            self.send_response(code)
            self.send_header('Content-Type', kind)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', CSP)
            self.end_headers()
            self.wfile.write(body)

        def fail(self, code, message):
            self.reply(code, json.dumps({'error': message}, ensure_ascii=False).encode(), 'application/json; charset=utf-8')

        def do_GET(self):
            if self.headers.get('Host') not in HOSTS:
                self.send_error(403)
                return
            route = urlsplit(self.path).path
            if route == '/':
                body, kind = page.read_bytes(), 'text/html; charset=utf-8'
            elif route == '/status':
                try:
                    body = json.dumps(status(), ensure_ascii=False).encode()
                    kind = 'application/json; charset=utf-8'
                except Exception:
                    self.send_error(503, 'Library temporarily unavailable')
                    return
            elif route == '/settings' and settings is not None:
                query = parse_qsl(urlsplit(self.path).query, keep_blank_values=True)
                if len(query) != 1 or query[0][0] != 'slug' or not SLUG.fullmatch(query[0][1]):
                    return self.fail(400, 'Identifiant de jeu invalide')
                try:
                    body = json.dumps(settings(query[0][1]), ensure_ascii=False).encode()
                    kind = 'application/json; charset=utf-8'
                except Exception as error:
                    code = getattr(error, 'status', None)
                    if code in (400, 409, 502):
                        return self.fail(code, str(error))
                    return self.fail(502, 'Réglages indisponibles')
            elif route == '/catalog':
                manifest = kinds()
                rows = profiles()
                for row in rows:
                    tid = row['title_id'].upper()
                    entry = manifest.get(tid)
                    art = f'/art/catalog/{tid}.jpg' if safe(base / 'art' / 'catalog' / f'{tid}.jpg', MAX_ART) else None
                    # Paths never come from the manifest: only the profile ID names a file; the manifest only labels it.
                    row['art'] = art
                    row['art_kind'] = entry.get('kind') if art and isinstance(entry, dict) and entry.get('kind') in ('cover', 'screenshot') else None
                body = json.dumps({'games': rows}, ensure_ascii=False).encode()
                kind = 'application/json; charset=utf-8'
            elif (match := ART_ID.fullmatch(route)) and match[1] in {row['title_id'].upper() for row in profiles()} and safe(base / 'art' / 'catalog' / f'{match[1]}.jpg', MAX_ART):
                body, kind = (base / 'art' / 'catalog' / f'{match[1]}.jpg').read_bytes(), 'image/jpeg'
            elif route in assets and (found := asset(route)):
                body, kind = found
            else:
                self.send_error(404)
                return
            self.reply(200, body, kind)

        def do_POST(self):
            if play is None and save_settings is None:
                self.send_error(501)  # read-only mode
                return
            self.close_connection = True  # the body may stay unread on an early refusal
            host = self.headers.get('Host')
            if host not in HOSTS:
                self.send_error(403)
                return
            route = urlsplit(self.path).path
            if route not in ('/play', '/settings'):
                self.send_error(404)
                return
            if (route == '/play' and play is None) or (route == '/settings' and save_settings is None):
                self.send_error(501)
                return
            if self.headers.get('Origin') != f'http://{host}':
                return self.fail(403, 'Origine refusée')
            if self.headers.get_content_type() != 'application/json':
                return self.fail(415, 'Type de contenu non pris en charge')
            length = self.headers.get('Content-Length', '')
            if 'Transfer-Encoding' in self.headers or not length.isascii() or not length.isdigit():
                return self.fail(400, 'Longueur de requête invalide')
            if int(length) > (16384 if route == '/settings' else 1024):
                return self.fail(413, 'Requête trop volumineuse')
            try:
                data = json.loads(self.rfile.read(int(length)))
            except (ValueError, RecursionError):
                return self.fail(400, 'JSON invalide')
            if not isinstance(data, dict) or not isinstance(data.get('slug'), str) or not SLUG.fullmatch(data['slug']):
                return self.fail(400, 'Requête invalide')
            if route == '/play':
                if set(data) - {'slug', 'show_launcher'} or 'show_launcher' in data and not isinstance(data['show_launcher'], bool):
                    return self.fail(400, 'Requête invalide')
            elif set(data) != {'slug', 'values'} or not isinstance(data['values'], dict):
                return self.fail(400, 'Requête invalide')
            try:
                if route == '/settings':
                    save_settings(data['slug'], data['values'])
                elif data.get('show_launcher', True):
                    play(data['slug'])  # Backward-compatible one-argument callback.
                else:
                    play(data['slug'], show_launcher=False)
            except Exception as error:
                # Only business errors that carry an HTTP status expose their (already safe) message.
                code = getattr(error, 'status', None)
                if code in (400, 409, 502):
                    return self.fail(code, str(error))
                return self.fail(502, 'Lancement impossible' if route == '/play' else 'Enregistrement impossible')
            self.reply(200, b'{"ok": true}', 'application/json; charset=utf-8')

        def log_message(self, *_):
            pass

    return Handler


def serve(status, play=None, settings=None, save_settings=None):
    server = ThreadingHTTPServer(('127.0.0.1', 8767), handler(status, play, settings, save_settings))
    print('Build monitor: http://127.0.0.1:8767', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log', type=Path)
    parser.add_argument('pid', type=int)
    args = parser.parse_args()
    if args.pid <= 0 or not args.log.is_file():
        parser.error('An existing build log and a positive process ID are required')
    start = args.log.stat().st_birthtime
    def status():
        with args.log.open('rb') as stream:
            text = stream.read(2 * 1024 * 1024).decode('utf-8', errors='replace')
        return parse(text, time.time(), start, alive(args.pid))
    serve(status)


if __name__ == '__main__':
    main()
