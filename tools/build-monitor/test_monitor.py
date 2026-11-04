from datetime import datetime
import unittest
from monitor import parse, parse_json, catalog
import json
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
import shutil
import subprocess
import tempfile
from threading import Thread
from unittest.mock import patch
import monitor
from monitor import handler


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), handler(lambda: {'games': [], 'checked_at': 1}))
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop_server)

    def stop_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def request(self, route, host='127.0.0.1:8767', method='GET'):
        connection = HTTPConnection('127.0.0.1', self.server.server_port, timeout=3)
        self.addCleanup(connection.close)
        connection.request(method, route, headers={'Host':host})
        response = connection.getresponse()
        return response.status, dict(response.getheaders()), response.read()

    def test_page_status_and_local_art(self):
        status, headers, body = self.request('/')
        self.assertEqual(status, 200)
        self.assertIn(b'Biblioth', body)
        self.assertIn("img-src 'self'", headers['Content-Security-Policy'])
        self.assertEqual(json.loads(self.request('/status')[2])['games'], [])
        for name in ('stardew', 'stardew-scene', 'zelda', 'pokemon', 'mario', 'n64'):
            status, headers, body = self.request(f'/art/{name}.jpg')
            self.assertEqual(status, 200)
            self.assertEqual(headers['Content-Type'], 'image/jpeg')
            self.assertTrue(body.startswith(b'\xff\xd8'))

    def test_only_allowlisted_artwork_is_served(self):
        for route in ('/art/sources.json', '/art/../monitor.py', '/art/%2e%2e/monitor.py', '/keys/prod.keys', '/art/other.jpg'):
            self.assertEqual(self.request(route)[0], 404)
        self.assertEqual(self.request('/', host='untrusted.example')[0], 403)
        self.assertEqual(self.request('/status', method='POST')[0], 501)

    def test_dashboard_logic(self):
        if not shutil.which('node'):
            self.fail('Node.js is required to run dashboard JavaScript tests')
        subprocess.run(['node', '--test', str(Path(__file__).with_name('test_dashboard.cjs'))], check=True)


    def test_catalog_route_serves_the_games_table(self):
        status, headers, body = self.request('/catalog')
        self.assertEqual(status, 200)
        self.assertIsInstance(json.loads(body)['games'], list)


