{
  description = "Station example Project development environment";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  outputs = { nixpkgs, ... }:
    let
      systems = [ "aarch64-darwin" "x86_64-darwin" "x86_64-linux" "aarch64-linux" ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
    in {
      devShells = forAllSystems (system:
        let pkgs = nixpkgs.legacyPackages.${system};
        in {
          default = pkgs.mkShell {
            name = "example-game1-dev";
            nativeBuildInputs = with pkgs; [ rustc cargo cargo-tauri libiconv pkg-config python3 nodejs cacert odin zig curl gnutar gzip perl ];
          };
        });
    };
}
