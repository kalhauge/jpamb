{
  description = "JPAMB: Java Program Analysis Micro Benchmarks";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs";
    flake-parts.url = "github:hercules-ci/flake-parts";

    jvm2json.url = "github:kalhauge/jvm2json";
    jvm2json.inputs.nixpkgs.follows = "nixpkgs";

    runit.url = "github:kalhauge/runit";
    runit.inputs.nixpkgs.follows = "nixpkgs";
    runit.inputs.ash.follows = "ash";
    runit.inputs.flake-parts.follows = "flake-parts";

    ash.url = "github:kalhauge/a.sh";
    ash.inputs.nixpkgs.follows = "nixpkgs";
    ash.inputs.flake-parts.follows = "flake-parts";
  };

  outputs =
    inputs@{ flake-parts, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } (
      top@{
        self,
        lib,
        config,
        ...
      }:
      {
        imports = [
          inputs.ash.flakeModules.default
        ];

        flake = {
          # Your flake goes here
          pythonOverlays.default = lib.composeManyExtensions [
            (pyfinal: pyprev: {
              jpamb = pyfinal.callPackage ./. { doCheck = false; };
            })
            inputs.runit.pythonOverlays.default
          ];
        };

        perSystem =
          {
            config,
            pkgs,
            system,
            self',
            ...
          }:
          {
            ash = {
              enable = true;
              configuration = {
                languages = {
                  git.enable = true;
                  markdown.enable = true;
                  nix.enable = true;
                  python.enable = true;
                  yaml.enable = true;
                  java.enable = true;
                  c.enable = true;
                };
              };
            };

            packages =
              let
                python = pkgs.python3.override {
                  self = python;
                  packageOverrides = self.pythonOverlays.default;
                };
              in
              {
                jpamb = python.pkgs.jpamb;
              };

            devShells = {
              default = pkgs.mkShell {
                name = "jpamb";
                nativeBuildInputs = [
                  pkgs.ruff
                  pkgs.uv
                ];
              };
            };

            checks = {
              jpamb = self'.packages.jpamb.override { doCheck = true; };

              ruff =
                pkgs.runCommandLocal "ruff-check"
                  {
                    nativeBuildInputs = [ pkgs.ruff ];
                  }
                  ''
                    cd ${self}
                    ruff check --no-cache 
                    ruff format --no-cache --check 
                    touch $out
                  '';
            };

          };
        systems = [
          "x86_64-linux"
          "aarch64-linux"
          "aarch64-darwin"
        ];
      }
    );
}
