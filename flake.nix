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
              in
              {
                jvm2json = inputs.jvm2json.packages.${system}.default;

                jpamb = python.pkgs.callPackage ./. { };

                docker_image = pkgs.dockerTools.buildImage {
                  name = "jpamb";
                  tag = "latest";

                  copyToRoot = pkgs.buildEnv {
                    name = "jpamb-test-env";
                    paths = [
                      pkgs.bashInteractive
                      pkgs.coreutils
                      pkgs.jdk
                      self'.packages.jvm2json
                    ];
                  };

                  config = {
                    Cmd = [ "/bin/bash" ];
                    WorkingDir = "/workspace";
                    Env = [
                      "JAVA_HOME=${pkgs.jdk}"
                    ];
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
