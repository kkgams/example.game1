"""Source Project references use the already reviewed public release versions."""
import json
from pathlib import Path
import unittest
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]


class ProjectConfigTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / 'gams.json').read_text())
        lock = json.loads((ROOT / 'release-lock.json').read_text())
        self.units = {unit['name']: unit for unit in lock['units']}

    def assert_zip_source(self, source, name):
        unit = self.units[name]
        parts = urlsplit(source)
        archive = f'{name}-{unit["version"]}.zip'
        self.assertEqual(source.split('#', 1)[0], unit['assets'][archive]['url'])
        self.assertEqual(unquote(parts.fragment), unit['files'][0])
        self.assertEqual(parts.scheme, 'https')

    def test_plugins_use_existing_direct_wasm_assets(self):
        names = ['plugin.layout', 'plugin.lua', 'plugin.director-compiler', 'plugin.respack']
        expected = [next(pin['url'] for asset, pin in self.units[name]['assets'].items()
                         if asset.endswith('.wasm')) for name in names]
        self.assertEqual(self.config['plugins'], expected)

    def test_all_ui_units_use_pinned_zip_sources_and_explicit_entries(self):
        ui = self.config['ui']
        self.assertNotIn('path', ui['theme'])
        self.assert_zip_source(ui['theme']['url'], 'theme.the98')
        self.assertEqual(set(ui['services']), {f'ui-{name}' for name in
                         ('context', 'keys', 'layout', 'toast', 'popup', 'tooltip')})
        for id, entry in ui['services'].items():
            self.assert_zip_source(entry['url'], 'ui-service.' + id.removeprefix('ui-'))
        views = {
            'view-files': 'view.files', 'view-code': 'view.code', 'view-ng': 'view.ng',
            'view-ng-node': 'view.ng-node', 'files-rename': 'view.files-rename',
            'files-default': 'view.files-default',
        }
        self.assertEqual(set(ui['views']), set(views))
        for id, name in views.items():
            self.assert_zip_source(ui['views'][id]['url'], name)

    def test_save_bindings_and_authored_layout_remain_project_owned(self):
        keys = {entry['key']: entry for entry in self.config['ui']['keys']}
        self.assertEqual(keys['mod+s']['call'], ['activeView.save'])
        self.assertEqual(keys['mod+alt+s']['call'], ['project.save'])
        self.assertEqual(keys['mod+enter']['call'], ['activeView.run'])
        self.assertIn('content/power.director', self.config['ui']['services']['ui-layout']['config']['layout'])


if __name__ == '__main__':
    unittest.main()
