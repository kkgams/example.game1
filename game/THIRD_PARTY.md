# Third-party origins

The standalone game downloads build dependencies at immutable upstream commits
and validates the fetched archives before extraction:

| Dependency | Revision | Archive SHA-256 |
| --- | --- | --- |
| [`sokol-odin`](https://github.com/floooh/sokol-odin) | `9ea6ec125f002180d6cc6e7a009087ca0a019da4` | `0eebee1d50bb08f1bf44f5458d8c32d61e4c2069d73a2eddb9feeb7c04d185ba` |
| [`sokol-tools-bin`](https://github.com/floooh/sokol-tools-bin) | `11d0cf678105d614d675e6d9bd2aaf3eeff12f8c` | `c18bc3d9a52d63f385fcff9d04461e0f1c58f84102a0386acf59b6747655d17d` |

`make deps` copies each upstream `LICENSE` into `THIRD_PARTY_LICENSES/` next to
the downloaded files. `sokol-odin` uses the zlib license. The Makefile alters
its WASM foreign-import lines to link the station game's local `../../env.o`;
each altered location receives a `GAMS station demo modification` comment, as
the license requires altered source to be plainly marked. No downloaded
`sokol-tools-bin` file is modified except making the selected executable
runnable.

`web/gl-bridge.js`, `env.c`, `host/`, and `web/wasm-include/` were copied and
adapted from this repository's `examples/demo/game` infrastructure. The earliest checked-in copies of these files in the original demo game
appear in the local May 2026 game migration (commit `9990f981`, committed by
Romāns Potašovs); earlier local `plugin:game2` history also contains the
WebGL bridge. That Git record establishes a **local lineage**, not who wrote
their earliest forms or whether any external source influenced them. No
separate upstream origin or third-party license is recorded. They remain
inherited local project code of **unconfirmed original authorship**; owner
review must explicitly cover that uncertainty before distributing the optional
example-source ZIP.
