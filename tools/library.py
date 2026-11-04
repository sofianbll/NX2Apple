"""Small local library manager. No network downloads, key values, or save operations."""
import argparse
import contextlib
from decimal import Decimal, InvalidOperation
import filecmp
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import plistlib
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = {'.nsp', '.nsz', '.xci', '.xcz'}
ARCHIVES = {'.rar', '.zip', '.7z'}
PARTIAL = ('.part', '.crdownload', '.download', '.aria2', '.tmp')
TITLE = re.compile(r'\[([0-9a-fA-F]{16})\]')
RESERVE = 10 * 2**30
SLUG = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*')
ENV = re.compile(r'DM_[A-Z0-9_]+')
DECIMAL = re.compile(r'-?(?:\d+(?:\.\d*)?|\.\d+)')
MAX_LAUNCHER = 256 * 1024
MAX_INFO = 1024 * 1024
MAX_ENV = 64 * 1024


def read_json(path, default=None):
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        return default


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', dir=path.parent, delete=False) as f:
        tmp = Path(f.name)
        try:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write('\n')
            f.flush()
            os.fsync(f.fileno())
        except BaseException:
            tmp.unlink(missing_ok=True)
            raise
    tmp.replace(path)


def slug(name):
    text = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-') or 'game'


def package_info(name):
    match = TITLE.search(name)
    if not match:
        raise ValueError('Title ID absent du nom du paquet')
    tid = int(match[1], 16)
    low = tid & 0xFFF
    kind = 'base' if low == 0 else 'updates' if low == 0x800 else 'dlc'
    base = tid if kind == 'base' else tid & ~0xFFF if kind == 'updates' else (tid & ~0xFFF) - 0x1000
    title = PurePosixPath(name).name.split('[')[0].strip(' ._-')
    version = re.search(r'\[v(\d+)\]', name, re.I)
    return f'{base:016X}', kind, title, int(version[1]) if version else None


def profiles(root):
    result = {}
    for path in (root / 'source/dm/games').glob('*/game.tsv'):
        rows = [line.split('\t') for line in path.read_text().splitlines() if line and not line.startswith('#')]
        fields = {r[0]: r[1] for r in rows if len(r) > 1}
        result[path.parent.name.upper()] = {'name': fields.get('name', path.parent.name), 'versions': {int(r[1][1:]) for r in rows if len(r) > 1 and r[0] == 'build' and r[1].startswith('v')}}
    return result


def games(root):
    result = []
    for path in (root / 'games').rglob('game.json'):
        game = read_json(path)
        if not SLUG.fullmatch(game['slug']) or not re.fullmatch(r'[0-9A-F]{16}', game['title_id']):
            raise ValueError('Identifiant de jeu invalide dans game.json')
        game['path'] = path.parent
        result.append(game)
    return sorted(result, key=lambda g: g['name'].casefold())


def game_for(root, name, title_id):
    for game in games(root):
        if game['title_id'] == title_id:
            return game
    name = profiles(root).get(title_id, {}).get('name', name) or title_id
    name = re.sub(r'[/\\\x00-\x1f]', '-', name).strip(' .') or title_id
    path = root / 'games' / name
    if path.exists():
        path = path.with_name(f'{name} [{title_id}]')
    game = {'name': name, 'slug': f'{slug(name)}-{title_id.lower()}', 'title_id': title_id}
    write_json(path / 'game.json', game)
    return dict(game, path=path)


def signature(path):
    s = path.stat()
    return s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns


def wait_reason(path, now=None):
    if path.is_symlink():
        return 'Lien symbolique laissé en place'
    if path.name.lower().endswith(PARTIAL):
        return 'Téléchargement partiel — laissé en place'
    if any(path.with_name(path.name + suffix).exists() for suffix in PARTIAL):
        return 'Marqueur de téléchargement associé — laissé en place'
    if not path.is_file():
        return 'Dossier de téléchargement — laissé en place'
    st = path.stat()
    if not st.st_size:
        return 'Fichier vide — laissé en place'
    if (now if now is not None else time.time()) - st.st_mtime < 60:
        return 'Fichier récent — attendre au moins une minute'
    # A stalled download can have an old mtime; also reject open write handles.
    p = subprocess.run(['/usr/sbin/lsof', '-F', 'a', '--', str(path)], capture_output=True, text=True, timeout=15)
    if p.returncode not in (0, 1) or p.stderr.strip():
        return 'Impossible de vérifier les écritures en cours'
    if any(line in ('aw', 'au') for line in p.stdout.splitlines()):
        return 'Fichier ouvert en écriture — laissé en place'
    return None