class StaticAndPlayTests(unittest.TestCase):
    HOST = '127.0.0.1:8767'

    def start(self, play=None, settings=None, save_settings=None):
        server = ThreadingHTTPServer(('127.0.0.1', 0), handler(lambda: {'games': []}, play, settings, save_settings))
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        def stop():
            server.shutdown()
            server.server_close()
            thread.join()
        self.addCleanup(stop)
        return server.server_port

    def call(self, port, method, route, body=None, headers=None):
        connection = HTTPConnection('127.0.0.1', port, timeout=3)
        self.addCleanup(connection.close)
        connection.request(method, route, body=body, headers=headers or {'Host': self.HOST})
        response = connection.getresponse()
        return response.status, dict(response.getheaders()), response.read()

    def post(self, port, payload=b'{"slug":"zelda"}', **overrides):
        headers = {'Host': self.HOST, 'Origin': f'http://{self.HOST}', 'Content-Type': 'application/json'}
        headers.update(overrides)
        return self.call(port, 'POST', '/play', payload, {k: v for k, v in headers.items() if v is not None})

    def test_static_routes_and_security_headers(self):
        port = self.start()
        for route, kind in (('/nx-components.js', 'text/javascript'), ('/nx-shared.css', 'text/css'), ('/art/stardew-logo.png', 'image/png'), ('/art/avatar.png', 'image/png'), ('/art/stardew-hero.png', 'image/png'), ('/art/library/01004B3023412000.jpg', 'image/jpeg'), ('/art/library/0100C9A00ECE6000.jpg', 'image/jpeg'), ('/art/library/010018E011D92000.jpg', 'image/jpeg')):
            status, headers, body = self.call(port, 'GET', route)
            self.assertEqual((status, headers['Content-Type'].split(';')[0]), (200, kind))
            self.assertTrue(body)
            self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')
            self.assertEqual(headers['Cache-Control'], 'no-store')
            self.assertIn("script-src 'self'", headers['Content-Security-Policy'])
        for route in ('/protos/nx-shared.css', '/art/hero-background.png', '/art/reference-hero.png', '/art/sources.json', '/art/library/sources.json', '/art/library/', '/art/library/0123456789ABCDEF.jpg', '/art/library/01004B3023412000.jpg/../sources.json', '/nx-components.js/../monitor.py', '/art/%2e%2e/monitor.py', '/protos/'):
            self.assertEqual(self.call(port, 'GET', route)[0], 404)

    def test_symlinked_or_escaping_assets_are_refused(self):
        with tempfile.TemporaryDirectory(dir='/private/var/folders/0_/1mcnsfdn41z6sltt2pmtqcrc0000gn/T/opencode') as tmp:
            tmp = Path(tmp)
            outside = tmp / 'outside.txt'
            outside.write_text('secret')
            site = tmp / 'site'
            (site / 'protos/cinema-block-1-assets').mkdir(parents=True)
            (site / 'art').mkdir()
            (site / 'index.html').write_text('x')
            (site / 'nx-components.js').symlink_to(outside)
            (site / 'protos/nx-shared.css').write_text('ok')
            (site / 'protos/cinema-block-1-assets/avatar.png').write_bytes(b'png')
            elsewhere = tmp / 'elsewhere'
            elsewhere.mkdir()
            (elsewhere / 'stardew-logo.png').write_text('secret')
            (site / 'art/stardew.jpg').symlink_to(outside)
            (site / 'art/library').mkdir()
            (site / 'art/library/01004B3023412000.jpg').symlink_to(outside)
            with patch.object(monitor, '__file__', str(site / 'monitor.py')):
                port = self.start()
            self.assertEqual(self.call(port, 'GET', '/nx-components.js')[0], 404)
            self.assertEqual(self.call(port, 'GET', '/art/stardew.jpg')[0], 404)
            self.assertEqual(self.call(port, 'GET', '/art/library/01004B3023412000.jpg')[0], 404)
            self.assertEqual(self.call(port, 'GET', '/nx-shared.css')[2], b'ok')
            self.assertEqual(self.call(port, 'GET', '/art/avatar.png')[2], b'png')
            # A parent directory replaced by a symlink must not leak files either.
            (site / 'protos/cinema-block-1-assets/avatar.png').unlink()
            (site / 'protos/cinema-block-1-assets').rmdir()
            (site / 'protos/cinema-block-1-assets').symlink_to(elsewhere)
            self.assertEqual(self.call(port, 'GET', '/art/stardew-logo.png')[0], 404)

    def catalog_site(self, tmp):
        site = Path(tmp) / 'site'
        (site / 'art/catalog').mkdir(parents=True)
        (site / 'index.html').write_text('x')
        readme = Path(tmp) / 'README.md'
        readme.write_text(SAMPLE)
        return site, readme

    def serve_catalog(self, site, readme):
        with patch.object(monitor, '__file__', str(site / 'monitor.py')), patch.object(monitor, 'GAMES_README', readme):
            return self.start()

    def test_catalog_art_is_allowlisted_by_profile_and_discovered_late(self):
        known, other = '01003FC01670C000', '01008D7016438000'
        with tempfile.TemporaryDirectory(dir='/private/var/folders/0_/1mcnsfdn41z6sltt2pmtqcrc0000gn/T/opencode') as tmp:
            site, readme = self.catalog_site(tmp)
            port = self.serve_catalog(site, readme)
            games = {g['title_id']: g for g in json.loads(self.call(port, 'GET', '/catalog')[2])['games']}
            self.assertEqual((games[known]['art'], games[known]['art_kind']), (None, None))
            self.assertEqual(self.call(port, 'GET', f'/art/catalog/{known}.jpg')[0], 404)
            # Files arrive after start: no restart needed. The manifest labels but never names a file.
            (site / 'art/catalog' / f'{known}.jpg').write_bytes(b'\xff\xd8jpeg')
            (site / 'art/catalog' / 'sources.json').write_text(json.dumps({known: {'name': 'x', 'file': '../../../secret.txt', 'source': 'https://example.com', 'kind': 'cover'}, other: {'kind': 'bogus'}}))
            (site / 'art/catalog' / '0123456789ABCDEF.jpg').write_bytes(b'\xff\xd8other')
            games = {g['title_id']: g for g in json.loads(self.call(port, 'GET', '/catalog')[2])['games']}
            self.assertEqual((games[known]['art'], games[known]['art_kind']), (f'/art/catalog/{known}.jpg', 'cover'))
            self.assertEqual((games[other]['art'], games[other]['art_kind']), (None, None))
            self.assertEqual(set(games[known]) & {'file', 'source'}, set())
            status, headers, body = self.call(port, 'GET', f'/art/catalog/{known}.jpg')
            self.assertEqual((status, headers['Content-Type'], body), (200, 'image/jpeg', b'\xff\xd8jpeg'))
            self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')
            # Present file but not a catalog profile, raw manifest, other names and traversal stay 404.
            for route in ('/art/catalog/0123456789ABCDEF.jpg', f'/art/catalog/{known.lower()}.jpg', '/art/catalog/sources.json', '/art/catalog/', '/art/catalog', f'/art/catalog/{known}.png', f'/art/catalog/..%2f{known}.jpg', f'/art/catalog/{known}.jpg/../sources.json'):
                self.assertEqual(self.call(port, 'GET', route)[0], 404, route)

    def test_catalog_art_refuses_symlinks_and_oversized_files(self):
        known = '01003FC01670C000'
        with tempfile.TemporaryDirectory(dir='/private/var/folders/0_/1mcnsfdn41z6sltt2pmtqcrc0000gn/T/opencode') as tmp:
            site, readme = self.catalog_site(tmp)
            secret = Path(tmp) / 'secret.jpg'
            secret.write_bytes(b'secret')
            (site / 'art/catalog' / f'{known}.jpg').symlink_to(secret)
            (site / 'art/catalog/sources.json').symlink_to(secret)
            port = self.serve_catalog(site, readme)
            self.assertEqual(self.call(port, 'GET', f'/art/catalog/{known}.jpg')[0], 404)
            self.assertIsNone(json.loads(self.call(port, 'GET', '/catalog')[2])['games'][0]['art'])
            (site / 'art/catalog' / f'{known}.jpg').unlink()
            with patch.object(monitor, 'MAX_ART', 3):
                (site / 'art/catalog' / f'{known}.jpg').write_bytes(b'toolarge')
                self.assertEqual(self.call(port, 'GET', f'/art/catalog/{known}.jpg')[0], 404)
            # A symlinked directory must not expose outside files either.
            (site / 'art/catalog' / f'{known}.jpg').unlink()
            (site / 'art/catalog/sources.json').unlink()
            (site / 'art/catalog').rmdir()
            outside = Path(tmp) / 'outside'
            outside.mkdir()
            (outside / f'{known}.jpg').write_bytes(b'secret')
            (site / 'art/catalog').symlink_to(outside)
            self.assertEqual(self.call(port, 'GET', f'/art/catalog/{known}.jpg')[0], 404)

    def test_get_and_read_only_mode_never_play(self):
        calls = []
        port = self.start(calls.append)
        self.assertEqual(self.call(port, 'GET', '/play')[0], 404)
        self.assertEqual(calls, [])
        readonly = self.start()
        self.assertEqual(self.post(readonly)[0], 501)

    def test_play_success(self):
        calls = []
        port = self.start(calls.append)
        status, headers, body = self.post(port)
        self.assertEqual((status, json.loads(body)), (200, {'ok': True}))
        self.assertEqual(calls, ['zelda'])
        self.assertEqual(headers['Cache-Control'], 'no-store')
        self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')
        self.assertIn('Content-Security-Policy', headers)
        self.assertEqual(self.post(port, Host='localhost:8767', Origin='http://localhost:8767', **{'Content-Type': 'application/json; charset=utf-8'})[0], 200)

    def test_play_refuses_untrusted_requests_without_calling(self):
        calls = []
        port = self.start(calls.append)
        cases = [
            (403, {'Host': 'untrusted.example', 'Origin': 'http://untrusted.example'}, b'{"slug":"zelda"}'),
            (403, {'Origin': None}, b'{"slug":"zelda"}'),
            (403, {'Origin': 'http://localhost:8767'}, b'{"slug":"zelda"}'),
            (403, {'Origin': 'http://127.0.0.1:9999'}, b'{"slug":"zelda"}'),
            (403, {'Origin': 'null'}, b'{"slug":"zelda"}'),
            (415, {'Content-Type': 'text/plain'}, b'{"slug":"zelda"}'),
            (415, {'Content-Type': None}, b'{"slug":"zelda"}'),
            (413, {}, b'{"slug":"' + b'a' * 1100 + b'"}'),
            (400, {}, b'not json'),
            (400, {}, b'[]'),
            (400, {}, b'{}'),
            (400, {}, b'{"slug":"zelda","extra":1}'),
            (400, {}, b'{"slug":1}'),
            (400, {}, b'{"slug":"../zelda"}'),
            (400, {}, b'{"slug":"Zelda"}'),
            (400, {}, b'{"slug":"zelda\\n"}'),
            (400, {'Content-Length': 'abc'}, b'{"slug":"zelda"}'),
        ]
        for code, overrides, payload in cases:
            with self.subTest(code=code, overrides=overrides, payload=payload[:30]):
                self.assertEqual(self.post(port, payload, **overrides)[0], code)
        self.assertEqual(self.call(port, 'POST', '/other', b'{}', {'Host': self.HOST})[0], 404)
        self.assertEqual(calls, [])

    def test_play_option_is_boolean_and_only_false_adds_callback_option(self):
        calls = []
        def play(slug, **options):
            calls.append((slug, options))
        port = self.start(play)
        self.assertEqual(self.post(port, b'{"slug":"zelda","show_launcher":false}')[0], 200)
        self.assertEqual(self.post(port, b'{"slug":"zelda","show_launcher":true}')[0], 200)
        self.assertEqual(calls, [('zelda', {'show_launcher': False}), ('zelda', {})])
        for payload in (b'{"slug":"zelda","show_launcher":0}', b'{"slug":"zelda","show_launcher":"false"}', b'{"slug":"zelda","show_launcher":null}'):
            self.assertEqual(self.post(port, payload)[0], 400)
        self.assertEqual(len(calls), 2)

    def test_get_settings_is_exact_json_and_errors_stay_safe(self):
        calls = []
        def settings(slug):
            calls.append(slug)
            return {'slug': slug, 'settings': [{'label': '<script>not HTML</script>', 'value': '30', 'locked': False}], 'runtime': {'state': 'stopped'}}
        port = self.start(settings=settings)
        status, headers, body = self.call(port, 'GET', '/settings?slug=zelda')
        self.assertEqual(status, 200)
        self.assertEqual(headers['Content-Type'], 'application/json; charset=utf-8')
        self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(json.loads(body)['settings'][0]['label'], '<script>not HTML</script>')
        self.assertEqual(calls, ['zelda'])
        for route in ('/settings', '/settings?slug=', '/settings?slug=Zelda', '/settings?slug=../zelda', '/settings?slug=zelda&extra=1', '/settings?slug=zelda&slug=other'):
            self.assertEqual(self.call(port, 'GET', route)[0], 400, route)
        self.assertEqual(calls, ['zelda'])
        def crash(slug):
            raise OSError('/Users/sofian/secret/path')
        status, _, body = self.call(self.start(settings=crash), 'GET', '/settings?slug=zelda')
        self.assertEqual(status, 502)
        self.assertNotIn(b'secret', body)

    def test_post_settings_security_limits_and_callback(self):
        calls = []
        def save(slug, values):
            calls.append((slug, values))
        port = self.start(save_settings=save)
        headers = {'Host': self.HOST, 'Origin': f'http://{self.HOST}', 'Content-Type': 'application/json'}
        payload = json.dumps({'slug': 'zelda', 'values': {'DM_METAL_HUD': '1'}}).encode()
        status, _, body = self.call(port, 'POST', '/settings', payload, headers)
        self.assertEqual((status, json.loads(body)), (200, {'ok': True}))
        self.assertEqual(calls, [('zelda', {'DM_METAL_HUD': '1'})])
        cases = [
            (403, dict(headers, Origin='http://evil.example'), payload),
            (415, dict(headers, **{'Content-Type': 'text/plain'}), payload),
            (400, headers, b'[]'),
            (400, headers, b'{"slug":"zelda"}'),
            (400, headers, b'{"slug":"zelda","values":[]}'),
            (400, headers, b'{"slug":"zelda","values":{},"extra":1}'),
            (400, headers, b'{"slug":"../zelda","values":{}}'),
            (413, headers, b'{"slug":"zelda","values":{"x":"' + b'a' * 17000 + b'"}}'),
        ]
        for code, request_headers, request_body in cases:
            with self.subTest(code=code, size=len(request_body)):
                self.assertEqual(self.call(port, 'POST', '/settings', request_body, request_headers)[0], code)
        self.assertEqual(self.call(port, 'PUT', '/settings', payload, headers)[0], 501)
        self.assertEqual(self.post(port)[0], 501)
        self.assertEqual(len(calls), 1)

    def test_post_settings_business_and_partial_failure_messages(self):
        class Business(Exception):
            status = 502
        def save(slug, values):
            raise Business('Écriture partielle : rechargez les valeurs')
        status, _, body = self.call(self.start(save_settings=save), 'POST', '/settings', b'{"slug":"zelda","values":{}}', {'Host': self.HOST, 'Origin': f'http://{self.HOST}', 'Content-Type': 'application/json'})
        self.assertEqual((status, json.loads(body)), (502, {'error': 'Écriture partielle : rechargez les valeurs'}))

    def test_play_errors_are_safe_and_generic(self):
        class Business(Exception):
            status = 409
        def fail(slug):
            raise Business('Un build est en cours')
        status, _, body = self.post(self.start(fail))
        self.assertEqual((status, json.loads(body)), (409, {'error': 'Un build est en cours'}))
        def crash(slug):
            raise OSError('/Users/sofian/secret/path')
        status, _, body = self.post(self.start(crash))
        self.assertEqual(status, 502)
        self.assertNotIn(b'secret', body)


