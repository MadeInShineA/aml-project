{
  description = "A very basic flake";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =

    {
      self,
      nixpkgs,
      flake-utils,
    }:

    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

      in
      {
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            uv
            python3
            ruff

            pyrefly
            nodejs
          ];

          # pip's pyrefly binary is dynamically linked and broken on NixOS;
          # replace it with the nixpkgs one (marimo still detects the pip *package*)
          shellHook = ''
            if [ -d .venv/bin ]; then
              ln -sf ${pkgs.pyrefly}/bin/pyrefly .venv/bin/pyrefly
            fi
          '';

          env.LD_LIBRARY_PATH =
            with pkgs;
            lib.makeLibraryPath [
              stdenv.cc.cc.lib
              libxcb
              libGL
              glib
            ];
        };
      }
    );
}