def archive_members(path):
    p = subprocess.run(['7zz', 'l', '-slt', '-ba', '-sccUTF-8', '-p-', '--', str(path)], capture_output=True, text=True, timeout=60, check=True)
    members = []
    seen = set()
    for block in p.stdout.strip().split('\n\n'):
        fields = dict(line.split(' = ', 1) for line in block.splitlines() if ' = ' in line)
        name = fields.get('Path', '')
        if PurePosixPath(name).suffix.lower() not in PACKAGES:
            continue
        member = PurePosixPath(name.replace('\\', '/'))
        if member.is_absolute() or '..' in member.parts or '\x00' in name or name in seen:
            raise ValueError('Chemin de paquet dangereux ou dupliqué dans l’archive')
        if any(fields.get(k) for k in ('Symbolic Link', 'Hard Link', 'Copy Link')) or fields.get('Encrypted') == '+':
            raise ValueError('Paquet lié ou chiffré dans l’archive : import refusé')
        package_info(member.name)
        size = int(fields['Size'])
        if size <= 0:
            raise ValueError('Paquet vide dans l’archive')
        members.append((name, member.name, size))
        seen.add(name)
    return members


def validate_package(path):
    with path.open('rb') as f:
        header = f.read(0x104)
        if header[:4] == b'PFS0':
            if len(header) < 16:
                raise ValueError('En-tête de paquet tronqué')
            count, strings = struct.unpack_from('<II', header, 4)
            data_start = 16 + count * 24 + strings
            if count > 100000 or data_start > path.stat().st_size:
                raise ValueError('Table du paquet tronquée ou démesurée')
            f.seek(16)
            for _ in range(count):
                entry = f.read(24)
                offset, size = struct.unpack_from('<QQ', entry)
                if data_start + offset + size > path.stat().st_size:
                    raise ValueError('Paquet incomplet : données encore manquantes')
    if header[:4] != b'PFS0' and header[0x100:] != b'HEAD':
        raise ValueError(f'En-tête de paquet invalide : {path.name}')


def keep_original(root, source):
    folder = root / 'inbox/imported'
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / source.name
    i = 2
    while target.exists():
        target = folder / f'{source.stem} ({i}){source.suffix}'
        i += 1
    shutil.move(str(source), target)


def publish(root, source, move=True, original=True):
    title_id, kind, name, _ = package_info(source.name)
    game = game_for(root, name, title_id)
    dest = game['path'] / kind / source.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        if not filecmp.cmp(source, dest, shallow=False):
            raise ValueError(f'Un autre fichier porte déjà ce nom : {source.name}')
        if move:
            if original:
                keep_original(root, source)
            else:
                source.unlink()  # Only our redundant, temporary extraction is removed.
    elif move:
        shutil.move(str(source), dest)
    else:
        # Clones keep the existing build staging files usable without duplicating blocks.
        subprocess.run(['cp', '-c', str(source), str(dest)], check=True)
    return game


def import_one(root, source, preserve=False):
    reason = wait_reason(source)
    if reason:
        return reason
    before = signature(source)
    if preserve:
        if shutil.disk_usage(root).free < source.stat().st_size + RESERVE:
            return 'Place insuffisante pour une copie de sécurité'
        with tempfile.TemporaryDirectory(prefix='snapshot-', dir=root / '.build') as tmp:
            snapshot = Path(tmp) / source.name
            subprocess.run(['cp', '-pc', str(source), str(snapshot)], check=True)
            if signature(source) != before or wait_reason(source):
                return 'Téléchargement repris — original laissé en place'
            # Only our immutable APFS snapshot is moved; the downloader's inode is never renamed.
            return import_one(root, snapshot)
    if source.suffix.lower() in PACKAGES:
        validate_package(source)
        if signature(source) != before or wait_reason(source):
            return 'Fichier modifié pendant la vérification — laissé en place'
        publish(root, source)
        return None
    members = archive_members(source)
    if not members:
        return 'Aucun paquet de jeu identifiable — laissé en place'
    if shutil.disk_usage(root).free < sum(m[2] for m in members) + RESERVE:
        return 'Place insuffisante en conservant 10 Gio libres'
    with tempfile.TemporaryDirectory(prefix='import-', dir=root / '.build') as tmp:
        staged = []
        subprocess.run(['7zz', 't', '-bd', '-p-', '--', str(source)], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=600, check=True)
        for index, (member, name, size) in enumerate(members):
            dest = Path(tmp) / str(index) / name
            dest.parent.mkdir()
            with dest.open('xb') as output:
                subprocess.run(['7zz', 'x', '-so', '-spd', '-p-', '--', str(source), member], stdout=output, stderr=subprocess.PIPE, timeout=600, check=True)
            if dest.stat().st_size != size:
                raise ValueError('Extraction incomplète')
            validate_package(dest)
            staged.append(dest)
        if signature(source) != before or wait_reason(source):
            return 'Archive modifiée pendant la vérification — laissée en place'
        for dest in staged:
            publish(root, dest, original=False)
        keep_original(root, source)
    return None


