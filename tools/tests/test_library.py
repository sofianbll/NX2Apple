import json
import io
import os
from pathlib import Path
import subprocess
import struct
import sys
import tempfile
import time
import unittest
import zipfile
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import library as lib

TEMP = '/private/var/folders/0_/1mcnsfdn41z6sltt2pmtqcrc0000gn/T/opencode'
BASE = 'Test Game [0100000000010000][v0][Base].nsp'
UPDATE = 'Test Game [0100000000010800][v65536][UPD].nsp'


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=TEMP)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / '.build').mkdir()
        self.downloads = self.root / 'downloads'
        self.downloads.mkdir()

    def package(self, name=BASE, data=b'PFS0' + b'\0' * 260):
        path = self.downloads / name
        path.write_bytes(data)
        os.utime(path, (time.time()-120, time.time()-120))
        return path

    def test_base_update_and_dlc_family(self):
        self.assertEqual(lib.package_info(BASE)[:2], ('0100000000010000', 'base'))
        self.assertEqual(lib.package_info(UPDATE)[:2], ('0100000000010000', 'updates'))
        self.assertEqual(lib.package_info('DLC [0100000000011001].nsp')[:2], ('0100000000010000', 'dlc'))

    def test_partial_empty_and_recent_are_never_moved(self):
        for name in ('game.rar.part', 'game.crdownload', 'game.download'):
            path = self.package(name)
            self.assertIsNotNone(lib.import_one(self.root, path))
            self.assertTrue(path.exists())
        empty = self.package('Empty.rar', b'')
        self.assertIn('vide', lib.import_one(self.root, empty))
        recent = self.package()
        os.utime(recent, None)
        self.assertIn('récent', lib.import_one(self.root, recent))

    def test_open_writer_is_rejected(self):
        path = self.package()
        result = subprocess.CompletedProcess([], 0, 'p123\naw\n', '')
        with patch.object(lib.subprocess, 'run', return_value=result):
            self.assertIn('écriture', lib.wait_reason(path))

    def test_stalled_download_sidecar_is_rejected(self):
        path = self.package()
        path.with_name(path.name+'.aria2').write_text('download state')
        self.assertIn('Marqueur', lib.wait_reason(path))
        self.assertTrue(path.exists())

    def test_truncated_pfs_payload_is_rejected(self):
        path = self.package(data=b'PFS0'+struct.pack('<III',1,0,0)+struct.pack('<QQII',0,500,0,0))
        with self.assertRaisesRegex(ValueError, 'incomplet'):
            lib.validate_package(path)

    def test_external_import_never_moves_source(self):
        path = self.package()
        before = lib.signature(path)
        with patch.object(lib, 'wait_reason', return_value=None):
            self.assertIsNone(lib.import_one(self.root, path, preserve=True))
        self.assertEqual(lib.signature(path), before)
        self.assertEqual(len(lib.games(self.root)), 1)

    def test_inbox_import_also_preserves_original(self):
        inbox = self.root/'inbox'
        inbox.mkdir()
        source = inbox/BASE
        source.write_bytes(b'PFS0'+b'\0'*260)
        os.utime(source, (time.time()-120,time.time()-120))
        with patch.object(lib, 'wait_reason', return_value=None):
            lib.import_files(self.root,[inbox])
        self.assertTrue(source.is_file())
        self.assertEqual(len(lib.games(self.root)),1)
        with patch.object(lib,'import_one') as importer:
            lib.import_files(self.root,[inbox])
            importer.assert_not_called()

    def test_changed_packages_use_a_new_upstream_extraction_directory(self):
        game = lib.publish(self.root, self.package(), move=False)
        old = lib.build_work(self.root, game)
        old.mkdir(parents=True)
        (old/'preserved-extraction').write_text('old')
        (game['path']/'base'/BASE).write_bytes(b'PFS0different content')
        self.assertNotEqual(lib.build_work(self.root, game), old)
        self.assertTrue((old/'preserved-extraction').is_file())

    def test_symlink_is_not_followed(self):
        target = self.package()
        link = self.downloads / 'link.nsp'
        link.symlink_to(target)
        self.assertIn('symbolique', lib.wait_reason(link))

    def test_unrelated_download_archives_are_not_inspected(self):
        self.package('personal-documents.zip')
        self.package('ProdKeys.zip')
        with patch.object(lib, 'import_one') as importer:
            lib.import_files(self.root, [self.downloads])
            importer.assert_not_called()

    def test_direct_import_moves_only_completed_package(self):
        path = self.package()
        with patch.object(lib, 'wait_reason', return_value=None):
            self.assertIsNone(lib.import_one(self.root, path))
        game = lib.games(self.root)[0]
        self.assertFalse(path.exists())
        self.assertEqual((game['path'] / 'base' / BASE).read_bytes(), b'PFS0' + b'\0' * 260)

    def test_conflicting_destination_preserves_original(self):
        path = self.package()
        game = lib.publish(self.root, path, move=False)
        other = self.package(data=b'PFS0different')
        with self.assertRaises(ValueError):
            lib.publish(self.root, other)
        self.assertTrue(other.exists())
        self.assertNotEqual((game['path'] / 'base' / BASE).read_bytes(), other.read_bytes())

    def test_duplicate_original_is_retained_not_deleted(self):
        path = self.package()
        lib.publish(self.root, path, move=False)
        lib.publish(self.root, path)
        self.assertTrue((self.root / 'inbox/imported' / BASE).is_file())

    def test_archive_traversal_is_refused(self):
        output = f'Path = ../{BASE}\nSize = 264\nFolder = -\n'
        with patch.object(lib.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, output, '')):
            with self.assertRaises(ValueError):
                lib.archive_members(self.downloads / 'archive.rar')

    def test_archive_member_names_are_literal_and_all_languages_kept(self):
        names = [f'FireRed ({language}) [{tid}][v0].nsp' for language, tid in [('FR', '01004B3023412000'), ('EN', '0100554023408000'), ('DE', '01007F8023416000'), ('IT', '010092302342A000'), ('ES', '0100EB702342C000'), ('JA', '01006FA0233F8000')]]
        for name in names:
            lib.publish(self.root, self.package(name))
        self.assertEqual(len(lib.games(self.root)), 6)
        self.assertEqual(sum(len(lib.inputs(g)) for g in lib.games(self.root)), 6)

    def test_nested_editions_are_discovered_and_selected_without_ambiguity(self):
        for index, (folder, edition) in enumerate((('Français', 'fr'), ('Anglais', 'en'), ('Allemand', 'de'), ('Espagnol', 'es'), ('Italien', 'it'), ('Japonais', 'ja'))):
            path = self.root / 'games' / 'Pokémon FireRed' / folder
            lib.write_json(path / 'game.json', {'name': f'Pokemon FireRed {edition}', 'slug': f'pokemon-firered-{edition}', 'title_id': f'{index:016X}', 'group': 'Pokémon FireRed', 'edition': edition})
        found = lib.games(self.root)
        self.assertEqual(len(found), 6)
        for game in found:
            self.assertEqual(lib.choose_game(self.root, 'pokemon', game['edition'])['path'], game['path'])
            self.assertTrue((game['path'] / 'game.json').is_file())
        self.assertEqual(lib.choose_game(self.root, 'pokemon-firered-fr')['edition'], 'fr')
        with self.assertRaisesRegex(ValueError, 'ambigu'):
            lib.choose_game(self.root, 'pokemon')
        with self.assertRaisesRegex(ValueError, 'ambigu'):
            lib.choose_game(self.root, 'pokemon', 'pt')
        with self.assertRaisesRegex(ValueError, 'ambigu'):
            lib.choose_game(self.root, 'pokemon-firered-en', 'fr')
        lib.write_json(self.root / 'games/nested/invalid/game.json', {'name': 'evil', 'title_id': 'invalid', 'slug': 'evil'})
        with self.assertRaises(ValueError):
            lib.games(self.root)

    def test_snapshot_exposes_group_and_edition_without_manifest_private_fields(self):
        lib.write_json(self.root / 'games/FireRed/Français/game.json', {'name': 'Pokemon FireRed FR', 'slug': 'pokemon-fr', 'title_id': '0100000000010000', 'group': 'Pokémon FireRed', 'edition': 'fr', 'private': 'do-not-expose'})
        lib.write_json(self.root / 'games/Other/game.json', {'name': 'Other', 'slug': 'other', 'title_id': '0100000000020000'})
        with patch.object(lib, 'source_stamp', return_value='source'), patch.object(lib, 'profiles', return_value={}):
            rows = lib.snapshot(self.root)['games']
        other, edition = rows
        self.assertEqual((edition['group'], edition['edition']), ('Pokémon FireRed', 'fr'))
        self.assertEqual((other['group'], other['edition']), (None, None))
        self.assertNotIn('do-not-expose', json.dumps(rows))
        self.assertNotIn(str(self.root), json.dumps(rows))
        self.assertNotIn('path', edition)

    def test_corrupt_archive_never_moves_source(self):
        path = self.package('game.rar')
        with patch.object(lib, 'wait_reason', return_value=None), patch.object(lib, 'archive_members', return_value=[(BASE, BASE, 264)]), patch.object(lib.subprocess, 'run', side_effect=subprocess.CalledProcessError(2, '7zz')):
            with self.assertRaises(subprocess.CalledProcessError):
                lib.import_one(self.root, path)
        self.assertTrue(path.exists())
        self.assertFalse(lib.games(self.root))

    def test_real_archive_import_preserves_archive_and_nested_literal_names(self):
        archive = self.downloads / 'Test Game [NSP].zip'
        with zipfile.ZipFile(archive, 'w') as output:
            output.writestr('nested/' + BASE, b'PFS0' + b'\0' * 260)
            output.writestr('nested/' + UPDATE, b'PFS0' + b'\0' * 260)
        with patch.object(lib, 'wait_reason', return_value=None):
            self.assertIsNone(lib.import_one(self.root, archive))
        game = lib.games(self.root)[0]
        self.assertEqual(len(lib.inputs(game)), 2)
        self.assertFalse(archive.exists())
        self.assertTrue((self.root / 'inbox/imported' / archive.name).is_file())

    def test_changed_source_during_validation_never_moves_it(self):
        path = self.package()
        with patch.object(lib, 'wait_reason', return_value=None), patch.object(lib, 'validate_package', side_effect=lambda p: p.write_bytes(b'PFS0changed')):
            self.assertIn('modifié', lib.import_one(self.root, path))
        self.assertTrue(path.exists())

    def test_done_build_skips_without_keys_or_subprocess(self):
        game = lib.publish(self.root, self.package(), move=False)
        app = lib.app_path(self.root, game)
        app.mkdir(parents=True)
        stamp = lib.fingerprint(self.root, game, 'source')
        lib.write_json(self.root / '.build' / game['slug'] / 'state.json', {'state': 'done', 'fingerprint': stamp})
        with patch.object(lib, 'source_stamp', return_value='source'), patch.object(lib, 'profiles', return_value={game['title_id']: {'versions': {0}}}), patch.object(lib.subprocess, 'Popen') as child:
            lib.build(self.root, game)
            child.assert_not_called()
        (game['path'] / 'base' / BASE).write_bytes(b'PFS0new')
        self.assertNotEqual(lib.fingerprint(self.root, game, 'source'), stamp)
        self.assertNotEqual(lib.fingerprint(self.root, game, 'changed-source'), stamp)

    def test_existing_app_remains_available_after_failed_rebuild(self):
        game = lib.publish(self.root, self.package(), move=False)
        lib.app_path(self.root, game).mkdir(parents=True)
        lib.write_json(self.root / '.build' / game['slug'] / 'state.json', {'state': 'error'})
        self.assertEqual(lib.state_for(self.root, game, {'versions': {0}}, 'source')[0], 'available')

    def test_missing_xcode_does_not_touch_existing_app_or_start_build(self):
        game = lib.publish(self.root, self.package(), move=False)
        app = lib.app_path(self.root, game)
        app.mkdir(parents=True)
        (app / 'preserve.txt').write_text('keep')
        missing = subprocess.CompletedProcess([], 1, '', 'metal missing')
        with patch.object(lib, 'source_stamp', return_value='source'), patch.object(lib, 'profiles', return_value={game['title_id']: {'versions': {0}}}), patch.object(lib.subprocess, 'run', return_value=missing), patch.object(lib.subprocess, 'Popen') as child:
            with self.assertRaisesRegex(ValueError, 'Xcode'):
                lib.build(self.root, game)
            child.assert_not_called()
        self.assertEqual((app / 'preserve.txt').read_text(), 'keep')

    def test_run_existing_app_never_rebuilds(self):
        game = lib.publish(self.root, self.package(), move=False)
        app = lib.app_path(self.root, game)
        app.mkdir(parents=True)
        with patch.object(lib, 'ROOT', self.root), patch.object(sys, 'argv', ['library.py', 'run']), patch.dict(os.environ, {'GAME': 'test-game'}), patch.object(lib, 'build') as builder, patch.object(lib.subprocess, 'run') as launch:
            lib.main()
            builder.assert_not_called()
            launch.assert_called_once_with(['open', str(app)], check=True)

    def test_main_passes_edition_for_build_and_run(self):
        for edition in ('fr', 'en'):
            lib.write_json(self.root / 'games' / 'FireRed' / edition / 'game.json', {'name': f'Pokemon FireRed {edition}', 'slug': f'pokemon-{edition}', 'title_id': '0100000000010000', 'edition': edition})
        selected = lib.choose_game(self.root, 'pokemon', 'fr')
        for action in ('build', 'run'):
            with self.subTest(action=action), patch.object(lib, 'ROOT', self.root), patch.object(sys, 'argv', ['library.py', action]), patch.dict(os.environ, {'GAME': 'pokemon', 'EDITION': 'fr', 'EXPERIMENTAL': '0'}), patch.object(lib, 'build') as builder, patch.object(lib.subprocess, 'run'):
                lib.main()
                builder.assert_called_once_with(self.root, selected, allow_untested=False)

    def test_successful_managed_build_then_second_invocation_skips(self):
        game = lib.publish(self.root, self.package(), move=False)
        lib.app_path(self.root, game).mkdir(parents=True)
        (self.root / 'keys').mkdir()
        (self.root / 'keys/prod.keys').write_text('synthetic fixture, not a real key')
        process = MagicMock(pid=os.getpid())
        process.stdout = io.StringIO(json.dumps({'ev': 'stage', 'name': 'rewrite', 'k': 1, 'n': 1})+'\n')
        process.wait.return_value = 0
        ok = subprocess.CompletedProcess([], 0, '', '')
        with patch.object(lib, 'source_stamp', return_value='source'), patch.object(lib, 'profiles', return_value={game['title_id']: {'versions': {0}}}), patch.object(lib.subprocess, 'run', return_value=ok), patch.object(lib.subprocess, 'Popen', return_value=process) as child:
            lib.build(self.root, game)
            lib.build(self.root, game)
            self.assertEqual(child.call_count, 1)
        saved = lib.read_json(self.root / '.build' / game['slug'] / 'state.json')
        self.assertEqual(saved['state'], 'done')
        self.assertTrue(saved['fingerprint'])
        self.assertTrue((self.root / 'logs' / f'{game["slug"]}.jsonl').is_file())

    def test_retry_preserves_the_upstream_survey_directory(self):
        game = lib.publish(self.root, self.package(), move=False)
        lib.app_path(self.root, game).mkdir(parents=True)
        (self.root/'keys').mkdir()
        (self.root/'keys/prod.keys').write_text('synthetic fixture only')
        survey = self.root/'.build'/game['slug']/'input'/f'{game["title_id"]}_survey'
        survey.mkdir(parents=True)
        (survey/'survey.md').write_text('keep previous analysis')
        process = MagicMock(pid=os.getpid())
        process.stdout = io.StringIO('')
        process.wait.return_value = 0
        ok = subprocess.CompletedProcess([],0,'','')
        with patch.object(lib,'source_stamp',return_value='source'), patch.object(lib,'profiles',return_value={game['title_id']:{'versions':{0}}}), patch.object(lib.subprocess,'run',return_value=ok), patch.object(lib.subprocess,'Popen',return_value=process):
            lib.build(self.root,game)
        self.assertEqual((survey/'survey.md').read_text(),'keep previous analysis')

    def test_edition_language_matches_fingerprint_and_build_command(self):
        game = lib.publish(self.root, self.package(), move=False)
        default_stamp = lib.fingerprint(self.root, game, 'source')
        game['edition'] = 'fr'
        self.assertEqual(lib.fingerprint(self.root, game, 'source'), default_stamp)
        game['edition'] = 'ja'
        self.assertNotEqual(lib.fingerprint(self.root, game, 'source'), default_stamp)
        (self.root / 'keys').mkdir()
        (self.root / 'keys/prod.keys').write_text('synthetic fixture')
        process = MagicMock(pid=os.getpid(), stdout=io.StringIO(''))
        process.wait.return_value = 0
        ok = subprocess.CompletedProcess([], 0, '', '')
        with patch.object(lib, 'source_stamp', return_value='source'), patch.object(lib, 'profiles', return_value={game['title_id']: {'versions': {0}}}), patch.object(lib.subprocess, 'run', return_value=ok), patch.object(lib.subprocess, 'Popen', return_value=process) as child:
            lib.build(self.root, game)
        command = child.call_args.args[0]
        self.assertEqual(command[command.index('-l') + 1], 'ja')
        self.assertEqual(lib.read_json(self.root / '.build' / game['slug'] / 'state.json')['fingerprint'], lib.fingerprint(self.root, game, 'source'))

    def test_unsupported_and_missing_base_are_not_ready(self):
        game = lib.publish(self.root, self.package(), move=False)
        self.assertEqual(lib.state_for(self.root, game, None, 'source')[0], 'unsupported')
        for p in lib.inputs(game):
            p.unlink()
        self.assertEqual(lib.state_for(self.root, game, {'versions': {0}}, 'source')[0], 'missing')

    def test_untested_version_requires_explicit_opt_in(self):
        game = lib.publish(self.root, self.package(), move=False)
        with patch.object(lib, 'source_stamp', return_value='source'), patch.object(lib, 'profiles', return_value={game['title_id']: {'versions': {65536}}}), patch.object(lib.subprocess, 'Popen') as child:
            with self.assertRaisesRegex(ValueError, 'non testée'):
                lib.build(self.root, game)
            child.assert_not_called()
        with patch.object(lib, 'source_stamp', return_value='source'), patch.object(lib, 'profiles', return_value={}):
            with self.assertRaisesRegex(ValueError, 'Pas de profil'):
                lib.build(self.root, game)

    def test_unknown_profile_opt_in_builds_and_caches_experimental_result(self):
        game = lib.publish(self.root, self.package(), move=False)
        lib.app_path(self.root, game).mkdir(parents=True)
        (self.root / 'keys').mkdir()
        (self.root / 'keys/prod.keys').write_text('synthetic fixture')
        process = MagicMock(pid=os.getpid(), stdout=io.StringIO(''))
        process.wait.return_value = 0
        ok = subprocess.CompletedProcess([], 0, '', '')
        with patch.object(lib, 'source_stamp', return_value='source'), patch.object(lib, 'profiles', return_value={}), patch.object(lib.subprocess, 'run', return_value=ok), patch.object(lib.subprocess, 'Popen', return_value=process) as child:
            lib.build(self.root, game, allow_untested=True)
            self.assertEqual(lib.state_for(self.root, game, None, 'source')[0], 'experimental')
            lib.build(self.root, game)
            self.assertEqual(child.call_count, 1)
            command = child.call_args.args[0]
            for flag in ('--provisional', '--allow-damaged', '--allow-other-metal'):
                self.assertNotIn(flag, command)
        saved = lib.read_json(self.root / '.build' / game['slug'] / 'state.json')
        self.assertTrue(saved['experimental'])
        self.assertEqual(lib.state_for(self.root, game, {'versions': {0}}, 'source')[0], 'experimental')

    def test_all_never_builds_unknown_profile(self):
        lib.publish(self.root, self.package(), move=False)
        with patch.object(lib, 'ROOT', self.root), patch.object(sys, 'argv', ['library.py', 'all']), patch.object(lib, 'source_stamp', return_value='source'), patch.object(lib, 'profiles', return_value={}), patch.object(lib, 'build') as builder:
            lib.main()
            builder.assert_not_called()

    def test_sidecar_hiding_is_best_effort_after_success(self):
        game = lib.publish(self.root, self.package(), move=False)
        app = lib.app_path(self.root, game)
        app.mkdir(parents=True)
        sidecar = app.with_name(app.name + '.key')
        sidecar.write_text('fingerprint')
        (self.root / 'keys').mkdir()
        (self.root / 'keys/prod.keys').write_text('synthetic fixture')
        process = MagicMock(pid=os.getpid(), stdout=io.StringIO(''))
        process.wait.return_value = 0
        ok = subprocess.CompletedProcess([], 0, '', '')
        def run(command, **kwargs):
            if command[0] == 'chflags':
                raise OSError('unavailable')
            return ok
        with patch.object(lib, 'source_stamp', return_value='source'), patch.object(lib, 'profiles', return_value={game['title_id']: {'versions': {0}}}), patch.object(lib.subprocess, 'run', side_effect=run) as calls, patch.object(lib.subprocess, 'Popen', return_value=process):
            lib.build(self.root, game)
        self.assertTrue(any(call.args[0] == ['chflags', 'hidden', str(sidecar)] for call in calls.call_args_list))
        self.assertTrue(sidecar.is_file())
        self.assertEqual(lib.read_json(self.root / '.build' / game['slug'] / 'state.json')['state'], 'done')

    def test_experimental_result_stays_labelled_but_does_not_rebuild(self):
        game = lib.publish(self.root, self.package(), move=False)
        lib.app_path(self.root, game).mkdir(parents=True)
        stamp = lib.fingerprint(self.root, game, 'source')
        lib.write_json(self.root / '.build' / game['slug'] / 'state.json', {'state': 'done', 'fingerprint': stamp})
        profile = {'versions': {65536}}
        self.assertEqual(lib.state_for(self.root, game, profile, 'source')[0], 'experimental')
        with patch.object(lib, 'source_stamp', return_value='source'), patch.object(lib, 'profiles', return_value={game['title_id']: profile}), patch.object(lib.subprocess, 'Popen') as child:
            lib.build(self.root, game)
            child.assert_not_called()

    def test_manifest_cannot_escape_cache_root(self):
        lib.write_json(self.root / 'games/evil/game.json', {'name': 'evil', 'title_id': '0100000000010000', 'slug': '../keys'})
        with self.assertRaises(ValueError):
            lib.games(self.root)

    def test_pending_downloads_disappear_after_import_or_rename(self):
        source = self.package()
        missing = source.with_name('completed.rar.part')
        lib.write_json(self.root/'.build/import-status.json', {'pending': [{'name':source.name,'source':str(source),'reason':'was pending'},{'name':missing.name,'source':str(missing),'reason':'was partial'}]})
        lib.write_json(self.root/'.build/import-receipts.json', {str(source):list(lib.signature(source))})
        with patch.object(lib,'source_stamp',return_value='source'):
            self.assertEqual(lib.snapshot(self.root)['pending'], [])


if __name__ == '__main__':
    unittest.main()
