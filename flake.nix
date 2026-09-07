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
                jpamb = python.pkgs.callPackage ./. { };

              in
              rec {
                inherit jpamb;

                grader = pkgs.runCommand "grader.tar" { } ''
                  mkdir lab
                  chmod a+rw -R lab
                  ${pkgs.gnutar}/bin/tar -cf $out lab
                '';

                syntactic =
                  let
                    config = {
                      autograder = {
                        autograde_image = "autograding_image";
                        autograde_timeout = 180;
                        release_score = true;
                      };
                      dates = {
                        due_at = "2026-09-13 23:59:59 +0200";
                        end_at = "2026-09-30 11:53:32 +0200";
                        start_at = "2026-09-08 11:53:32 +0200";
                      };
                      general = {
                        allow_student_assign_group = true;
                        category_name = "Syntactic";
                        disable_network = true;
                        display_name = "Syntactic Assignment";
                        github_submission_enabled = true;
                        group_size = 1;
                        handin_directory = "handin";
                        handin_filename = "report.sexp";
                        is_positive_grading = false;
                        max_grace_days = 0;
                        max_size = 2;
                        max_submissions = -1;
                      };
                      problems = [
                        {
                          name = "Total";
                          max_score = 70 * 6;
                          description = "The total score";
                          optional = false;
                          started = false;
                        }
                      ];
                    };
                  in
                  pkgs.runCommand "syntactic-assign.tar"
                    {
                      buildInputs = with pkgs; [ yj ];
                      json = builtins.toJSON config;
                    }
                    ''
                      NAME=syntactic-assign
                      mkdir $NAME
                      cp ${./autolab/syntactic}/autograde-Makefile $NAME
                      cp ${grader} $NAME/autograde.tar
                      cp ${./autolab/syntactic}/syntactic.rb $NAME/$NAME.rb
                      cp ${./autolab/syntactic}/scoreboard.json $NAME
                      echo "$json" | yj -jy > $NAME/$NAME.yml
                      chmod a+rw -R $NAME
                      ${pkgs.gnutar}/bin/tar -cf $out $NAME
                    '';

                docker_image = pkgs.dockerTools.buildImage {
                  name = "jpamb";
                  tag = "latest";

                  copyToRoot = pkgs.buildEnv {
                    name = "jpamb";
                    paths = [
                      pkgs.coreutils
                      pkgs.gnumake
                      jpamb
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