def import_files(root, folders):
    pending = []
    receipt_file = root / '.build/import-receipts.json'
    receipts = read_json(receipt_file, {})
    for folder in dict.fromkeys(p.expanduser().resolve() for p in folders):
        if not folder.is_dir():
            raise ValueError(f'Dossier introuvable : {folder}')
        for source in sorted(folder.iterdir()):
            if source.suffix.lower() not in PACKAGES | ARCHIVES and not source.name.lower().endswith(PARTIAL):
                continue
            # Downloads also holds unrelated documents and secrets: inspect only game-labelled files.
            if folder != (root / 'inbox').resolve() and source.suffix.lower() not in PACKAGES and not (TITLE.search(source.name) or re.search(r'\b(nsp|nsz|xci|xcz|switch|upd|dlc)\b', source.name.replace('_', ' '), re.I)):
                continue
            try:
                stamp = list(signature(source))
                if receipts.get(str(source)) == stamp:
                    print(f'DÉJÀ IMPORTÉ  {source.name} — original conservé', flush=True)
                    continue
                preserve = True  # A downloader may also target inbox; never rename its original inode.
                reason = import_one(root, source, preserve=preserve)
                if not reason and preserve and source.exists() and list(signature(source)) == stamp:
                    receipts[str(source)] = stamp
                    write_json(receipt_file, receipts)
            except (ValueError, OSError, subprocess.SubprocessError) as error:
                reason = f'Import interrompu, original conservé ({type(error).__name__})'
            if reason:
                pending.append({'name': source.name, 'source': str(source), 'reason': reason})
                print(f'EN ATTENTE  {source.name} : {reason}', flush=True)
            else:
                print(f'IMPORTÉ     {source.name}', flush=True)
    write_json(root / '.build/import-status.json', {'checked_at': time.time(), 'pending': pending})


def inputs(game):
    return sorted(p for kind in ('base', 'updates', 'dlc') for p in (game['path'] / kind).glob('*') if p.is_file() and p.suffix.lower() in PACKAGES)


def input_stamp(game):
    # shortcut: like Make, size/mtime changes invalidate inputs; clean before rebuilding files restored with identical timestamps.
    return [(str(p.relative_to(game['path'])), p.stat().st_size, p.stat().st_mtime_ns) for p in inputs(game)]


def source_stamp(root):
    def git(*args):
        return subprocess.run(['git', *args], cwd=root / 'source', capture_output=True, check=True).stdout
    data = git('rev-parse', 'HEAD') + git('diff', '--binary', 'HEAD')
    for name in git('ls-files', '--others', '--exclude-standard', '-z').split(b'\0'):
        if name:
            path = root / 'source' / os.fsdecode(name)
            if path.is_file():
                data += name + hashlib.sha256(path.read_bytes()).digest()
    return hashlib.sha256(data).hexdigest()


def fingerprint(root, game, source=None):
    return hashlib.sha256(json.dumps({'inputs': input_stamp(game), 'source': source if source is not None else source_stamp(root), 'platform': 'mac-app', 'language': game.get('edition', 'fr')}, sort_keys=True).encode()).hexdigest()


def build_work(root, game):
    generation = hashlib.sha256(json.dumps(input_stamp(game)).encode()).hexdigest()[:16]
    return root / '.build' / game['slug'] / 'work' / generation


def app_path(root, game):
    return root / 'apps' / f'{game["name"]}.app'


def state_for(root, game, profile, source):
    files = inputs(game)
    base = any(p.parent.name == 'base' for p in files)
    versions = [package_info(p.name)[3] for p in files if p.parent.name == 'updates']
    version = max((v for v in versions if v is not None), default=0)
    saved = read_json(root / '.build' / game['slug'] / 'state.json', {})
    current = bool(app_path(root, game).is_dir() and saved.get('fingerprint') == fingerprint(root, game, source) and saved.get('state') == 'done')
    if not base:
        return 'missing', 'Jeu de base manquant'
    if current:
        if saved.get('experimental') or not profile or version not in profile['versions']:
            return 'experimental', 'Application construite — version non validée par le profil'
        return 'done', 'Application à jour'
    if not profile:
        return 'unsupported', 'Pas de profil nxnative — non construit automatiquement'
    if version not in profile['versions']:
        return 'untested', f'Version v{version} non testée dans le profil'
    if saved.get('state') == 'error':
        if app_path(root, game).is_dir():
            return 'available', 'Application existante disponible ; reconstruction à vérifier'
        return 'error', 'Dernière construction en échec'
    if app_path(root, game).is_dir():
        return 'available', 'Application existante disponible ; make build vérifie les changements'
    return 'ready', 'À construire / vérifier'


