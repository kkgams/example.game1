# Source Project: released Unit URLs

The current `gams.json` requires the development GAMS Host with ZIP installation
and explicit bootstrap UI Service URLs. Released Host v2.0.3 does not support this
config. This migration does not publish a Project or change reviewed Unit versions.

## Sources

- Four configured components (`layout`, `lua`, `director-compiler`, `respack`)
  use their existing tagged v0.1.0 `.wasm` assets. Those releases have no ZIPs.
- Six Views, six UI Services and the theme use tagged v0.1.0 ZIP assets with
  explicit archive-root-relative entry selectors, for example:
  `https://github.com/kkgams/view.code/releases/download/v0.1.0/view.code-0.1.0.zip#views/view-code.js`.
- The Host's temporary FS bootstrap constant uses the direct public
  `plugin.fs` v0.1.1 WASM asset. FS is not duplicated in `config.plugins`.
- All six shell service roles are explicit under `ui.services`: `ui-context`,
  `ui-keys`, `ui-layout`, `ui-toast`, `ui-popup`, `ui-tooltip`. Layout configuration,
  View settings and key bindings remain Project-owned and unchanged.

The public assets and ZIP entry paths were checked against `release-lock.json`,
including asset SHA-256 hashes. The lock still describes the original explicit
Python installer/packaging workflow; the Host does **not** read its hashes or
receipt. Host installs are URL-cached, not checksum-pinned/authenticated installs.
ZIP CRC/expanded-byte limits and archive-level deduplication remain deferred.

## GUI startup

Run the sibling development Host from its Nix environment:

```sh
cd ../gams
nix develop --command make run GAMS_APP_CWD=../example.game1
```

Or use this Project's `make run` with the Host toolchain already active. That
recipe no longer requires `make setup-local`. First startup needs HTTPS access
for missing Units. The Host caches into ignored `gams_modules/` (or the shared
store selected by `GAMS_MODULES_DIR`) and reuses completed installs offline.
Downloaded packages retain their own license/notice files. Game compilation and
prebuilt export input preparation are unchanged and separate from Unit downloads.

## CLI integration remains explicit

The native CLI does not run the browser downloader. `make integration` and
content/export checks still need locally installed components and prebuilt game
inputs. Use `make setup-releases` for the reviewed original releases, or
`make setup-local` for sibling-built development artifacts. The helper
`scripts/local-plugin-paths.mjs` maps the known configured component URLs back to
the deployment paths in this Project's lock; it refuses unknown remote sources.
These local copies are not used by the GUI's URL-based config.

```sh
python3 -m unittest discover -s test -p 'test_*.py'
node --test test/local-plugin-paths.test.mjs
```

Node checks use the development Host's environment if Node is not installed
separately. Python installer/packaging tests remain standalone and network-free.

## Release boundary

The previous preinstalled Project packaging/Host v2.0.3 guidance is not migrated
by changing source URLs. In particular, preinstalling Units at the old local paths
does not seed the Host's new `gams_modules` cache. The current config is not an
old-Host-compatible or guaranteed first-run-offline distributed Project.

`gams.json`, documentation and tooling changes introduce intentional drift from
`NOTICE-EVIDENCE.json`; the historical evidence, approval digests and lock are
not rewritten or weakened here. A new candidate requires a separately reviewed
packaging/Host-version migration, exact source evidence refresh and approval,
and interactive desktop edit/export/play validation. No publication is authorized
by this development change.