SAMPLE = '''# Game profiles

| Who | Picks | Reads |
|---|---|---|
| Host | GAME= | tables |

## Games

One row per profile.

| Game | Title ID | Build | SDK | Engine | Graphics |
|---|---|---|---|---|---|
| [13 Sentinels: Aegis Rim](01003FC01670C000/README.md) | `01003FC01670C000` | 1.10 | 11.4.3 | Vanillaware's engine | NVN |
| [13 Sentinels: Aegis Rim, Asian release](01008D7016438000/README.md) | `01008D7016438000` | 1.00 (base) | 11.4.3 | Vanillaware's engine | NVN |
| Broken row | nothex | 1.0 | | | |

## Keys

| Key | Meaning |
|---|---|
| `name` | Display name |
'''


class CatalogTests(unittest.TestCase):
    def test_parses_links_backticks_and_base_builds(self):
        rows = catalog(SAMPLE)
        self.assertEqual(rows, [
            {'name': '13 Sentinels: Aegis Rim', 'title_id': '01003FC01670C000', 'build': '1.10', 'sdk': '11.4.3', 'engine': "Vanillaware's engine", 'graphics': 'NVN'},
            {'name': '13 Sentinels: Aegis Rim, Asian release', 'title_id': '01008D7016438000', 'build': '1.00 (base)', 'sdk': '11.4.3', 'engine': "Vanillaware's engine", 'graphics': 'NVN'},
        ])

    def test_stops_at_table_end_and_skips_malformed_rows(self):
        self.assertEqual(catalog('# No games table\n| a | b | c | d | e | 01003FC01670C000 |\n'), [])


