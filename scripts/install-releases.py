#!/usr/bin/env python3
"""Install reviewed, pinned public GitHub Project Unit releases (stdlib only)."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import stat
import tempfile
import urllib.request
import zipfile

OWNER = 'kkgams'
MAX_DOWNLOAD = 32 * 1024 * 1024
MAX_STAGE = 256 * 1024 * 1024
NOTICES = 'notices/project-units'
RECEIPT = 'build.nosync/release-install.json'
# Exact deployed paths from the ecosystem repositories.json, not config ids.
UNITS = {
    'plugin.fs': ('component', 'plugins/fs.comp.wasm'),
    'plugin.layout': ('component', 'plugins/layout.comp.wasm'),
    'plugin.lua': ('component', 'plugins/lua.comp.wasm'),
    'plugin.respack': ('component', 'plugins/respack.comp.wasm'),
    'plugin.director-compiler': ('component', 'plugins/director-compiler.comp.wasm'),
    'view.files': ('view', 'views/view-files.js'),
    'view.code': ('view', 'views/view-code.js'),
    'view.ng': ('view', 'views/view-ng.js'),
    'view.ng-node': ('view', 'views/view-ng-node.js'),
    'view.files-rename': ('view', 'views/files-rename.js'),
    'view.files-default': ('view', 'views/files-default.js'),
    'ui-service.context': ('ui-service', 'ui-plugins/context.js'),
    'ui-service.keys': ('ui-service', 'ui-plugins/keys.js'),
    'ui-service.layout': ('ui-service', 'ui-plugins/layout.js'),
    'ui-service.toast': ('ui-service', 'ui-plugins/toast.js'),
    'ui-service.popup': ('ui-service', 'ui-plugins/popup.js'),
    'ui-service.tooltip': ('ui-service', 'ui-plugins/tooltip.js'),
    'theme.the98': ('theme', 'themes/the98.css'),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f'duplicate JSON key: {key}')
        result[key] = value
    return result


def parse(data):
    return json.loads(data, object_pairs_hook=unique_object)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def valid_hash(value):
    require(isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value),
            'expected real lowercase SHA-256 digest')


def relative(path):
    require(isinstance(path, str) and path and '\\' not in path and ':' not in path
            and all(part not in ('', '.', '..') for part in path.split('/'))
            and not any(ord(c) < 32 for c in path), f'unsafe relative path: {path!r}')
    return path


def release_url(name, tag, asset):
    relative(asset)
    require('/' not in asset, 'asset must be a filename')
    return f'https://github.com/{OWNER}/{name}/releases/download/{tag}/{asset}'


def asset_names(name, version):
    if UNITS[name][0] == 'component':
        # The compiler's existing release predates the plugin.<slug> convention.
        wasm = 'director-compiler.wasm' if name == 'plugin.director-compiler' else name + '.wasm'
        return [wasm, 'LICENSE', 'NOTICE', 'SHA256SUMS']
    return [f'{name}-{version}.zip', 'SHA256SUMS']


def validate(document, locked):
    require(set(document) == {'schema', 'units'} and document['schema'] == 1, 'invalid document schema')
    require(isinstance(document['units'], list), 'units must be a list')
    names = [u['name'] for u in document['units']]
    require(len(names) == len(set(names)) and set(names) == set(UNITS), 'expected all 18 distinct Project Units')
    destinations = set()
    for unit in document['units']:
        name = unit['name']
        expected = {'name', 'kind', 'version', 'tag', 'files', 'assets'} if locked else {'name', 'kind', 'version', 'tag', 'status'}
        require(set(unit) == expected, f'invalid fields: {name}')
        require(unit['kind'] == UNITS[name][0], f'wrong kind: {name}')
        version = unit['version']
        require(isinstance(version, str) and re.fullmatch(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)', version), 'explicit release version required')
        require(unit['tag'] == 'v' + version, 'tag must match explicit version')
        if not locked:
            require(unit['status'] in ('published-observed', 'planned-not-ready'), 'invalid selection status')
            continue
        require(unit['files'] == [UNITS[name][1]], f'wrong deployment mapping: {name}')
        for path in unit['files']:
            relative(path)
            require(path not in destinations, 'duplicate deployment destination')
            destinations.add(path)
        require(set(unit['assets']) == set(asset_names(name, version)), f'wrong assets: {name}')
        for asset, pin in unit['assets'].items():
            require(set(pin) == {'url', 'sha256'}, 'invalid asset pin')
            require(pin['url'] == release_url(name, unit['tag'], asset), 'only exact public GitHub tagged asset URLs allowed')
            valid_hash(pin['sha256'])
    return document


def download(url):
    accept = 'application/vnd.github+json' if url.startswith('https://api.github.com/') else 'application/octet-stream'
    request = urllib.request.Request(url, headers={'User-Agent': 'example-game1-release-installer', 'Accept': accept})
    with urllib.request.urlopen(request, timeout=60) as response:
        require(response.geturl().startswith('https://'), 'non-HTTPS redirect')
        data = response.read(MAX_DOWNLOAD + 1)
    require(0 < len(data) <= MAX_DOWNLOAD, 'empty or oversized download')
    return data


def checksums(data):
    result = {}
    for line in data.decode('utf-8').splitlines():
        match = re.fullmatch(r'([0-9a-f]{64}) [ *]([^\r\n]+)', line)
        require(match is not None, 'invalid SHA256SUMS line')
        sha, name = match.groups()
        relative(name)
        require('/' not in name and name not in result, 'duplicate/unsafe checksum filename')
        result[name] = sha
    require(result, 'empty SHA256SUMS')
    return result


def unpack(unit, data):
    """Read only validated members; never extract an archive wholesale."""
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        members = archive.infolist()
        require(len(members) <= 128, 'too many ZIP members')
        names = []
        total = 0
        for info in members:
            relative(info.orig_filename)
            require(info.filename == info.orig_filename, 'normalized ZIP filename')
            mode = stat.S_IFMT(info.external_attr >> 16)
            require(mode in (0, stat.S_IFREG) and not info.is_dir()
                    and not info.external_attr & 0x10, 'non-regular ZIP member')
            require(not info.flag_bits & 1 and info.compress_type in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED), 'unsupported ZIP encoding')
            require(info.file_size <= MAX_DOWNLOAD and info.file_size <= max(1, info.compress_size) * 200, 'ZIP bomb limit')
            total += info.file_size
            names.append(info.filename)
        require(total <= MAX_DOWNLOAD and len(names) == len(set(names)), 'oversized/duplicate ZIP members')
        expected = set(unit['files']) | {'unit.json', 'LICENSE', 'NOTICE', 'README.md'}
        require(set(names) == expected, 'unexpected or missing ZIP members')
        metadata = parse(archive.read('unit.json'))
        require(set(metadata) == {'name', 'kind', 'version', 'entry', 'files', 'host'}, 'invalid unit.json fields')
        require(metadata['entry'] == UNITS[unit['name']][1], 'unit.json entry mismatch')
        host = metadata['host']
        require(isinstance(host, dict) and set(host) == {'target', 'note'}
                and host['target'] == '2.0.3' and isinstance(host['note'], str),
                'invalid unit.json Host source contract')
        for field in ('name', 'kind', 'version'):
            require(metadata[field] == unit[field], f'unit.json {field} mismatch')
        require(set(metadata['files']) == set(unit['files']), 'unit.json deployment mapping mismatch')
        files = {path: archive.read(path) for path in unit['files']}
        for path, data in files.items():
            valid_hash(metadata['files'][path])
            require(digest(data) == metadata['files'][path], f'mapped file checksum mismatch: {path}')
        for name in ('LICENSE', 'NOTICE', 'README.md', 'unit.json'):
            data = archive.read(name)
            require(data.strip(), f'empty {name}')
            files[f'{NOTICES}/{unit["name"]}/{name}'] = data
        return files


def stage(lock, fetch):
    validate(lock, True)
    files, receipts = {}, []
    for unit in lock['units']:
        payloads = {}
        for asset, pin in unit['assets'].items():
            data = fetch(pin['url'])
            require(0 < len(data) <= MAX_DOWNLOAD and digest(data) == pin['sha256'], f'download checksum mismatch: {unit["name"]}/{asset}')
            payloads[asset] = data
        sums = checksums(payloads['SHA256SUMS'])
        for asset, data in payloads.items():
            if asset != 'SHA256SUMS':
                require(sums[asset] == digest(data), f'SHA256SUMS mismatch: {asset}')
        artifact = asset_names(unit['name'], unit['version'])[0]
        if unit['kind'] == 'component':
            require(payloads[artifact].startswith(b'\x00asm\x0d\x00\x01\x00'), 'expected WASM component')
            deployed = {unit['files'][0]: payloads[artifact]}
            for notice in ('LICENSE', 'NOTICE'):
                require(payloads[notice].strip(), f'empty {notice}')
                deployed[f'{NOTICES}/{unit["name"]}/{notice}'] = payloads[notice]
        else:
            deployed = unpack(unit, payloads[artifact])
        for path, data in deployed.items():
            relative(path)
            require(path not in files, f'duplicate destination: {path}')
            files[path] = data
        require(sum(map(len, files.values())) <= MAX_STAGE, 'staging size limit')
        receipts.append({'name': unit['name'], 'version': unit['version'], 'tag': unit['tag'],
                         'sources': unit['assets'], 'files': {p: digest(d) for p, d in deployed.items()}})
    files[RECEIPT] = (json.dumps({'schema': 1, 'lock_sha256': digest(json.dumps(lock, sort_keys=True).encode()), 'units': receipts}, indent=2) + '\n').encode()
    return files


def target_path(project, path):
    relative(path)
    target = project / path
    for candidate in [target, *target.parents]:
        if candidate == project:
            break
        require(not candidate.is_symlink(), f'symlink destination: {candidate}')
        if candidate == target:
            require(not candidate.exists() or candidate.is_file(), f'not a file: {candidate}')
        else:
            require(not candidate.exists() or candidate.is_dir(), f'not a directory: {candidate}')
    return target


def install(project, lock_path, fetch=download):
    project = Path(project)
    require(project.is_dir() and not project.is_symlink(), 'expected real Project directory')
    project = project.resolve()
    require((project / 'gams.json').is_file(), 'Project gams.json required')
    lock = validate(parse(Path(lock_path).read_bytes()), True)
    files = stage(lock, fetch)  # All network, checksums and archive checks precede mutation.
    targets = {path: target_path(project, path) for path in files}
    for path in files:
        require(not any(parent.as_posix() in files for parent in Path(path).parents), 'overlapping destinations')
    # Verified bytes are held outside the Project until preflight is complete.
    # Atomic per-file replacement, not a transaction against OS/disk failures.
    for path, data in files.items():
        target = targets[path]
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as temporary:
            temporary.write(data)
            temporary_path = Path(temporary.name)
        try:
            temporary_path.replace(target)
        finally:
            temporary_path.unlink(missing_ok=True)
    return len(files)


def build_lock(selection_path, output, fetch=download):
    """Owner review operation, never implicitly called by installation."""
    selection = validate(parse(Path(selection_path).read_bytes()), False)
    lock = {'schema': 1, 'units': []}
    for selected in selection['units']:
        name, tag = selected['name'], selected['tag']
        request_url = f'https://api.github.com/repos/{OWNER}/{name}/releases/tags/{tag}'
        release = parse(fetch(request_url))
        require(release['tag_name'] == tag and release['draft'] is False
                and release['prerelease'] is False
                and isinstance(release['published_at'], str) and release['published_at'].strip(),
                'not a published stable tagged release')
        available = {a['name']: a for a in release['assets']}
        require(len(available) == len(release['assets']), 'duplicate GitHub release asset names')
        wanted = asset_names(name, selected['version'])
        require(set(wanted) <= set(available), f'public release assets not ready: {name}/{tag}')
        unit = {k: selected[k] for k in ('name', 'kind', 'version', 'tag')}
        unit['files'] = [UNITS[name][1]]
        unit['assets'] = {}
        for asset in wanted:
            url = release_url(name, tag, asset)
            require(available[asset]['browser_download_url'] == url, 'unexpected GitHub release URL')
            data = fetch(url)
            unit['assets'][asset] = {'url': url, 'sha256': digest(data)}
        lock['units'].append(unit)
    stage(lock, fetch)  # Validate sidecars and actual archives before publishing the lock.
    output = Path(output)
    require(not output.exists() and not output.is_symlink(), 'refusing to overwrite lock; review a new output file')
    with output.open('x') as stream:
        stream.write(json.dumps(lock, indent=2) + '\n')
    return lock


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    setup = commands.add_parser('install')
    setup.add_argument('--project', type=Path, default=root)
    setup.add_argument('--lock', type=Path, default=root / 'release-lock.json')
    review = commands.add_parser('build-lock')
    review.add_argument('--selection', type=Path, default=root / 'release-selection.json')
    review.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'install':
        print(f'Installed {install(args.project, args.lock)} verified files')
    else:
        build_lock(args.selection, args.output)
        print(f'Complete lock ready for owner review: {args.output}')


if __name__ == '__main__':
    main()
