# Station showcase Director content

This directory owns the author-facing one-room puzzle rules and their fixed
Director-to-RSPK contract. The standalone game contract is
[`../game/CONTRACT.md`](../game/CONTRACT.md).

## Variants

- `power.director` is the initial walkthrough: interacting with `EXIT` unlocks
  it only after `PLAYER.powered` is set by `POWER_SWITCH`.
- `key.director` changes only that prerequisite to `PLAYER.carrying_key`.
- Both keep switch activation, idempotent key pickup/removal, and the
  `EXIT.-locked` effect in Director. The game has no power-versus-key branch.

The sources intentionally use the currently implemented IR only: entity/tag
matchers, conditions, entity removal, tag addition, and generic property
removal. Structured value paths are documented v1 work but are not implemented
by the current runtime/schema, so compiler placeholder `value_paths` and
`path_steps` arrays are explicitly excluded before packing.

## Developer compile -> bind -> pack proof

From the repository root:

```sh
nix develop --command make setup-local
nix develop --command node content/build.mjs
```

`build.mjs` invokes the real singleton compiler and respack components through
the CLI runtime. It validates IR pool ranges, resolves every game-facing value
from compiler `symbols` metadata, removes metadata from runtime slot 0, and
writes both packs under `content/generated/`. No numeric compiler ID is authored
in source or build configuration.

Generated evidence per variant:

- `*.director.json` — implemented five-pool Director runtime IR;
- `*.bindings.json` — resolved `(kind, name, value)` records required by the game;
- `*.slots.json` — exact two-slot respack input;
- `*.rspk` — standalone RSPK v1 content;
- `decoder.odin` — raw checked-in decoder output generated from
  `director.rspk.json` for pipeline tests.

These are committed deterministic fixtures, not alternate authored sources.
After intentional source/schema/tool changes, regenerate and review them with:

```sh
nix develop --command node content/build.mjs --generate-decoder
```

CI-style verification is non-mutating and fails on any fixture drift, including
the generated decoder:

```sh
nix develop --command node content/build.mjs --check --generate-decoder
```

Decoder regeneration is a game-development/schema-change operation, not part of
the visitor workflow. The game decoder's generation/custom-validation boundary
is documented beside that source in `game/content/README.md`; the raw fixture
here is not copied over the hardened game decoder.

The content-only path calls `build.mjs` without that flag, or uses the Lua
presets in `../ng/presets/`. In particular,
`respack-content-save.lua` only packs/writes data and cannot regenerate game
source. The already compiled game decoder therefore remains stable across both
variants.

## Tests and visitor game

The former cross-Project pipeline and Odin matrix tests were monorepo tests, not included here. After `make setup-local`, run `make test` for game-owned tests and deterministic fixture drift checking. Run `make web` to build the visitor game; `make -C game serve` serves it.

## Schema and failure behavior

`director.rspk.json` has exactly two non-empty slots:

1. the implemented `director.Director_Data` field layout;
2. `station.Bindings`, a vector of named entity/word/rule bindings matching
   `game/CONTRACT.md`.

RSPK magic/version/slot count, enum values, all ranges/references, contiguous
entity IDs, duplicate bindings, and required bindings are validated by the game
loader. Missing compiler symbols, malformed source, malformed IR, or respack
errors abort generation; no fallback IDs or old-pack success is reported.

## Verification record

The original monorepo validation record is not evidence of validation of this standalone extraction. Run the targets described in the root README in an assembled workspace.

## Remaining limitations

- `build.mjs` is developer evidence and uses repository Cargo/Nix tooling. The
  visitor workflow invokes the same compiler/respack Project Units from GAMS
  through the checked-in Node Graph and Lua presets; it does not run this Node
  script.
- Export assembly is exercised by the Project graph, but browser automation is
  not implemented. Serving and browser play remain explicit manual checks.
- The schema has no independent fingerprint field because the implemented RSPK
  format provides magic, version, and slot count only. Compatibility is enforced
  structurally and by required named bindings in the prebuilt game decoder.
