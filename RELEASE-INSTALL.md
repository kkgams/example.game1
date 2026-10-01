# Run example.game1 with released Project Units

This path installs packages into this **external Project**, not into GAMS and not
from sibling source builds. It requires Python 3.10+ and public HTTPS access;
no Nix, Node/npm, Cargo, Odin, shared SDK checkout, or sibling workspace is needed
for package installation or opening the existing Project in the downloaded GUI.
`make setup-local` remains the separate, unchanged source-development path.

## Publication readiness (public API observation)

The public `https://api.github.com/repos/kkgams/<repo>/releases` endpoints were
queried during implementation. The explicit selections in `release-selection.json`
record the observed component releases, **not** a mutable latest resolver:

| Unit | Selected version/tag | Observed public assets |
| --- | --- | --- |
| plugin.fs | 0.1.1 / v0.1.1 | plugin.fs.wasm, LICENSE, NOTICE, SHA256SUMS |
| plugin.layout | 0.1.0 / v0.1.0 | plugin.layout.wasm, LICENSE, NOTICE, SHA256SUMS |
| plugin.lua | 0.1.0 / v0.1.0 | plugin.lua.wasm, LICENSE, NOTICE, SHA256SUMS |
| plugin.respack | 0.1.0 / v0.1.0 | plugin.respack.wasm, LICENSE, NOTICE, SHA256SUMS |
| plugin.director-compiler | 0.1.0 / v0.1.0 | director-compiler.wasm, LICENSE, NOTICE, SHA256SUMS |

For all thirteen UI repositories (`view.files`, `view.code`, `view.ng`,
`view.ng-node`, `view.files-rename`, `view.files-default`, `ui-service.context`,
`ui-service.keys`, `ui-service.layout`, `ui-service.toast`, `ui-service.popup`,
`ui-service.tooltip`, `theme.the98`), the public release API returned **404**.
Their v0.1.0 selections are **planned-not-ready**; a source push, private repo,
or CI candidate is not evidence of a public released asset. No complete
`release-lock.json` or fake digests are shipped. Until these packages are public,
the release installation path deliberately cannot complete. Recheck explicit
selected tags with the review command after owner-approved publication.

The compiler's currently published filename is `director-compiler.wasm`, unlike
the other four `plugin.<slug>.wasm` assets. Its Project destination remains
`plugins/director-compiler.comp.wasm`. Every component retains its original
`plugins/<slug>.comp.wasm` destination. UI deployment filenames (including
`views/files-rename.js` and `views/files-default.js`) are not repository/config ids.

## Owner: generate and review a complete lock

Review `LICENSING.md`, each Unit's LICENSE/NOTICE and release provenance first.
Extraction/install code does not grant redistribution approval. In particular,
UI licensing and theme embedded artwork require owner decisions; do not create
releases merely to unblock this installer.

Select explicit versions/tags in `release-selection.json`, then:

```sh
python3 scripts/install-releases.py build-lock \
  --selection release-selection.json --output release-lock.review.json
```

This separate command queries **only those explicit tags** through the public
GitHub API, rejects drafts, prereleases, absent publication timestamps and duplicate
asset names, requires every named release asset, downloads and hashes all assets,
checks the sidecars, validates actual archives, and writes the lock only when the
whole set succeeds. It never installs, publishes, tags, or changes credentials.
It refuses an existing output. Review the resulting URLs, versions, digests,
LICENSE/NOTICE and upstream provenance; only then rename the reviewed file to
`release-lock.json` and distribute it with the Project. SHA256SUMS is an integrity
cross-check, not an independent signature; the reviewed lock is the trust anchor.
The selection `status` is an observation, not an approval bypass.

Lock schema 1 contains exactly eighteen distinct `units`; each record contains:
`name`, `kind`, distribution `version`, exact `tag` (`v` + version), `files` (the
exact Project-relative deployment list), and `assets`. Each asset filename maps
to `{ "url": "https://github.com/kkgams/<repo>/releases/download/<tag>/<asset>",
"sha256": "<64 lowercase hexadecimal characters>" }`. This description is not
a usable lock: placeholders, absent fields and incomplete sets fail installation.
`SHA256SUMS` itself is pinned too. Arbitrary hosts, tags, source trees, API asset
URLs, dynamic latest coordinates and mutable branch downloads are rejected.

