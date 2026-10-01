"""Real archive execution tests; injected transport retains public URL validation."""
import copy
import importlib.util
import io
import json
import os
from unittest.mock import patch
from pathlib import Path
import stat
import tempfile
import unittest
import zipfile

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('release_installer', HERE.parent / 'scripts/install-releases.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class ReleaseInstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = self.root / 'project'
        self.project.mkdir()
        (self.project / 'gams.json').write_text('{}')
        (self.project / 'keep.txt').write_text('unchanged')
        self.lock_path = self.root / 'lock.json'
        self.lock = {'schema': 1, 'units': []}
        self.downloads = {}
        for name, (kind, path) in installer.UNITS.items():
            unit = {'name': name, 'kind': kind, 'version': '0.1.0', 'tag': 'v0.1.0', 'files': [path], 'assets': {}}
            self.lock['units'].append(unit)
            if kind == 'component':
                payloads = {installer.asset_names(name, '0.1.0')[0]: b'\x00asm\x0d\x00\x01\x00fixture', 'LICENSE': b'license', 'NOTICE': b'notice'}
            else:
                payloads = {installer.asset_names(name, '0.1.0')[0]: self.archive(unit)}
            self.pin(unit, payloads)
        self.save()

    def archive(self, unit, mutate=None):
        path = unit['files'][0]
        contents = {path: b'export default 1;', 'LICENSE': b'license', 'NOTICE': b'notice', 'README.md': b'readme'}
        metadata = {key: unit[key] for key in ('name', 'kind', 'version')}
        metadata['entry'] = path
        metadata['host'] = {'target': '2.0.3', 'note': 'Host source contract targeted; package-level GUI validation remains a release gate.'}
        metadata['files'] = {path: installer.digest(contents[path])}
        if mutate:
            mutate(contents, metadata)
        contents['unit.json'] = json.dumps(metadata).encode()
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as archive:
            for name, data in contents.items():
                archive.writestr(name, data)
        return buffer.getvalue()

    def pin(self, unit, payloads):
        payloads['SHA256SUMS'] = ''.join(f'{installer.digest(data)}  {name}\n' for name, data in payloads.items() if name != 'SHA256SUMS').encode()
        for name, data in payloads.items():
            url = installer.release_url(unit['name'], unit['tag'], name)
            unit['assets'][name] = {'url': url, 'sha256': installer.digest(data)}
            self.downloads[url] = data

    def save(self):
        self.lock_path.write_text(json.dumps(self.lock))

    def snapshot(self):
        return {p.relative_to(self.project).as_posix(): p.read_bytes() for p in self.project.rglob('*') if p.is_file()}

    def run_install(self):
        self.save()
        return installer.install(self.project, self.lock_path, self.downloads.__getitem__)

    def assert_failure(self, fetch=None):
        before = self.snapshot()
        self.save()
        with self.assertRaises((ValueError, KeyError, OSError, zipfile.BadZipFile)):
            installer.install(self.project, self.lock_path, fetch or self.downloads.__getitem__)
        self.assertEqual(before, self.snapshot())

    def test_install_all_paths_notices_receipt_and_repeat(self):
        self.run_install()
        for name, (kind, path) in installer.UNITS.items():
            self.assertTrue((self.project / path).is_file())
            self.assertEqual((self.project / installer.NOTICES / name / 'LICENSE').read_bytes(), b'license')
            self.assertEqual((self.project / installer.NOTICES / name / 'NOTICE').read_bytes(), b'notice')
        receipt = json.loads((self.project / installer.RECEIPT).read_text())
        self.assertEqual(len(receipt['units']), 18)
        self.assertEqual(receipt['units'][0]['sources'], self.lock['units'][0]['assets'])
        before = self.snapshot()
        self.run_install()
        self.assertEqual(before, self.snapshot())

    def test_last_download_mismatch_and_transport_failure_do_not_mutate(self):
        url = list(self.downloads)[-1]
        original = self.downloads[url]
        self.downloads[url] = b'corrupt'
        self.assert_failure()
        self.downloads[url] = original
        def fail_last(value):
            if value == url:
                raise OSError('network failure')
            return self.downloads[value]
        self.assert_failure(fail_last)

    def test_missing_lock(self):
        before = self.snapshot()
        with self.assertRaises(FileNotFoundError):
            installer.install(self.project, self.root / 'missing')
        self.assertEqual(before, self.snapshot())

    def test_invalid_pins_selection_and_urls(self):
        original = copy.deepcopy(self.lock)
        for field, value in [('version', 'latest'), ('version', '01.1.0'), ('tag', 'main'), ('files', ['../bad']), ('kind', 'theme')]:
            self.lock = copy.deepcopy(original)
            self.lock['units'][0][field] = value
            self.assert_failure()
        self.lock = copy.deepcopy(original)
        self.lock['units'].append(copy.deepcopy(self.lock['units'][0]))
        self.assert_failure()
        for value in ['', 'PLACEHOLDER', '0' * 63]:
            self.lock = copy.deepcopy(original)
            next(iter(self.lock['units'][0]['assets'].values()))['sha256'] = value
            self.assert_failure()
        for value in ['http://localhost/test', 'https://evil.test/a', 'https://github.com/kkgams/plugin.fs/releases/latest/download/plugin.fs.wasm']:
            self.lock = copy.deepcopy(original)
            next(iter(self.lock['units'][0]['assets'].values()))['url'] = value
            self.assert_failure()

    def test_archive_metadata_and_file_hash_attacks(self):
        unit = self.lock['units'][-1]
        asset = installer.asset_names(unit['name'], unit['version'])[0]
        mutations = [lambda c, m: m.update(name='view.files'), lambda c, m: m.update(kind='view'),
                     lambda c, m: m.update(version='9.9.9'), lambda c, m: m.update(files={'evil.js': 'a'*64}),
                     lambda c, m: m.update(entry='themes/wrong.css'),
                     lambda c, m: m.update(host={'target': '2.0.4', 'note': 'wrong target'}),
                     lambda c, m: m.update(host={'target': '2.0.3', 'note': None}),
                     lambda c, m: m.update(host={'minimum': '2.0.3', 'tested': ['2.0.3'], 'note': 'legacy'}),
                     lambda c, m: m.update(extra=True),
                     lambda c, m: c.update({unit['files'][0]: b'tampered'})]
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                self.pin(unit, {asset: self.archive(unit, mutate)})
                self.assert_failure()

    def test_unexpected_traversal_absolute_backslash_and_symlink_members(self):
        unit = self.lock['units'][-1]
        asset = installer.asset_names(unit['name'], unit['version'])[0]
        for name in ['../bad', '/bad', 'C:/bad', 'themes\\bad', 'src/extra.js', 'themes//bad']:
            self.pin(unit, {asset: self.archive(unit, lambda c, m: c.update({name: b'bad'}))})
            self.assert_failure()
        for attack in ['symlink', 'duplicate', 'bomb']:
            buffer = io.BytesIO(self.archive(unit))
            with zipfile.ZipFile(buffer, 'a') as archive:
                if attack == 'duplicate':
                    archive.writestr('LICENSE', b'duplicate')
                elif attack == 'symlink':
                    info = zipfile.ZipInfo('link')
                    info.external_attr = (stat.S_IFLNK | 0o777) << 16
                    archive.writestr(info, '../outside')
                else:
                    archive.writestr('bomb', b'0' * 100000, compress_type=zipfile.ZIP_DEFLATED)
            self.pin(unit, {asset: buffer.getvalue()})
            self.assert_failure()

    def test_checksum_sidecar_disagreement(self):
        unit = self.lock['units'][-1]
        url = unit['assets']['SHA256SUMS']['url']
        self.downloads[url] = b'0' * 64 + b'  theme.the98-0.1.0.zip\n'
        unit['assets']['SHA256SUMS']['sha256'] = installer.digest(self.downloads[url])
        self.assert_failure()

    def test_existing_destination_symlink_preflight(self):
        outside = self.root / 'outside'
        outside.mkdir()
        (self.project / 'themes').symlink_to(outside, target_is_directory=True)
        self.assert_failure()
        self.assertEqual(list(outside.iterdir()), [])

    def test_build_lock_public_release_availability_and_complete_validation(self):
        selection = {'schema': 1, 'units': []}
        downloads = dict(self.downloads)
        for unit in self.lock['units']:
            selected = {k: unit[k] for k in ('name', 'kind', 'version', 'tag')}
            selected['status'] = 'planned-not-ready'
            selection['units'].append(selected)
            downloads[f'https://api.github.com/repos/kkgams/{unit["name"]}/releases/tags/{unit["tag"]}'] = json.dumps({
                'tag_name': unit['tag'], 'draft': False, 'prerelease': False, 'published_at': '2026-03-01T00:00:00Z',
                'assets': [{'name': n, 'browser_download_url': p['url']} for n, p in unit['assets'].items()]}).encode()
        path = self.root / 'selection.json'
        path.write_text(json.dumps(selection))
        output = self.root / 'review.json'
        last = list(downloads)[-1]
        missing = dict(downloads)
        del missing[last]
        with self.assertRaises(KeyError):
            installer.build_lock(path, output, missing.__getitem__)
        self.assertFalse(output.exists())
        original = json.loads(downloads[last])
        invalid = [dict(original, draft=True), dict(original, prerelease=True),
                   dict(original, published_at=None), dict(original, published_at=''),
                   dict(original, assets=original['assets'] + [original['assets'][0]])]
        missing_publication = dict(original)
        del missing_publication['published_at']
        invalid.append(missing_publication)
        before = self.snapshot()
        for release in invalid:
            with self.subTest(release=release):
                downloads[last] = json.dumps(release).encode()
                with self.assertRaises((ValueError, KeyError)):
                    installer.build_lock(path, output, downloads.__getitem__)
                self.assertFalse(output.exists())
                self.assertEqual(before, self.snapshot())
        downloads[last] = json.dumps(original).encode()
        self.assertEqual(installer.build_lock(path, output, downloads.__getitem__), self.lock)
        with self.assertRaises(ValueError):
            installer.build_lock(path, output, downloads.__getitem__)


release_spec = importlib.util.spec_from_file_location('release', HERE.parent / 'scripts/release.py')
release = importlib.util.module_from_spec(release_spec)
release_spec.loader.exec_module(release)


class PackagingTests(unittest.TestCase):
    pin = ReleaseInstallTests.pin
    save = ReleaseInstallTests.save
    archive = ReleaseInstallTests.archive

    def setUp(self):
        ReleaseInstallTests.setUp(self)
        self.source = {
            'gams.json': b'{}', 'README.md': b'readme', 'LICENSE': b'Apache fixture',
            'flake.lock': b'locked fixture',
            'BROWSER-README.md': b'browser readme', 'THIRD-PARTY-REVIEW.md': b'review',
            'THIRD-PARTY-NOTICES.txt': b'full upstream license fixture',
            'release.json': json.dumps({'name': 'example.game1', 'version': '0.1.0', 'repository': 'kkgams/example.game1', 'license': 'Apache-2.0'}).encode(),
            'release-lock.json': json.dumps(self.lock).encode(),
            'game/THIRD_PARTY.md': b'upstream inventory',
            'game/THIRD_PARTY_LICENSES/full.txt': b'full upstream license fixture',
            'game/web/index.html': b'index', 'game/web/gl-bridge.js': b'bridge',
            'content/generated/power.rspk': b'pack',
            'scripts/release.py': b'tooling fixture',
        }
        evidence = json.dumps({'files_sha256': {p: installer.digest(d) for p, d in self.source.items() if p != 'LICENSE'}}).encode()
        self.source['NOTICE-EVIDENCE.json'] = evidence
        self.source['NOTICE'] = ('NOTICE-EVIDENCE.json SHA-256: ' + installer.digest(evidence)).encode()
        for path, data in self.source.items():
            target = self.project / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        self.approval = patch.dict(os.environ, {**{'APPROVED_' + n + '_SHA256': installer.digest(self.source[n]) for n in ('LICENSE', 'NOTICE')}, 'GITHUB_REPOSITORY': 'kkgams/example.game1'})
        self.approval.start()
        self.addCleanup(self.approval.stop)
        self.tracking = patch.object(release, 'tracked', return_value=self.source)
        self.tracking.start()
        self.addCleanup(self.tracking.stop)
        for url, data in self.downloads.items():
            p = self.project / release.CACHE / installer.digest(url.encode())
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
        installer.install(self.project, self.project / 'release-lock.json', self.downloads.__getitem__)
        for name, data in zip(release.WEB, (b'index', b'bridge', bytes.fromhex('0061736d01000000') + b'fixture', b'pack')):
            p = self.project / 'game/build.nosync/web' / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
        proof = {'schema': 1, 'flake_lock_sha256': installer.digest(self.source['flake.lock']),
                 'odin_version': 'dev-2026-05 fixture', 'zig_version': '0.16.0',
                 'outputs_sha256': {name: installer.digest((self.project / 'game/build.nosync/web' / name).read_bytes()) for name in release.WEB}}
        receipt = self.project / 'dist/proof/build-receipt.json'
        receipt.parent.mkdir(parents=True)
        receipt.write_text(json.dumps(proof))
        self.out = self.root / 'candidate'

    def test_stage_check_determinism_layout_no_network(self):
        with patch.object(release.installer, 'download', side_effect=AssertionError('network forbidden')):
            release.stage(self.project, self.out, 'v0.1.0')
            release.check(self.project, self.out, 'v0.1.0')
            other = self.root / 'second'
            release.stage(self.project, other, 'v0.1.0')
        for path in self.out.iterdir():
            self.assertEqual(path.read_bytes(), (other / path.name).read_bytes())
        with zipfile.ZipFile(self.out / 'example.game1-0.1.0-project.zip') as z:
            self.assertTrue(all(n.startswith('example.game1/') for n in z.namelist()))
            self.assertIn('example.game1/game/build.nosync/web/station-demo.wasm', z.namelist())
            self.assertIn('example.game1/' + installer.RECEIPT, z.namelist())
        with zipfile.ZipFile(self.out / 'example.game1-0.1.0-web.zip') as z:
            self.assertIn('station-demo.wasm', z.namelist())
            self.assertNotIn('gams.json', z.namelist())

    def test_build_receipt_must_bind_actual_outputs_and_tools(self):
        receipt = self.project / 'dist/proof/build-receipt.json'
        original = json.loads(receipt.read_text())
        for field, value in [('flake_lock_sha256', '0' * 64), ('outputs_sha256', {}), ('zig_version', 'wrong')]:
            with self.subTest(field=field):
                proof = dict(original, **{field: value})
                receipt.write_text(json.dumps(proof))
                with self.assertRaises(ValueError):
                    release.payload(self.project, 'v0.1.0')
        receipt.write_text(json.dumps(original))

    def test_empty_legal_documents_fail_even_with_refreshed_hashes(self):
        for path in ('LICENSE', 'game/THIRD_PARTY.md', 'game/THIRD_PARTY_LICENSES/full.txt'):
            original = self.source[path]
            self.source[path] = b'   \n'
            with self.subTest(path=path), patch.dict(os.environ, {'APPROVED_LICENSE_SHA256': installer.digest(self.source['LICENSE'])}):
                with self.assertRaisesRegex(ValueError, 'empty'):
                    release.approved(self.project, self.source)
            self.source[path] = original

    def test_final_sidecar_and_duplicate_archive_fail(self):
        release.stage(self.project, self.out, 'v0.1.0')
        sums = self.out / 'SHA256SUMS'
        original = sums.read_bytes()
        sums.write_bytes(b'bad')
        with self.assertRaises(ValueError):
            release.check(self.project, self.out, 'v0.1.0')
        sums.write_bytes(original)
        target = self.out / 'example.game1-0.1.0-web.zip'
        with zipfile.ZipFile(target, 'a') as z:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', UserWarning)
                z.writestr('NOTICE', b'duplicate')
        with self.assertRaisesRegex(ValueError, 'duplicate ZIP'):
            release.check(self.project, self.out, 'v0.1.0')

    def test_corruption_missing_wasm_and_traversal_candidate(self):
        release.stage(self.project, self.out, 'v0.1.0')
        target = self.out / 'example.game1-0.1.0-web.zip'
        original = target.read_bytes()
        for attack in ('corrupt', 'missing', 'traversal'):
            if attack == 'corrupt':
                target.write_bytes(b'not zip')
            else:
                with zipfile.ZipFile(io.BytesIO(original)) as z:
                    files = {n: z.read(n) for n in z.namelist()}
                if attack == 'missing':
                    del files['station-demo.wasm']
                else:
                    files['../evil'] = b'evil'
                if attack == 'traversal':
                    stream = io.BytesIO()
                    with zipfile.ZipFile(stream, 'w') as z:
                        for n, d in files.items():
                            z.writestr(n, d)
                    target.write_bytes(stream.getvalue())
                else:
                    target.write_bytes(release.archive(files))
            with self.assertRaises((ValueError, zipfile.BadZipFile)):
                release.check(self.project, self.out, 'v0.1.0')

    def test_missing_wasm_incomplete_lock_receipt_and_cached_pin(self):
        wasm = self.project / 'game/build.nosync/web/station-demo.wasm'
        wasm.unlink()
        with self.assertRaises(ValueError):
            release.payload(self.project, 'v0.1.0')
        wasm.write_bytes(bytes.fromhex('0061736d01000000') + b'fixture')
        receipt = self.project / installer.RECEIPT
        receipt.write_bytes(b'{}')
        with self.assertRaises(ValueError):
            release.payload(self.project, 'v0.1.0')
        self.source['release-lock.json'] = json.dumps({'schema': 1, 'units': []}).encode()
        with self.assertRaises(ValueError):
            release.payload(self.project, 'v0.1.0')

    def test_cached_release_and_installed_asset_hashes(self):
        unit = self.lock['units'][0]
        asset = installer.asset_names(unit['name'], unit['version'])[0]
        cached = self.project / release.CACHE / installer.digest(unit['assets'][asset]['url'].encode())
        original = cached.read_bytes()
        cached.write_bytes(b'corrupt upstream artifact')
        with self.assertRaises(ValueError):
            release.payload(self.project, 'v0.1.0')
        cached.write_bytes(original)
        (self.project / unit['files'][0]).write_bytes(b'corrupt installed artifact')
        with self.assertRaises(ValueError):
            release.payload(self.project, 'v0.1.0')

    def test_evidence_symlink_and_source_changes(self):
        bridge = self.project / 'game/web/gl-bridge.js'
        bridge.write_bytes(b'changed audited source')
        with self.assertRaises(ValueError):
            release.payload(self.project, 'v0.1.0')
        bridge.unlink()
        bridge.symlink_to(self.project / 'game/web/index.html')
        with self.assertRaises(ValueError):
            release.payload(self.project, 'v0.1.0')

    def test_source_selection_requires_git_root_committed_files_and_excludes_junk(self):
        self.project = self.project.resolve()
        self.tracking.stop()
        required = ('gams.json', 'release-lock.json', 'LICENSE', 'NOTICE', 'NOTICE-EVIDENCE.json', 'README.md', 'Makefile', 'flake.nix', 'flake.lock', 'scripts/install-releases.py', 'scripts/release.py', 'game/Makefile', 'game/THIRD_PARTY.md')
        paths = list(required) + ['.github/workflows/release.yml', 'game/build.nosync/extra', 'node_modules/a', 'dist/junk', 'game/env.o', 'plugins/fs.comp.wasm']
        def git(command):
            if '--show-toplevel' in command:
                return str(self.project).encode() + b'\n'
            if 'ls-files' in command:
                return ('\0'.join(paths) + '\0').encode()
            return b'committed'
        with patch.object(release.subprocess, 'check_output', side_effect=git), patch.object(release, 'read', return_value=b'committed'):
            self.assertEqual(set(release.tracked(self.project)), set(required))
            paths.append('../escape')
            with self.assertRaises(ValueError):
                release.tracked(self.project)
            paths.pop()
            paths.append('cmd/app/native-source.rs')
            with self.assertRaises(ValueError):
                release.tracked(self.project)
            paths.pop()
            with patch.object(release, 'read', return_value=b'dirty'):
                with self.assertRaises(ValueError):
                    release.tracked(self.project)

    def test_release_absence_only_authenticated_404(self):
        with patch.dict(os.environ, {'GH_TOKEN': 'test-token'}):
            error = release.urllib.error.HTTPError('https://api.github.com', 404, 'missing', {}, None)
            with patch.object(release.urllib.request, 'urlopen', side_effect=error):
                release.absent(self.project, 'v0.1.0')
            for status in (401, 403, 429, 500):
                error = release.urllib.error.HTTPError('https://api.github.com', status, 'failure', {}, None)
                with patch.object(release.urllib.request, 'urlopen', side_effect=error):
                    with self.assertRaises(release.urllib.error.HTTPError):
                        release.absent(self.project, 'v0.1.0')
            with patch.object(release.urllib.request, 'urlopen'):
                with self.assertRaises(ValueError):
                    release.absent(self.project, 'v0.1.0')

    def test_tag_must_match_current_release_head_and_workflow_sha(self):
        refs = {'HEAD': b'abc\n', 'FETCH_HEAD': b'abc\n', 'v0.1.0^{commit}': b'abc\n'}
        with patch.dict(os.environ, {'GITHUB_SHA': 'abc'}), patch.object(release.subprocess, 'run'), patch.object(release.subprocess, 'check_output', side_effect=lambda c: refs[c[-1]]):
            release.branch(self.project, 'v0.1.0')
            refs['FETCH_HEAD'] = b'stale\n'
            with self.assertRaises(ValueError):
                release.branch(self.project, 'v0.1.0')

    def test_policy_and_approval_failclosed(self):
        for tag in ('v0.2.0', '0.1.0', 'v01.1.0'):
            with self.assertRaises(ValueError):
                release.payload(self.project, tag)
        with patch.dict(os.environ, {'APPROVED_NOTICE_SHA256': '0' * 64}):
            with self.assertRaises(ValueError):
                release.payload(self.project, 'v0.1.0')
        with patch.dict(os.environ, {'GITHUB_REPOSITORY': 'wrong/repo'}):
            with self.assertRaises(ValueError):
                release.payload(self.project, 'v0.1.0')


if __name__ == '__main__':
    unittest.main()