def choose_game(root, query, edition=None):
    if not query:
        raise ValueError('Préciser GAME=… ; make list affiche les identifiants')
    candidates = [g for g in games(root) if not edition or g.get('edition', '').casefold() == edition.casefold()]
    found = [g for g in candidates if query.casefold() in (g['slug'].casefold(), g['title_id'].casefold(), g['name'].casefold())]
    if not found:
        found = [g for g in candidates if slug(query) in g['slug']]
    if len(found) != 1:
        raise ValueError('Jeu absent ou nom ambigu ; utiliser l’identifiant de make list')
    return found[0]


def build(root, game, allow_untested=False):
    source = source_stamp(root)
    state, reason = state_for(root, game, profiles(root).get(game['title_id']), source)
    if state in ('done', 'experimental'):
        print(f'À JOUR  {game["name"]} — aucune reconstruction', flush=True)
        return
    if state == 'missing' or (state in ('unsupported', 'untested') and not allow_untested):
        raise ValueError(f'{game["name"]} : {reason}')
    if state in ('unsupported', 'untested'):
        print(f'ESSAI EXPLICITE  {reason} — profil officiel provisoire ou dérivé, sans contourner les contrôles', flush=True)
    toolchain = subprocess.run(['bash', '-c', 'source "$1/env.sh"\nxcrun --sdk macosx metal --version', 'nxnative', str(root)], capture_output=True, text=True)
    if toolchain.returncode:
        raise ValueError('Xcode avec Metal est indisponible. Une app existante reste jouable avec make run ; aucune réinstallation automatique')
    key = root / 'keys/prod.keys'
    if not key.is_file():
        raise ValueError('keys/prod.keys est absent ; ne pas coller sa valeur dans le chat')
    running = subprocess.run(['ps', '-axo', 'comm='], capture_output=True, text=True, check=True).stdout
    if str(app_path(root, game)) in running:
        raise ValueError(f'Sauvegarder puis quitter {game["name"]} avant de remplacer son application')
    if shutil.disk_usage(root).free < 2 * sum(p.stat().st_size for p in inputs(game)) + RESERVE:
        raise ValueError('Place libre insuffisante pour une construction prudente')
    work = root / '.build' / game['slug']
    staging = work / 'input'
    staging.mkdir(parents=True, exist_ok=True)
    for old in staging.iterdir():
        if old.is_symlink():
            old.unlink()
        elif old.is_dir() and old.name == f'{game["title_id"]}_survey':
            continue  # Upstream keeps its unknown-game survey here between attempts.
        else:
            raise ValueError('Le staging contient un fichier non géré ; ne rien écraser')
    for p in inputs(game):
        (staging / p.name).symlink_to(p.resolve())
    stamp = fingerprint(root, game, source)
    log = root / 'logs' / f'{game["slug"]}.jsonl'
    log.parent.mkdir(exist_ok=True)
    state_file = work / 'state.json'
    record = {'game': game['name'], 'slug': game['slug'], 'started': time.time(), 'state': 'running', 'experimental': state in ('unsupported', 'untested'), 'log': str(log.relative_to(root))}
    command = ['bash', '-c', 'source "$1/env.sh"\nshift\nexec "$@"', 'nxnative', str(root), str(root / '.venv/bin/python'), str(root / 'source/scripts/build_ipa_from_nsp.py'), str(staging), '-k', str(key), '--platform', 'mac-app', '--work-dir', str(build_work(root, game)), '-o', str(app_path(root, game)), '-l', game.get('edition', 'fr'), '--progress', 'json']
    with log.open('w') as output, log.with_suffix('.stderr.log').open('w') as errors:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=errors, text=True)
        record['pid'] = process.pid
        write_json(state_file, record)
        write_json(root / '.build/active.json', record)
        try:
            for line in process.stdout:
                output.write(line)
                output.flush()
                try:
                    event = json.loads(line)
                    if event.get('ev') in ('stage', 'stage_end'):
                        print(f'{game["name"]} : {event.get("name", "")} {"✓" if event.get("ev") == "stage_end" and event.get("ok") else ""}', flush=True)
                except json.JSONDecodeError:
                    pass
            code = process.wait()
            if code == 0:
                subprocess.run(['codesign', '--verify', '--deep', '--strict', str(app_path(root, game))], check=True)
                sidecar = app_path(root, game).with_name(app_path(root, game).name + '.key')
                if sidecar.is_file():
                    try:
                        subprocess.run(['chflags', 'hidden', str(sidecar)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    except OSError:
                        pass
            record.update(state='done' if code == 0 else 'error', finished=time.time(), fingerprint=stamp if code == 0 else None, returncode=code)
        except BaseException:
            process.terminate()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            record.update(state='error', finished=time.time())
            raise
        finally:
            process.stdout.close()
            write_json(state_file, record)
            write_json(root / '.build/active.json', record)
    if record['state'] != 'done':
        raise ValueError(f'Construction arrêtée : consulter logs/{game["slug"]}.jsonl et .stderr.log')


def process_table():
    """Return (pid, ppid, executable) once, or None when process state is unavailable."""
    try:
        result = subprocess.run(['/bin/ps', '-axo', 'pid=,ppid=,comm='], capture_output=True, text=True, timeout=5, check=True)
        rows = []
        for line in result.stdout.splitlines():
            fields = line.strip().split(None, 2)
            if len(fields) == 3:
                rows.append((int(fields[0]), int(fields[1]), fields[2]))
        return rows
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def runtime_for(root, game, processes):
    if processes is None:
        return {'state': 'unknown'}
    macos = app_path(root, game) / 'Contents/MacOS'
    launchers = {pid for pid, _, command in processes if command == str(macos / 'nxnative')}
    if any(command == str(macos / 'dmhost') for _, _, command in processes):
        return {'state': 'running'}
    return {'state': 'launcher'} if launchers else {'state': 'stopped'}


def runtime_state(root, game):
    return runtime_for(root, game, process_table())


def snapshot(root):
    profile = profiles(root)
    source = source_stamp(root)
    processes = process_table()
    rows = []
    for game in games(root):
        state, reason = state_for(root, game, profile.get(game['title_id']), source)
        rows.append({'name': game['name'], 'slug': game['slug'], 'title_id': game['title_id'], 'group': game.get('group'), 'edition': game.get('edition'), 'state': state, 'reason': reason, 'runtime': runtime_for(root, game, processes), 'app': app_path(root, game).is_dir(), 'files': {kind: len(list((game['path'] / kind).glob('*'))) for kind in ('base', 'updates', 'dlc')}})
    pending = []
    receipts = read_json(root / '.build/import-receipts.json', {})
    for item in read_json(root / '.build/import-status.json', {}).get('pending', []):
        path = Path(item['source'])
        if not path.exists() or (path.is_file() and receipts.get(str(path)) == list(signature(path))):
            continue
        pending.append({'name': item['name'], 'reason': item['reason'], 'bytes': path.stat().st_size if path.is_file() else None})
    active = read_json(root / '.build/active.json')
    if active:
        path = root / active['log']
        active = dict(active, events=path.read_text(errors='replace')[-2*1024*1024:] if path.is_file() else '')
    return {'games': rows, 'pending': pending, 'active': active, 'free_bytes': shutil.disk_usage(root).free, 'checked_at': time.time()}


@contextlib.contextmanager
def operation(root):
    (root / '.build').mkdir(exist_ok=True)
    with (root / '.build/operation.lock').open('a') as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('Un import, nettoyage ou build est déjà en cours') from None
        yield


class PlayError(ValueError):
    """Business error whose message is safe to show; status is the HTTP code used by the dashboard."""
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


def known_game(root, name):
    if not isinstance(name, str) or not SLUG.fullmatch(name):
        raise PlayError(400, 'Identifiant de jeu invalide')
    game = next((g for g in games(root) if g['slug'] == name), None)
    if not game:
        raise PlayError(400, 'Jeu inconnu')
    return game


def checked_app(root, game):
    app = app_path(root, game)
    try:
        valid = not app.is_symlink() and app.is_dir() and app.resolve().parent == (root / 'apps').resolve()
    except OSError:
        valid = False
    if not valid:
        raise PlayError(409, 'Application absente ou invalide')
    return app


def bundle_file(app, relative, limit, required=False):
    """Read one allowlisted regular file without following a symlink out of the app."""
    path = app
    try:
        for part in PurePosixPath(relative).parts:
            path = path / part
            if path.is_symlink():
                raise PlayError(409, 'Bundle d’application invalide')
        if not path.resolve().is_relative_to(app.resolve()) or not path.is_file():
            raise FileNotFoundError
        if path.stat().st_size > limit:
            raise PlayError(409, 'Métadonnées d’application trop volumineuses')
        data = path.read_bytes()
    except FileNotFoundError:
        if required:
            raise PlayError(409, 'Métadonnées d’application absentes') from None
        return None
    except PlayError:
        raise
    except OSError:
        raise PlayError(409, 'Métadonnées d’application illisibles') from None
    if len(data) > limit:
        raise PlayError(409, 'Métadonnées d’application trop volumineuses')
    return data


def decimal_value(value, string=False):
    if isinstance(value, bool) or (string and not isinstance(value, str)) or (not string and not isinstance(value, (int, float))):
        raise ValueError
    if isinstance(value, str) and not DECIMAL.fullmatch(value):
        raise ValueError
    try:
        result = Decimal(str(value))
    except InvalidOperation:
        raise ValueError from None
    if not result.is_finite():
        raise ValueError
    return result


def valid_setting_value(setting, value):
    if not isinstance(value, str):
        return False
    if setting['kind'] == 'choice':
        return value in {option[0] for option in setting['options']}
    if setting['kind'] == 'toggle':
        return value in (setting['on'], setting['off'])
    try:
        number = decimal_value(value, string=True)
        low = decimal_value(setting['min'])
        high = decimal_value(setting['max'])
        step = decimal_value(setting['step'])
        return low <= number <= high and (number - low) % step == 0
    except (ValueError, InvalidOperation):
        return False


def launcher_definitions(data, title_id):
    """Validate schema 1 and copy only fields understood by this frontend."""
    schema = data.get('schema', 1) if isinstance(data, dict) else None
    if not isinstance(data, dict) or isinstance(schema, bool) or not isinstance(schema, int) or schema != 1 or data.get('game') != title_id or not isinstance(data.get('settings'), list):
        raise ValueError
    result = []
    seen = set()
    for source in data['settings']:
        if not isinstance(source, dict):
            raise ValueError
        setting = {}
        for key in ('env', 'kind', 'section', 'label', 'note', 'default'):
            if not isinstance(source.get(key), str):
                raise ValueError
            setting[key] = source[key]
        if not ENV.fullmatch(setting['env']) or setting['env'] in seen or setting['kind'] not in ('choice', 'range', 'toggle'):
            raise ValueError
        seen.add(setting['env'])
        if setting['kind'] == 'choice':
            options = source.get('options')
            if not isinstance(options, list) or not options:
                raise ValueError
            setting['options'] = []
            for option in options:
                if not isinstance(option, list) or len(option) != 2 or not all(isinstance(item, str) for item in option):
                    raise ValueError
                setting['options'].append(option.copy())
            if len({option[0] for option in setting['options']}) != len(setting['options']):
                raise ValueError
        elif setting['kind'] == 'range':
            for key in ('min', 'max', 'step'):
                setting[key] = source.get(key)
                decimal_value(setting[key])
            if decimal_value(setting['min']) > decimal_value(setting['max']) or decimal_value(setting['step']) <= 0:
                raise ValueError
        else:
            for key in ('on', 'off'):
                if not isinstance(source.get(key), str):
                    raise ValueError
                setting[key] = source[key]
            if setting['on'] == setting['off']:
                raise ValueError
        if not valid_setting_value(setting, setting['default']):
            raise ValueError
        if 'base' in source:
            base = source['base']
            if not isinstance(base, dict) or set(('docked', 'handheld')) - set(base):
                raise ValueError
            setting['base'] = {}
            for key in ('docked', 'handheld'):
                size = base[key]
                if not isinstance(size, list) or len(size) != 2 or any(isinstance(item, bool) or not isinstance(item, int) for item in size):
                    raise ValueError
                setting['base'][key] = size.copy()
        if 'level' in source:
            if source['level'] != 'basic':
                raise ValueError
            setting['level'] = 'basic'
        if 'needs' in source:
            if not isinstance(source['needs'], str) or not re.fullmatch(r'DM_[A-Z0-9_]+=[^;=]+', source['needs']):
                raise ValueError
            setting['needs'] = source['needs']
        result.append(setting)
    return result


def check_native_rules(settings, rules):
    if not isinstance(rules, list):
        raise ValueError
    indexed = {}
    for rule in rules:
        if not isinstance(rule, dict) or not isinstance(rule.get('env'), str) or rule['env'] in indexed:
            raise ValueError
        indexed[rule['env']] = rule
    for setting in settings:
        rule = indexed.get(setting['env'])
        if rule is None:
            raise ValueError
        if setting['kind'] == 'range':
            if decimal_value(rule.get('min')) != decimal_value(setting['min']) or decimal_value(rule.get('max')) != decimal_value(setting['max']):
                raise ValueError
        elif rule.get('values') != ([option[0] for option in setting['options']] if setting['kind'] == 'choice' else [setting['on'], setting['off']]):
            raise ValueError


def settings_bundle(root, game):
    app = checked_app(root, game)
    try:
        info = plistlib.loads(bundle_file(app, 'Contents/Info.plist', MAX_INFO, required=True))
    except (ValueError, plistlib.InvalidFileException):
        raise PlayError(409, 'Informations d’application invalides') from None
    domain = f'org.nxnative.{game["title_id"].lower()}'
    if not isinstance(info, dict) or info.get('DMTitleID') != game['title_id'] or info.get('CFBundleIdentifier') != domain:
        raise PlayError(409, 'Identité d’application invalide')
    raw = bundle_file(app, 'Contents/Resources/dm/launcher.json', MAX_LAUNCHER)
    if raw is None:
        return app, domain, []
    try:
        settings = launcher_definitions(json.loads(raw), game['title_id'])
        check_native_rules(settings, info.get('DMSettings'))
    except (ValueError, TypeError, InvalidOperation, json.JSONDecodeError):
        raise PlayError(409, 'Schéma de réglages invalide') from None
    return app, domain, settings


def env_file(path, wanted):
    try:
        if path.is_symlink():
            raise PlayError(409, 'Fichier env.txt invalide')
        if not path.is_file():
            return {}
        if path.stat().st_size > MAX_ENV:
            raise PlayError(409, 'Fichier env.txt trop volumineux')
        text = path.read_text()
    except PlayError:
        raise
    except FileNotFoundError:
        return {}
    except (OSError, UnicodeError):
        raise PlayError(409, 'Fichier env.txt illisible') from None
    found = {}
    for line in text.splitlines():
        line = line.strip(' \t\r\n')
        key, separator, value = line.partition('=')
        key = key.rstrip(' \t')
        if separator and not line.startswith('#') and key in wanted and key not in found:
            found[key] = value
    return found


def defaults(*arguments):
    return subprocess.run(['/usr/bin/defaults', *arguments], capture_output=True, text=True, timeout=10)


def saved_value(domain, setting):
    try:
        result = defaults('read', domain, f'launcher.{setting["env"]}')
    except (OSError, subprocess.SubprocessError):
        raise PlayError(502, 'Lecture des réglages impossible ou trop longue') from None
    if result.returncode == 1:
        return setting['default']
    if result.returncode:
        raise PlayError(502, 'Lecture des réglages impossible')
    value = result.stdout.removesuffix('\n')
    if not valid_setting_value(setting, value):
        return setting['default']
    try:
        value_type = defaults('read-type', domain, f'launcher.{setting["env"]}')
    except (OSError, subprocess.SubprocessError):
        raise PlayError(502, 'Lecture des réglages impossible ou trop longue') from None
    if value_type.returncode not in (0, 1):
        raise PlayError(502, 'Lecture des réglages impossible')
    if value_type.returncode or value_type.stdout.strip() != 'Type is string':
        return setting['default']
    return value


def settings_response(root, game, processes=None):
    app, domain, settings = settings_bundle(root, game)
    wanted = {setting['env'] for setting in settings} | {'DM_SAVED_CHOICES'}
    overrides = {key: (os.environ[key], 'environnement de lancement') for key in wanted if key in os.environ}
    for path, origin in ((Path.home() / 'Library/Application Support/nxnative' / game['title_id'] / 'env.txt', 'env.txt utilisateur'), (app / 'Contents/Resources/dm/env.txt', 'env.txt du bundle')):
        for key, value in env_file(path, wanted).items():
            overrides.setdefault(key, (value, origin))
    disabled = overrides.get('DM_SAVED_CHOICES', (None,))[0] == '0'
    rows = []
    for setting in settings:
        row = dict(setting, value=saved_value(domain, setting), locked=disabled or setting['env'] in overrides)
        if disabled:
            row['lock_reason'] = 'DM_SAVED_CHOICES=0 : les choix enregistrés sont ignorés'
        elif setting['env'] in overrides:
            row['lock_reason'] = f'Variable imposée par {overrides[setting["env"]][1]} ; le choix enregistré n’est pas effectif'
        rows.append(row)
    return {'slug': game['slug'], 'settings': rows, 'runtime': runtime_for(root, game, process_table() if processes is None else processes)}


def dashboard_settings(root, name):
    return settings_response(root, known_game(root, name))


def dashboard_save_settings(root, name, values):
    game = known_game(root, name)
    if not isinstance(values, dict):
        raise PlayError(400, 'Valeurs de réglages invalides')
    try:
        with operation(root):
            response = settings_response(root, game)
            if response['runtime']['state'] != 'stopped':
                raise PlayError(409, 'Quitter le jeu et son launcher avant de modifier les réglages ; état inconnu = refus')
            offered = {setting['env']: setting for setting in response['settings']}
            if any(not isinstance(key, str) or key not in offered or not valid_setting_value(offered[key], value) for key, value in values.items()):
                raise PlayError(400, 'Valeur absente des choix offerts ou invalide')
            locked = [key for key in values if offered[key]['locked']]
            if locked:
                raise PlayError(409, 'Un réglage verrouillé par l’environnement ne peut pas être modifié')
            domain = f'org.nxnative.{game["title_id"].lower()}'
            commands = [('delete', domain, f'launcher.{key}') if value == offered[key]['default'] else ('write', domain, f'launcher.{key}', '-string', value) for key, value in values.items()]
            for index, command in enumerate(commands):
                try:
                    result = defaults(*command)
                    failed = result.returncode and not (command[0] == 'delete' and result.returncode == 1)
                except (OSError, subprocess.SubprocessError):
                    failed = True
                if failed:
                    message = 'Écriture partielle : certains réglages ont changé, rechargez les valeurs' if index else 'Enregistrement des réglages impossible ou trop long'
                    raise PlayError(502, message)
    except PlayError:
        raise
    except ValueError:
        raise PlayError(409, 'Un import, nettoyage ou build est déjà en cours') from None


def open_existing(root, game, show_launcher=True, **options):
    """Open an already built app, never build. The app must be a real directory directly under apps/."""
    app = checked_app(root, game)
    command = ['open', str(app)] if show_launcher else ['open', str(app), '--args', '--no-launcher']
    subprocess.run(command, check=True, **options)


def dashboard_play(root, name, show_launcher=True, timeout=10):
    game = known_game(root, name)
    if not isinstance(show_launcher, bool):
        raise PlayError(400, 'Option du launcher invalide')
    try:
        # The lock is held while opening so a build or import cannot replace the app meanwhile.
        with operation(root):
            if runtime_state(root, game)['state'] != 'stopped':
                raise PlayError(409, 'Jeu déjà ouvert ou état du processus inconnu')
            open_existing(root, game, show_launcher=show_launcher, timeout=timeout, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except PlayError:
        raise
    except ValueError:
        raise PlayError(409, 'Un import, nettoyage ou build est déjà en cours') from None
    except (OSError, subprocess.SubprocessError):
        # No automatic retry: a second open could start a second instance.
        raise PlayError(502, 'Lancement impossible ou trop long') from None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['import', 'list', 'build', 'all', 'run', 'monitor', 'clean'])
    parser.add_argument('--stop-on-stdin-eof', action='store_true')
    args = parser.parse_args()
    action = args.action
    if action == 'monitor':
        sys.path.insert(0, str(ROOT / 'tools/build-monitor'))
        from monitor import serve, parse_json
        def status():
            data = snapshot(ROOT)
            active = data['active']
            if active:
                from monitor import alive
                state = active['state']
                if state == 'running' and not alive(active['pid']):
                    state = 'stopped'
                parsed = parse_json(active.pop('events'), time.time(), active['started'], state, active.get('finished'))
                data['active'] = dict(parsed, game=active['game'])
                for row in data['games']:
                    if row['slug'] == active['slug'] and state == 'running':
                        row.update(state='running', reason='Construction en cours')
            return data
        serve(status, lambda name, show_launcher=True: dashboard_play(ROOT, name, show_launcher), lambda name: dashboard_settings(ROOT, name), lambda name, values: dashboard_save_settings(ROOT, name, values), stop_on_stdin_eof=args.stop_on_stdin_eof)
        return
    if action == 'list':
        for row in snapshot(ROOT)['games']:
            print(f'{row["slug"]:65} {row["reason"]}')
        return
    with operation(ROOT):
        if action == 'import':
            folders = [Path(os.environ['FROM'])] if os.environ.get('FROM') else [Path.home() / 'Downloads', ROOT / 'inbox']
            import_files(ROOT, folders)
        elif action == 'all':
            for game in games(ROOT):
                state, reason = state_for(ROOT, game, profiles(ROOT).get(game['title_id']), source_stamp(ROOT))
                if state in ('missing', 'unsupported', 'untested'):
                    print(f'IGNORÉ  {game["name"]} : {reason}', flush=True)
                    continue
                build(ROOT, game)
        else:
            game = choose_game(ROOT, os.environ.get('GAME', ''), os.environ.get('EDITION'))
            if action == 'clean':
                path = ROOT / '.build' / game['slug']
                if path.is_symlink() or path.resolve().parent != (ROOT / '.build').resolve():
                    raise ValueError('Chemin de cache inattendu — nettoyage refusé')
                if path.exists():
                    shutil.rmtree(path)
                print('Caches effacés ; jeu, application et sauvegardes conservés')
            elif action == 'run' and app_path(ROOT, game).is_dir():
                print(f'OUVERTURE  {game["name"]} — application existante, sans reconstruction', flush=True)
                open_existing(ROOT, game)
            else:
                build(ROOT, game, allow_untested=os.environ.get('EXPERIMENTAL') == '1')
                if action == 'run':
                    subprocess.run(['open', str(app_path(ROOT, game))], check=True)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.SubprocessError, json.JSONDecodeError) as error:
        print(f'ERREUR : {error}', file=sys.stderr)
        sys.exit(1)