## Install and open the downloaded GUI

After receiving a reviewed, complete lock alongside the example source:

```sh
cd /absolute/path/to/example.game1
python3 scripts/install-releases.py install --lock release-lock.json
```

Download **GAMS 2.0.3** from its public tagged release (if published):
`https://github.com/kkgams/gams/releases/tag/v2.0.3`. Choose the supported platform
package and verify its release checksum using the Host's published instructions;
source version, a successful push or CI candidate is not proof of publication.
On macOS install/open the downloaded `GAMS.app`; choose the example.game1 folder
containing `gams.json` in its external-Project picker. Alternatively:

```sh
GAMS_APP_CWD=/absolute/path/to/example.game1 \
  /Applications/GAMS.app/Contents/MacOS/gams
```

No Project files or Units need copying into the app bundle. The Host supplies
its own `/core`, `/util`, `/widgets`, DOM and font APIs; this installer adds no npm
packages or invented shared SDK dependency. This installs the editing/content
Project, **not** a built visitor game. Building/rebuilding game source (`make web`,
Odin tests and related content pipelines) still requires the documented game
compiler/toolchain and reviewed pinned Sokol downloads; package installation does
not remove those toolchain requirements. Existing checked-in fixtures stay intact.

## Archive and safety contract

A UI release has `<repo>-<version>.zip` and a `SHA256SUMS` sidecar covering that
ZIP. Its ZIP contains only the deployed JS/CSS paths at its root (`src/` removed),
`unit.json`, `LICENSE`, `NOTICE`, `README.md`. `unit.json` contains exactly `name`,
`kind`, `version`, `entry`, `files` mapping each deployed path to its SHA-256, and
`host`. The entry must equal the installer’s explicit Unit deployment mapping;
`host` must contain exactly `target` (`2.0.3`) and a string `note`. This records a
Host **source contract target**, not tested GUI compatibility or a minimum-version
guarantee. Package-level downloaded-GUI validation remains an owner release gate.
No parent archive wrapper, directory entries, extra source/dependency files or
symlinks are accepted. Component release sidecars cover the WASM, LICENSE and
NOTICE assets.

Installer schema v1 deliberately permits exactly one deployed entry per Unit.
The current thirteen UI source closures each contain only that entry. Although the
producer supports recursive local source closures, a future multi-file Unit must
receive an explicit reviewed installer mapping/schema change before installation;
archives cannot silently expand their allowed Project paths.

All downloads and mapped file bytes are verified and staged in bounded memory
before any Project mutation. ZIP names, duplicates, special files, encryption,
compression/size limits, unit identity and exact deployment mappings are checked;
untrusted archives are never extracted wholesale. Limits: 32 MiB per download
and per expanded ZIP, 128 ZIP members, 200:1 compression ratio, 256 MiB overall
staged payloads. Existing symlink destinations/parents and conflicting filesystem
types fail preflight. Install into a trusted Project not being concurrently edited
by another process. Repeat installation refreshes the owned paths; unrelated
files are not deleted. Individual file replacements are atomic, but OS/disk
failures during writing are **not** a whole-Project transaction; restore a backup
or rerun after resolving such failures.

Per-Unit licensing bytes remain under `notices/project-units/<repo>/`; UI README
and unit metadata are retained there too. `build.nosync/release-install.json`
records pinned URLs, source digests, versions/tags, canonical lock digest and all
installed file hashes. Download/checksum/validation failures leave the Project
unchanged (no receipt or notices written on failure).

## Generator wiring

`packaging/ecosystem/example_game1.py::prepare` already copies the entire template
with `copy_real_tree(TEMPLATE, stage)`. The new script, selection and this document
therefore land in generated example.game1 automatically; no generator, Makefile,
existing README or setup-local edits are needed. A reviewed release-lock.json can
be supplied with the distributed Project after publication review. Generator
extraction tests verify these template bytes are retained. An offline integration
regression generates the real thirteen UI repositories, stages each with its own
release producer and exact-byte LICENSE/NOTICE digest approvals, then installs
those actual archives alongside five WASM fixtures. It compares deployed UI
bytes directly with monorepo sources and retained notices with generated originals,
including the theme’s complete upstream MIT terms. This checks packaging and
installation, not GUI behavior or public publication readiness.
