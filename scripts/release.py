#!/usr/bin/env python3
"""Self-contained example release; final checks are strictly offline."""
import argparse
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import subprocess
import urllib.error
import urllib.request
import zipfile

_spec = importlib.util.spec_from_file_location('installer', Path(__file__).with_name('install-releases.py'))
installer = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(installer)
require, digest, parse = installer.require, installer.digest, installer.parse
WEB = ('index.html', 'gl-bridge.js', 'station-demo.wasm', 'station.rspk')
CACHE = 'build.nosync/release-assets'
FORBIDDEN = {'.git', '.github', 'build.nosync', 'node_modules', 'dist', 'tmp', 'temp', '__pycache__', '.DS_Store', 'sokol'}
GENERATED = {'env.o', 'room.glsl.odin', 'station.rspk'}


def read(root, path):
    installer.relative(path)
    local = installer.target_path(root, path)
    require(local.is_file(), 'required file missing: ' + path)
    require(local.stat().st_size <= installer.MAX_STAGE, 'oversized local input: ' + path)
    return local.read_bytes()


def metadata(root, tag):
    config = parse(read(root, 'release.json'))
    require(set(config) == {'name', 'version', 'repository', 'license'} and
            config['name'] == 'example.game1' and config['repository'] == 'kkgams/example.game1' and
            config['license'] == 'Apache-2.0' and re.fullmatch(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)', config['version']), 'invalid release policy')
    require(tag == 'v' + config['version'], 'tag/version mismatch')
    require(os.environ.get('GITHUB_REPOSITORY', config['repository']) == config['repository'], 'wrong repository')
    return config


def tracked(root):
    require(Path(subprocess.check_output(['git', '-C', str(root), 'rev-parse', '--show-toplevel']).decode().strip()).resolve() == root, 'standalone repository root required')
    paths = subprocess.check_output(['git', '-C', str(root), 'ls-files', '-z']).decode().split('\0')[:-1]
    result = {}
    for path in paths:
        installer.relative(path)
        parts = Path(path).parts
        if any(p in FORBIDDEN for p in parts) or path.startswith(('plugins/', 'views/', 'ui-plugins/', 'themes/')) or (parts[0] == 'game' and parts[-1] in GENERATED):
            continue
        require(parts[0] not in ('cmd', 'target') and not any(p.endswith(('.app', '.exe', '.dylib', '.so')) for p in parts) and parts[-1] not in ('gams', 'GAMS'), 'Host/native binary source boundary: ' + path)
        committed = subprocess.check_output(['git', '-C', str(root), 'show', 'HEAD:' + path])
        require(read(root, path) == committed, 'source differs from committed HEAD: ' + path)
        result[path] = committed
    for path in ('gams.json', 'release-lock.json', 'LICENSE', 'NOTICE', 'NOTICE-EVIDENCE.json', 'README.md', 'Makefile', 'flake.nix', 'flake.lock', 'scripts/install-releases.py', 'scripts/release.py', 'game/Makefile', 'game/THIRD_PARTY.md'):
        require(path in result, 'required committed source missing: ' + path)
    return result


def approved(root, source):
    for name in ('LICENSE', 'NOTICE'):
        expected = os.environ['APPROVED_' + name + '_SHA256']
        installer.valid_hash(expected)
        require(source[name].strip(), 'empty ' + name)
        require(digest(source[name]) == expected, name + ' approval mismatch')
    notice = source['NOTICE'].decode()
    require('PROVENANCE_PENDING' not in notice, 'audit pending')
    evidence = source['NOTICE-EVIDENCE.json']
    require('NOTICE-EVIDENCE.json SHA-256: ' + digest(evidence) in notice, 'NOTICE must bind evidence')
    mapping = parse(evidence)['files_sha256']
    require(isinstance(mapping, dict) and mapping, 'empty audit evidence')
    require('game/THIRD_PARTY.md' in mapping and any(p.startswith('game/THIRD_PARTY_LICENSES/') for p in mapping), 'third-party documentation and full license evidence required')
    # The audit describes source inputs, not an assertion of complete app ownership.
    required = set(source) - {'LICENSE', 'NOTICE', 'NOTICE-EVIDENCE.json', 'SOURCE.json'}
    require(required <= set(mapping), 'audit must cover committed source/build inputs/tooling')
    legal = [p for p in source if p.startswith('game/THIRD_PARTY_LICENSES/')]
    require(legal, 'full upstream license texts must be committed')
    for path in ['game/THIRD_PARTY.md', 'THIRD-PARTY-NOTICES.txt', *legal]:
        require(source[path].strip(), 'empty legal document: ' + path)
    for path in legal:
        require(source[path] in source['THIRD-PARTY-NOTICES.txt'], 'full upstream terms missing from export notice bundle: ' + path)
    for path, expected in mapping.items():
        installer.valid_hash(expected)
        require(digest(read(root, path)) == expected, 'audited input changed: ' + path)


def cache_fetch(root):
    def fetch(url):
        return read(root, CACHE + '/' + digest(url.encode()))
    return fetch


def install(root, lock_path, offline=False):
    lock = installer.validate(parse(read(root, lock_path)), True)
    def fetch(url):
        data = installer.download(url)
        target = installer.target_path(root, CACHE + '/' + digest(url.encode()))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return data
    # Preserve original public release bytes so stage/check can repeat the full
    # installer stage validation, including upstream ZIP hashes, without network.
    return installer.install(root, root / lock_path, cache_fetch(root) if offline else fetch)


def payload(root, tag):
    config = metadata(root, tag)
    source = tracked(root)
    approved(root, source)
    lock = installer.validate(parse(source['release-lock.json']), True)
    installed = installer.stage(lock, cache_fetch(root))
    for path, expected in installed.items():
        require(read(root, path) == expected, 'installed pin/receipt differs: ' + path)
    require(not set(source) & set(installed), 'source/installed collision')
    web = {name: read(root, 'game/build.nosync/web/' + name) for name in WEB}
    require(web['station-demo.wasm'].startswith(b'\0asm\x01\0\0\0'), 'expected core game WASM')
    require(all(web.values()), 'empty web input')
    require(web['index.html'] == read(root, 'game/web/index.html') and web['gl-bridge.js'] == read(root, 'game/web/gl-bridge.js'), 'browser support source mismatch')
    require(web['station.rspk'] == read(root, 'content/generated/power.rspk'), 'content pack mismatch')
    receipt_bytes = read(root, 'dist/proof/build-receipt.json')
    receipt = parse(receipt_bytes)
    require(receipt['schema'] == 1 and receipt['flake_lock_sha256'] == digest(source['flake.lock']), 'build receipt lock mismatch')
    require(receipt['outputs_sha256'] == {p: digest(d) for p, d in web.items()}, 'build receipt output mismatch')
    require('dev-2026-05' in receipt['odin_version'] and receipt['zig_version'] == '0.16.0', 'unreviewed game tool versions')
    project = dict(source, **installed)
    project['BUILD-RECEIPT.json'] = receipt_bytes
    project.update({'game/build.nosync/web/' + p: d for p, d in web.items()})
    project['RELEASE-MANIFEST.json'] = (json.dumps({'schema': 1, 'source_sha256': {p: digest(d) for p, d in source.items()}, 'installed_sha256': {p: digest(d) for p, d in installed.items()}, 'web_sha256': {p: digest(d) for p, d in web.items()}}, sort_keys=True, indent=2) + '\n').encode()
    browser = dict(web)
    browser.update({p: source[p] for p in ('LICENSE', 'NOTICE', 'THIRD-PARTY-NOTICES.txt')})
    browser['README.md'] = source['BROWSER-README.md']
    browser['THIRD-PARTY-REVIEW.md'] = source['THIRD-PARTY-REVIEW.md']
    browser['UPSTREAM-NOTICES/NOTICE-EVIDENCE.json'] = source['NOTICE-EVIDENCE.json']
    for path, data in source.items():
        if path.startswith('game/THIRD_PARTY_LICENSES/') or path == 'game/THIRD_PARTY.md':
            browser['UPSTREAM-NOTICES/' + path.removeprefix('game/')] = data
    stem = config['name'] + '-' + config['version']
    return {stem + '-project.zip': {'example.game1/' + p: d for p, d in project.items()}, stem + '-web.zip': browser}


def archive(files):
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_STORED) as z:
        for path, data in sorted(files.items()):
            installer.relative(path)
            info = zipfile.ZipInfo(path, (1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            z.writestr(info, data)
    return out.getvalue()


def outputs(root, tag):
    files = {name: archive(data) for name, data in payload(root, tag).items()}
    files.update({name: read(root, name) for name in ('LICENSE', 'NOTICE')})
    files['SHA256SUMS'] = ''.join(f'{digest(data)}  {name}\n' for name, data in sorted(files.items())).encode()
    return files


def stage(root, out, tag):
    files = outputs(root, tag)
    out.mkdir(parents=True, exist_ok=False)
    for name, data in files.items():
        (out / name).write_bytes(data)


def check(root, out, tag):
    expected = outputs(root, tag)
    require({p.name for p in out.iterdir()} == set(expected), 'missing/extra candidate files')
    for name, data in expected.items():
        actual = read(out.resolve(), name)
        if name.endswith('.zip'):
            with zipfile.ZipFile(io.BytesIO(actual)) as z:
                require(len(z.namelist()) == len(set(z.namelist())), 'duplicate ZIP members')
                for info in z.infolist():
                    installer.relative(info.orig_filename)
                    require(info.filename == info.orig_filename and not info.is_dir() and info.external_attr == 0o100644 << 16, 'unsafe ZIP metadata')
                require(z.testzip() is None, 'corrupt ZIP')
        require(actual == data, 'candidate byte/content/policy mismatch: ' + name)


def branch(root, tag):
    metadata(root, tag)
    subprocess.run(['git', '-C', str(root), 'fetch', '--no-tags', 'origin', 'refs/heads/release'], check=True)
    def rev(ref):
        return subprocess.check_output(['git', '-C', str(root), 'rev-parse', ref]).decode().strip()
    require(rev('HEAD') == rev('FETCH_HEAD') == rev(tag + '^{commit}') == os.environ['GITHUB_SHA'], 'tag must match current release HEAD and workflow SHA')


def absent(root, tag):
    config = metadata(root, tag)
    request = urllib.request.Request(f'https://api.github.com/repos/{config["repository"]}/releases/tags/{tag}', headers={'Authorization': 'Bearer ' + os.environ['GH_TOKEN'], 'Accept': 'application/vnd.github+json'})
    try:
        with urllib.request.urlopen(request, timeout=30):
            pass
    except urllib.error.HTTPError as error:
        error.close()
        if error.code == 404:
            return
        raise
    raise ValueError('immutable release exists; refusing overwrite')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['install', 'stage', 'check', 'branch', 'absent'])
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--out', type=Path, default=Path('dist/candidate'))
    parser.add_argument('--tag', default='v0.2.0')
    parser.add_argument('--lock', default='release-lock.json')
    parser.add_argument('--offline', action='store_true')
    args = parser.parse_args()
    root = args.root.resolve()
    if args.command == 'install':
        install(root, args.lock, args.offline)
    elif args.command in ('stage', 'check'):
        globals()[args.command](root, args.out, args.tag)
    else:
        globals()[args.command](root, args.tag)
