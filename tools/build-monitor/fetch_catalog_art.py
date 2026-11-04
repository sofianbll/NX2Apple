#!/usr/bin/env python3
"""Fetch one public image per game profile into art/catalog/ (stdlib only).

Order per profile: nlib cover -> sibling region variant's cover -> upstream gallery screenshot.
Writes art/catalog/<TID>.jpg (screenshots too, JPEG only; kind tells them apart), sources.json (successes) and missing.json (absences).
One attempt per URL, 6 parallel, 15 s per request, 1 MB per image, 25 MB downloaded in total.
"""
import json, os, re, shutil, subprocess, sys, threading, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.abspath(os.path.join(HERE, '..', '..', 'source'))
OUT = os.path.join(HERE, 'art', 'catalog')
NLIB = 'https://api.nlib.cc/nx/{}/icon/512'
RAW = 'https://raw.githubusercontent.com/seedds/nxnative/{}/docs/images/{}'
MAX_IMG, MAX_TOTAL, TIMEOUT, WORKERS = 1_000_000, 25_000_000, 15, 6
SIG = {'image/jpeg': b'\xff\xd8\xff', 'image/png': b'\x89PNG\r\n\x1a\n'}

total = 0
lock = threading.Lock()


def fetch(url):
    """-> (bytes, content-type) or raises RuntimeError with the reason."""
    global total
    deadline = time.monotonic() + TIMEOUT
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'nxnative-catalog/0.1'}), timeout=TIMEOUT) as r:
            ctype = r.headers.get_content_type()
            buf = b''
            while chunk := r.read(65536):
                buf += chunk
                if len(buf) > MAX_IMG:
                    raise RuntimeError(f'>{MAX_IMG} bytes')
                if time.monotonic() > deadline:
                    raise RuntimeError('timeout')
    except urllib.error.HTTPError as e:
        raise RuntimeError(f'HTTP {e.code}')
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise RuntimeError(f'{type(e).__name__}: {e}')
    if ctype not in SIG or not buf.startswith(SIG[ctype]):
        raise RuntimeError(f'not an image ({ctype}, sig {buf[:4].hex()})')
    with lock:
        if total + len(buf) > MAX_TOTAL:
            raise RuntimeError('total budget exceeded')
        total += len(buf)
    return buf, ctype


def write_atomic(path, data):
    tmp = path + '.part'
    with open(tmp, 'wb') as f:
        f.write(data)
    os.replace(tmp, path)


def profiles():
    text = open(os.path.join(SRC, 'dm/games/README.md')).read()
    rows = re.findall(r'^\| \[(.*?)\]\((\w+)/README\.md\) \| `(\w+)`', text, re.M)
    assert rows and all(r[1] == r[2] for r in rows)
    ids = [r[2] for r in rows]
    assert len(ids) == len(set(ids))
    return {r[2].upper(): r[0] for r in rows}


def base_title(name):
    # "X, Japanese release" / "X, Asian release" -> "X"
    return re.sub(r',\s*[^,]*\brelease$', '', name).strip()


