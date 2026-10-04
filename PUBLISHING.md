## LOCAL v0.2.0 preparation

Prospective own release only; no v0.2.0 assets are claimed public.
Public Unit pins and Host v2.0.3 visitor guidance remain unchanged.
Candidate stage/check requires separately authorized committed HEAD, exact NOTICE approval, pinned builds/receipt, cached original assets and interactive tests; all pending.

# Publishing example.game1 v0.2.0

Canonical repository: `kkgams/example.game1`. The publishing repository must exist;
this template neither creates it nor performs Git operations on your behalf.
Commit the standalone extraction, reviewed `release-lock.json`, full upstream
license texts, and `NOTICE-EVIDENCE.json` before preparing a candidate. Do not
copy monorepo tests into this repository: `test/test_release.py` contains only
stdlib standalone installer/packaging tests.

## Approval gates

GAMS-authored code is Apache-2.0 by owner authorization. That authorization is
not proof of exact application provenance or ownership of upstream code. Audit
all retained source, generated fixture/build inputs, upstream documentation and
license texts. Evidence must contain a nonempty `files_sha256` object using
Project-relative paths and lowercase SHA-256 hashes. Cover every packaged tracked
source except LICENSE, NOTICE, NOTICE-EVIDENCE.json and the historical SOURCE.json
snapshot record. Include `game/THIRD_PARTY.md` and full license files beneath
`game/THIRD_PARTY_LICENSES/`. Additional audited build inputs are checked in place;
never bind a macOS-built WASM digest as the expected Linux-built WASM digest.

NOTICE must include `NOTICE-EVIDENCE.json SHA-256: <digest>` binding the exact
committed audit bytes. Set repository variables `LICENSE_SHA256` and
`NOTICE_SHA256` to the owner-reviewed texts. The packager requires the corresponding
`APPROVED_LICENSE_SHA256` and `APPROVED_NOTICE_SHA256` environment variables for
both stage and check. Missing evidence, pending provenance, changed source,
incomplete lock, invalid installed receipt or missing prebuilt WASM fails closed.

## Independent preparation (no sibling Host)

```sh
python3 -m unittest discover -s test -p 'test_*.py'
nix develop --no-update-lock-file --command odin version
nix develop --no-update-lock-file --command make --trace -C game test web
nix develop --no-update-lock-file --command python3 scripts/build-receipt.py dist/proof/build-receipt.json
python3 scripts/release.py install --lock release-lock.json
python3 scripts/release.py stage --tag v0.2.0
python3 scripts/release.py check --tag v0.2.0
```

`release.py install` calls the stdlib `install-releases.py` installation API with
a transport that preserves original public release bytes in
`build.nosync/release-assets/<SHA256-of-URL>`. All 18 Units must already have public,
immutable, hash-pinned releases. The normal `make setup-releases` command remains
available, but does not preserve this verifier cache; use `release.py install`
for packaging. Final stage/check never download: they re-run the installer's
complete validate/stage pipeline against cached originals, then compare every
installed file and the exact receipt. No reconstructed ZIP or receipt-only trust.
`install --offline` restores installed files from those same pinned cached bytes.

The checked-in Nix lock is not updated. Linux and Darwin shells are supported;
this is not a promise that independently compiled WASM is byte-identical between
operating systems. ZIPs are deterministic for identical source/selected inputs.
Game compilation needs Odin/Zig; visitors editing/exporting the downloaded Project
do not. No npm install, Node tests, native game build, sibling sources or Host
binary is used by release CI. Root `run` stays the developer Host command;
`run-dev` is only an alias, not the visitor launch workflow.

## Download layout

- `example.game1-0.2.0-project.zip`: rooted `example.game1/`; committed Project
  source/tooling/readmes, release lock, installed Units/notices, exact installation
  receipt, `RELEASE-MANIFEST.json` with source/installed/web hashes, and
  `BUILD-RECEIPT.json` with actual selected tools/source/output hashes.
- Its prebuilt content-only export inputs are exactly
  `game/build.nosync/web/{index.html,gl-bridge.js,station-demo.wasm,station.rspk}`.
  Project Config relative paths and source mappings are unchanged.
- `example.game1-0.2.0-web.zip`: flat four web files, LICENSE, NOTICE, README.md,
  with full `THIRD-PARTY-NOTICES.txt`, a browser-specific README, and bound
  NOTICE-EVIDENCE.json/individual game upstream license texts under `UPSTREAM-NOTICES/`. Serve the extracted folder with static HTTP hosting.
- `SHA256SUMS` covers both ZIPs and the LICENSE/NOTICE release attachments.

Only explicit git-tracked committed source is packaged; no `.git`, `.github`,
node_modules, arbitrary build output, downloaded Sokol sources, dist or temporary
files. Exceptions are the validated installed receipt and four selected web
inputs. No Host binaries are bundled. Install/run the separately released Host
according to the Project README; a public Project artifact is not a Host bundle.

## CI and publication

PRs run standalone Python tests. Release-branch candidates build only when both
approval variables are set. Tags independently compile/test the browser game,
install pinned public Units, stage and check; they never reuse branch binaries.
Both pinned checkout actions fetch full history. The pinned Nix installer matches
the Host workflow. CI retains `odin-version.txt` and `game-build.txt` alongside
Zig version, actual build receipt, exact cached upstream assets and prebuilt web inputs in a separate verifier
artifact; these are build evidence, not proof of interactive browser gameplay or
legal ownership, and are not public release attachments.

Publication downloads candidate and verifier artifacts, installs offline, and
checks candidate bytes against committed source and verified pins before release
creation. The tag, semver, repository identity, workflow SHA and current `release`
HEAD must agree. An existing release is immutable: only an authenticated 404
allows creation; network/auth/server errors fail closed. The public release has
the two ZIPs, SHA256SUMS, LICENSE and NOTICE. No Pages deployment yet. The user
remains responsible for GitHub permissions, committing, pushing, and tagging.

A successful packaging check does not replace the clean-machine interactive
Host edit/export/play walkthrough or browser game smoke test required by PRD0015.