class ProgressTests(unittest.TestCase):
    def setUp(self):
        self.start = datetime(2026, 11, 3, 0, 58).timestamp()

    def test_stage_changes_clear_previous_eta(self):
        text = '[00:58:00] [1/6] rewrite · compiling: 50%, ETA 0:20\n[00:58:10] ✓ [1/6] rewrite (0:10)\n[00:58:11] [2/7] Mac host · building …'
        state = parse(text, self.start + 15, self.start, True)
        self.assertEqual((state['total'], state['current'], state['stage_eta']), (7, 2, None))
        self.assertEqual(state['stages'][0]['status'], 'done')

    def test_eta_counts_down_then_expires(self):
        text = '[00:58:00] [1/7] rewrite · compiling: ETA 0:20'
        self.assertEqual(parse(text, self.start+5, self.start, True)['stage_eta'], 15)
        self.assertIsNone(parse(text, self.start+30, self.start, True)['stage_eta'])

    def test_success_requires_final_completed_stage(self):
        text = '[00:58:00] [7/7] Mac app · starting\n[00:58:04] ✓ [7/7] Mac app (0:04)'
        self.assertEqual(parse(text, self.start+6, self.start, False)['state'], 'done')
        self.assertEqual(parse(text.splitlines()[0], self.start+6, self.start, False)['state'], 'stopped')

    def test_error_and_private_lines(self):
        text = '[00:58:00] app: /private/path\n[00:58:01] ✗ [3/7] rewrite (0:01)\n[RED] failure at /private/path'
        state = parse(text, self.start+2, self.start, False)
        self.assertEqual(state['state'], 'error')
        self.assertNotIn('/private/path', str(state))

    def test_midnight(self):
        start = datetime(2026, 11, 2, 23, 59, 50).timestamp()
        text = '[23:59:50] [1/7] rewrite …\n[00:00:10] [1/7] rewrite · compiling …'
        state = parse(text, start+25, start, True)
        self.assertEqual(state['elapsed'], 25)
        self.assertEqual(state['updated_age'], 5)

    def test_no_events_does_not_claim_completion(self):
        self.assertEqual(parse('', self.start+1, self.start, False)['state'], 'stopped')

    def test_dynamic_pipeline_stage(self):
        text = '[00:58:00] [7/8] Pipeline archive · compiling …\n[00:58:05] ✓ [7/8] Pipeline archive (0:05)\n[00:58:06] [8/8] Mac app · starting …\n[00:58:10] ✓ [8/8] Mac app (0:04)'
        state = parse(text, self.start+11, self.start, False)
        self.assertEqual(state['state'], 'done')
        self.assertEqual(state['stages'][0]['name'], 'Préparer les pipelines graphiques')
        self.assertEqual(state['total'], 8)

    def test_json_events_dynamic_count_and_eta(self):
        events = [
            {'ev': 'stage', 'k': 1, 'n': 7, 'name': 'rewrite', 't': self.start},
            {'ev': 'progress', 'k': 1, 'eta': 30, 't': self.start+2},
            {'ev': 'stage_end', 'k': 1, 'ok': True, 'elapsed': 4, 't': self.start+4},
            {'ev': 'stage', 'k': 2, 'n': 8, 'name': 'Mac host', 't': self.start+5},
        ]
        state = parse_json('\n'.join(json.dumps(e) for e in events), self.start+7, self.start, 'running')
        self.assertEqual((state['current'], state['total'], state['stage_eta']), (2, 8, None))
        self.assertEqual(state['stages'][0]['duration'], 4)

    def test_json_exit_status_is_authoritative(self):
        state = parse_json('{"ev":"say","msg":"[RED] warning"}\ninvalid', self.start+10, self.start, 'done', self.start+9)
        self.assertEqual(state['state'], 'done')
        self.assertEqual(state['elapsed'], 9)


if __name__ == '__main__':
    unittest.main()
