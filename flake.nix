{
  description = "JPAMB: Java Program Analysis Micro Benchmarks";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/ca77296380960cd497a765102eeb1356eb80fed0";
    jvm2json.url = "github:kalhauge/jvm2json";
    jvm2json.inputs.nixpkgs.follows = "nixpkgs";
  };
  outputs = {
    nixpkgs,
    jvm2json,
    self,
    ...
  }: let
    perSystem = {
      systems ? [
        "x86_64-linux"
        "x86_64-darwin"
      ],
      do,
    }:
      nixpkgs.lib.genAttrs systems (
        system:
          do {
            inherit system;
            pkgs = import nixpkgs {
              inherit system;
              overlays = [
                (final: prev: {
                  jvm2json = jvm2json.packages.${system}.default;
                })
              ];
            };
          }
      );
  in {
    packages =
      perSystem {
        do = {pkgs, ...}: {
          jvm2json = pkgs.jvm2json;
        };
      }
      // perSystem {
        systems = ["x86_64-linux"];
        do = {pkgs, ...}: let
          pythonWithPackages = pkgs.python313.withPackages (ps:
            with ps; [
              pytest
              hypothesis
              click
              loguru
              matplotlib
              tree-sitter
              tree-sitter-grammars.tree-sitter-java
              z3-solver
              z3
            ]);
        in {
          docker_image = pkgs.dockerTools.buildImage {
            name = "jpamb";
            tag = "latest";

            copyToRoot = pkgs.buildEnv {
              name = "jpamb-test-env";
              paths = [
                pkgs.bashInteractive
                pkgs.coreutils
                pkgs.jdk
                pythonWithPackages
                pkgs.jvm2json
              ];
            };

            config = {
              Cmd = ["/bin/bash"];
              WorkingDir = "/workspace";
              Env = [
                "JAVA_HOME=${pkgs.jdk}"
              ];
            };
          };
        };
      };
  };
}
