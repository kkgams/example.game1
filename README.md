## LOCAL v0.2.0 preparation

Prospective own release only; no v0.2.0 assets are claimed public.
Public Unit pins and Host v2.0.3 visitor guidance remain unchanged.
Candidate stage/check requires separately authorized committed HEAD, exact NOTICE approval, pinned builds/receipt, cached original assets and interactive tests; all pending.

# example.game1 — abandoned station

One room, one locked exit, and a rule you can change. Play without GAMS, or open
the Project and change the door condition with the released editor. This is the
initial one-room showcase slice, not the planned full multi-room game.

## Download

The `v0.2.0` assets are created automatically after the owner pushes the reviewed
tag and CI completes: https://github.com/kkgams/example.game1/releases/tag/v0.2.0

- **Play:** `example.game1-0.2.0-web.zip` — standalone prebuilt browser game.
- **Edit:** `example.game1-0.2.0-project.zip` — complete external Project, all 18
  pinned released Project Units, retained notices, prebuilt game and source.
- Verify the downloaded ZIP against `SHA256SUMS` before extraction.

Do not install a Host from this Project; no Host binary is bundled. Download GAMS
2.0.3 separately: https://github.com/kkgams/gams/releases/tag/v2.0.3
Its current supported package is Apple Silicon macOS, ad-hoc signed/unnotarized;
follow the Host's installation/security guide rather than disabling global security.

## Play

Unpack the browser ZIP and serve its directory over static HTTP (not file://):

```sh
python3 -m http.server 8814 --directory /path/to/unpacked-web
```

Open http://localhost:8814/ in a WebGL2-capable browser. Move with WASD/arrows,
interact with E/Space, restart with R. Restore power at the switch before opening
the exit. No GAMS, Odin, Zig, Nix or game compiler is needed to play.

## Open and edit

Unpack the Project ZIP. Its `example.game1/` folder already contains the installed
Units and prebuilt game; **no setup-local, compiler, package download or Nix is
needed to open it**. Start the downloaded GAMS app and select this folder containing
`gams.json`. Python is only a convenient static server for playing exported output.

1. In Code, open `content/power.director`; initially the exit rule contains
   `IF: PLAYER.powered`.
2. Save, then press **Run** in the **Build & Export** Node Graph panel
   (`build.ng.json`). Wait for `Pipeline 'build.ng.json' completed`.
3. Serve `export/web/` with ordinary static HTTP and play the power-rule export.
4. Change only `IF: PLAYER.powered` to `IF: PLAYER.carrying_key`. Save and Run again.
5. Reload/restart the game. The exit now requires the access key, not power.

The same prebuilt WASM consumes both packs; graph execution compiles only content
through the published compiler/respack/Lua/filesystem plugins. The export copies
LICENSE, NOTICE and full third-party terms as well as the four runtime files.
Keep those documents with any redistributed export. Missing required inputs or
legal files fail the export, rather than claiming a successful partial build.

The fixed decoder/schema contract must remain unchanged for content-only edits.
`content/key.director` is a comparison fixture; the graph edits/compiles power.director.
Full game-source changes still require rebuilding with the pinned developer tools.

## Source checkout and release pins

A source checkout does not contain downloaded Unit binaries or a prebuilt game.
Python 3.10+ installs the exact reviewed public pins:

```sh
python3 scripts/install-releases.py install --lock release-lock.json
```

See [RELEASE-INSTALL.md](RELEASE-INSTALL.md). A source checkout requires the locked
Odin/Zig development shell to build its prebuilt game; use the Project ZIP for the
toolchain-free walkthrough. `make setup-local` and `make run`/`run-dev` are separate
sibling-source development commands, not the published visitor workflow.

Developer/release checks:

```sh
python3 -m unittest discover -s test -p 'test_*.py'
nix develop --no-update-lock-file --command make -C game test web
```

For source Host integration, use the documented HOST_BIN/HOST_ROOT overrides and
`make integration`. See [PUBLISHING.md](PUBLISHING.md) for candidate/tag gates.

## Licensing and evidence

Owner-controlled GAMS code: Apache-2.0. Identified upstream terms are retained in
NOTICE, THIRD-PARTY-NOTICES.txt and game/THIRD_PARTY_LICENSES/. Installed Units keep
their notices under notices/project-units/. See LICENSING.md and
THIRD-PARTY-REVIEW.md for source-level findings and disclosed provenance bounds.
RELEASE-MANIFEST.json in the Project ZIP records source/installed/web hashes;
NOTICE-EVIDENCE.json binds the prepared source/legal inputs. Packaging checks are
not a substitute for the final browser/Host walkthrough.
