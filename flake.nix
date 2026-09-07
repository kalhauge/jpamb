{
  description = "JPAMB: Java Program Analysis Micro Benchmarks";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/ca77296380960cd497a765102eeb1356eb80fed0";
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
      top@{ self, config, ... }:
      {
        imports = [
          inputs.ash.flakeModules.default
          ./autolab
        ];

        flake = {
          # Your flake goes here
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
                  packageOverrides = inputs.runit.pythonOverlay.default;
                };
                jpamb = python.pkgs.callPackage ./. { };

              in
              rec {
                inherit jpamb;

                docker_image = pkgs.dockerTools.buildImage {
                  name = "jpamb";
                  tag = "latest";

                  copyToRoot = pkgs.buildEnv {
                    name = "jpamb";
                    paths = [
                      pkgs.coreutils
                      pkgs.gnumake
                      (python.withPackages (py: [
                        py.pip
                        py.click
                        py.runit
                        py.setuptools
                      ]))
                    ];
                  };

                  config = {
                    Cmd = [ "${pkgs.bashInteractive}/bin/bash" ];
                    WorkingDir = "/workspace";
                    Env = [ ];
                  };
                };
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
