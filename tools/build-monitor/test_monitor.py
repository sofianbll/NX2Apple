from datetime import datetime
import unittest
from monitor import parse, parse_json, catalog
import json
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
import shutil
import subprocess
from threading import Thread
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

    @unittest.skipUnless(shutil.which('node'), 'Node is needed only for dashboard JavaScript tests')
    def test_dashboard_logic(self):
        subprocess.run(['node', '--test', str(Path(__file__).with_name('test_dashboard.cjs'))], check=True, capture_output=True, text=True)


    def test_catalog_route_serves_the_games_table(self):
        status, headers, body = self.request('/catalog')
        self.assertEqual(status, 200)
        self.assertIsInstance(json.loads(body)['games'], list)


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