def main():
    os.makedirs(OUT, exist_ok=True)
    names = profiles()
    commit = subprocess.check_output(['git', '-C', SRC, 'rev-parse', 'HEAD'], text=True).strip()
    gallery = {}
    for line in open(os.path.join(SRC, 'docs/images/gallery.tsv')):
        p = line.rstrip('\n').split('\t')
        if line.startswith('#') or len(p) < 4 or not p[3]:
            continue
        gallery[p[3].upper()] = p[0]

    sources, reasons = {}, {}

    def cover(tid):
        url = NLIB.format(tid)
        try:
            buf, _ = fetch(url)
        except RuntimeError as e:
            return tid, None, f'nlib cover: {e}'
        write_atomic(os.path.join(OUT, f'{tid}.jpg'), buf)
        return tid, {'name': names[tid], 'file': f'{tid}.jpg', 'source': url, 'kind': 'cover'}, None

    with ThreadPoolExecutor(WORKERS) as ex:
        for tid, entry, why in ex.map(cover, names):
            if entry:
                sources[tid] = entry
            else:
                reasons[tid] = [why]

    # region variants: same base title (exact match after stripping the release suffix) borrow a sibling's cover
    for tid in sorted(reasons):
        base = base_title(names[tid])
        sib = [t for t in sources if sources[t]['kind'] == 'cover' and 'shared_from' not in sources[t] and base_title(names[t]) == base]
        if sib:
            s = sib[0]
            shutil.copyfile(os.path.join(OUT, f'{s}.jpg'), os.path.join(OUT, f'{tid}.jpg'))
            sources[tid] = {**sources[s], 'name': names[tid], 'file': f'{tid}.jpg', 'shared_from': s}
            del reasons[tid]

    # upstream gallery screenshots, last resort (never called a cover)
    def shot(tid):
        img = gallery.get(tid)
        if not img:
            return tid, None, 'no gallery screenshot'
        url = RAW.format(commit, img)
        try:
            buf, ctype = fetch(url)
        except RuntimeError as e:
            return tid, None, f'gallery {img}: {e}'
        if ctype != 'image/jpeg':  # the backend serves art/catalog/<TID>.jpg only
            return tid, None, f'gallery {img}: {ctype}, not JPEG'
        fn = f'{tid}.jpg'
        write_atomic(os.path.join(OUT, fn), buf)
        return tid, {'name': names[tid], 'file': fn, 'source': url, 'kind': 'screenshot',
                     'provenance': {'repo': 'https://github.com/seedds/nxnative', 'path': f'docs/images/{img}', 'commit': commit}}, None

    with ThreadPoolExecutor(WORKERS) as ex:
        for tid, entry, why in ex.map(shot, sorted(reasons)):
            if entry:
                sources[tid] = entry
                del reasons[tid]
            else:
                reasons[tid].append(why)

    missing = {t: {'name': names[t], 'reasons': r} for t, r in sorted(reasons.items())}
    assert set(sources) | set(missing) == set(names) and not set(sources) & set(missing)
    for t, e in sources.items():
        assert e['file'] == f'{t}.jpg'
        p = os.path.join(OUT, e['file'])
        assert os.path.getsize(p) <= MAX_IMG and open(p, 'rb').read(3) == SIG['image/jpeg']
    write_atomic(os.path.join(OUT, 'sources.json'), (json.dumps(dict(sorted(sources.items())), indent=2, ensure_ascii=False) + '\n').encode())
    write_atomic(os.path.join(OUT, 'missing.json'), (json.dumps(missing, indent=2, ensure_ascii=False) + '\n').encode())
    kinds = [e['kind'] for e in sources.values()]
    print(f'profiles={len(names)} covers={kinds.count("cover")} (shared={sum("shared_from" in e for e in sources.values())}) '
          f'screenshots={kinds.count("screenshot")} missing={len(missing)} downloaded_bytes={total}')


LIBRARY = {  # TID -> name; art/catalog covers are reused, the others fetched into art/library/.
    '0100E65002BB8000': 'Stardew Valley', '01006BB00C6F0000': "The Legend of Zelda: Link's Awakening",
    '0100152000022000': 'Mario Kart 8 Deluxe', '01004B3023412000': 'Pokémon FireRed Version (French)',
    '0100C9A00ECE6000': 'Nintendo 64 - Nintendo Classics',
    '0100F43008C44000': 'Pokémon Legends: Z-A', '010018E011D92000': 'Pokémon Shining Pearl',
}


def library():
    lib = os.path.join(HERE, 'art', 'library')
    os.makedirs(lib, exist_ok=True)
    out = {}
    for tid, name in LIBRARY.items():
        url = NLIB.format(tid)
        if os.path.exists(os.path.join(OUT, f'{tid}.jpg')):
            out[tid] = {'name': name, 'file': f'art/catalog/{tid}.jpg', 'route': f'/art/catalog/{tid}.jpg',
                        'source': url, 'kind': 'cover', 'origin': 'reused from art/catalog'}
            continue
        buf, ctype = fetch(url)  # raises on failure: no silent gap
        assert ctype == 'image/jpeg'
        write_atomic(os.path.join(lib, f'{tid}.jpg'), buf)
        out[tid] = {'name': name, 'file': f'art/library/{tid}.jpg', 'route': f'/art/library/{tid}.jpg',
                    'source': url, 'kind': 'cover', 'origin': 'downloaded'}
    write_atomic(os.path.join(lib, 'sources.json'), (json.dumps(out, indent=2, ensure_ascii=False) + '\n').encode())
    print(f'library={len(out)} downloaded_bytes={total}')


if __name__ == '__main__':
    sys.exit(library() if sys.argv[1:] == ['library'] else main())
