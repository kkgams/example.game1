# example.game1 — station Project

Standalone source snapshot of the GAMS one-room station example, extracted from
`examples/station-demo`. The original `gams.json`, Director content, generated
fixtures, Node Graph, game source, and Project files are at this repository root.
The historical monorepo tests, built Units and export artifacts are not shipped.
This is a desktop Host development Project using the Host's present config shape,
not a released Project Config contract.

## Published installation

See [RELEASE-INSTALL.md](RELEASE-INSTALL.md) for checksum-pinned installation of
all 18 Project Units and opening this Project with the released GAMS Host. The
installer needs only Python 3; it never builds from sibling repositories or
selects a moving latest version. A complete `release-lock.json` can be collected
once all selected UI releases exist. Until then, the selection is a plan, not an
installable lock. Existing component releases are publicly available.

## Source/development workflow

Keep the `gams` Host alongside this repository (or set `HOST_ROOT` to its path).
Build its release binary first with `nix develop --command make app-build-release`
from the Host root; example integration and fixture checks invoke that binary
through `GAMS_HOST_BIN`, not a second debug Cargo build.
The local ecosystem workspace's `repositories.json` and built sibling Project
Units are required for `make setup-local`; this explicitly copies assets into
this Project, never into the Host. Build each sibling Unit first. The Host reads
this external Project via `GAMS_APP_CWD`.

```sh
nix develop --command make setup-local
nix develop --command make test
nix develop --command make web
nix develop --command make integration
nix develop --command make run
```

`make test` runs game-owned Odin tests and checks the checked-in content fixture
bytes via the sibling Host runtime. `make web` builds the visitor game; it may
fetch the pinned Sokol source/tool archives described in `game/THIRD_PARTY.md`.
`make integration` exercises the Host CLI with configured Project plugins;
`make run` opens the Host with this Project. For a Host outside `../gams`, set
`HOST_ROOT=/absolute/path/to/gams` (also accepted by the Node scripts as
`GAMS_HOST_ROOT`). `CARGO_TARGET_DIR` may be set to reuse another Cargo target.
The default is the sibling Host's `build.nosync/app/target`; `HOST_BIN` selects
its release binary if built at a different path.

The original root README contained monorepo symlink, build and test instructions
which do not apply to this independent repository. The adapted `content/README.md`
and `game/README.md` retain the source pipeline/game design notes. No public push
or binary distribution is approved by extraction; read `LICENSING.md` and
`NOTICE` first.
