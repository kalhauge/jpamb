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

                autodriver = pkgs.stdenv.mkDerivation {
                  name = "autodriver";
                  src = pkgs.fetchFromGitHub {
                    owner = "autolab";
                    repo = "Tango";
                    rev = "24558e3db2be78831d00cc2b56579be205dc6e4b";
                    sha256 = "sha256-gabBfNnNnDGcwxEJi5MW+uz5I2gcvOmOloeYo74wmVE=";
                  };

                  preConfigure = ''
                    ls -l
                    cd autodriver
                  '';

                  buildPhase = ''
                    gcc -W -Wall -Wextra   -c -o autodriver.o autodriver.c
                    gcc  -o autodriver autodriver.o
                  '';

                  installPhase = ''
                    mkdir -p $out/bin
                    cp autodriver $out/bin/
                  '';
                };
              in
              rec {
                inherit jpamb autodriver;

                docker_image = pkgs.dockerTools.buildLayeredImage {
                  name = "autograder_02242_e26_v2";
                  tag = "latest";

                  contents = [
                    pkgs.coreutils
                    pkgs.gnumake
                    pkgs.bashInteractive
                    autodriver
                    (python.withPackages (py: [
                      py.pip
                      py.click
                      py.runit
                      py.setuptools
                    ]))
                  ];

                  enableFakechroot = true;

                  fakeRootCommands = ''
                    mkdir -p /home/autolab /home/autograde /home/output /etc

                    echo "autolab:x:1000:" >> /etc/group
                    echo "auotlab:x:1000:1000:Autolab:/autolab:/bin/bash" >> /etc/passwd

                    echo "autograde:x:1001:" >> /etc/group
                    echo "auotgrade:x:1001:1001:Autograde:/autograde:/bin/bash" >> /etc/passwd

                    # Set ownership
                    chown -R 1000:1000 /home/autolab
                    chown -R 1000:1000 /home/output
                    chown -R 1001:1001 /home/autograde
                  '';

                  config = {
                    # WorkingDir = "/home";
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
