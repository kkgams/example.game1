# Published Project Unit installation

The current source `gams.json` now uses release URLs with the development Host;
see [PROJECT-SOURCES.md](PROJECT-SOURCES.md). The Python installer below remains
the separate CLI/packaging workflow and does not seed `gams_modules`. Its older
preinstalled-Project/Host v2.0.3 visitor guidance requires migration before a new
Project candidate can be published.

The complete release-lock.json records **18 public releases and 46 exact asset
pins**. FS is v0.1.1; the other four WASM plugins and all thirteen UI Units are
v0.1.0. These selected versions do not change automatically. Their GitHub release
ZIP/component bytes, SHA256SUMS, metadata and notices were downloaded and verified
before collecting this lock. Public URLs are a requirement; authenticated-only
private-repository downloads are not a usable visitor dependency.

## Visitor

The Project ZIP already contains every installed Unit, per-Unit notice, an install
receipt and the prebuilt game. Open its example.game1 folder with the separately
released GAMS 2.0.3 app. No installation/build toolchain is needed for GUI edits.

For a source checkout or to refresh installed Units, Python 3.10+ and HTTPS suffice:

```sh
python3 scripts/install-releases.py install --lock release-lock.json
```

The installer checks all downloads and archive metadata before changing Project
files. It installs only the declared original Project-relative paths, retaining
per-Unit LICENSE/NOTICE under notices/project-units/. It never downloads latest,
substitutes sibling source, installs npm packages or copies Units into the Host.
It refreshes owned files without deleting unrelated data. Individual writes are
atomic, not a transaction against disk/OS failure. Use a trusted Project folder
without concurrent filesystem edits.

The compiler's asset is director-compiler.wasm; its deployed Project path remains
plugins/director-compiler.comp.wasm. UI filenames/config ids also remain separate
from repository names. All thirteen UI closures currently contain one entry each;
future multi-file packages require an explicitly reviewed installer mapping change.

## Maintainer: collect a new lock

Change explicit release-selection.json versions only deliberately, then collect a
new review file (existing output is never overwritten):

```sh
python3 scripts/install-releases.py build-lock --output release-lock.review.json
```

Review the public tagged releases, bytes, notices, versions and hashes before
replacing/committing release-lock.json. Lock collection is a separate review step,
not trust-on-first-use during every install. SHA256SUMS is an integrity cross-check,
not an independent signature; committed reviewed lock pins are the trust anchor.
Drafts/prereleases/missing assets/API errors fail; no incomplete lock is written.

## Release builder

`python3 scripts/release.py install --lock release-lock.json` preserves downloaded
originals in build.nosync/release-assets/ for independent offline packaging checks.
The CI build runs the locked game toolchain separately, packages the installed
Units plus prebuilt export inputs, and keeps Host binaries out of both ZIPs.
The source checkout's `make setup-local` is development-only and must not be used
to assemble the published release.

Installer safety: exact known HTTPS asset URLs, all SHA pins and sidecars, bounded
ZIP expansion/member counts, duplicate/traversal/symlink/special-file rejection,
strict Unit metadata and mapped file hashes. Limits: 32 MiB/download or expanded
ZIP, 128 members, 200:1 compression ratio, 256 MiB total staged bytes. Validated
archives are read member-by-member, never extracted wholesale. No receipt or
Project files are written on network/checksum/validation failure.

See README.md for the power-to-key edit/export/play walkthrough. Source game
rebuilding still needs Odin/Zig/Nix; installing packages does not erase that
requirement. The downloaded prebuilt Project is the toolchain-free editing path.
