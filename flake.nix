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
                  needed = with final; [
                    jdt-language-server
                    jdk
                    maven
                    final.jvm2json
                  ];
                  jpamb = final.callPackage ./build.nix {inherit self;};
                })
              ];
            };
          }
      );
  in rec {
    apps = perSystem {
      do = {pkgs, ...}: let
        detect_container = ''
          if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
              CONTAINER_CMD="docker"
          elif command -v podman >/dev/null 2>&1; then
              CONTAINER_CMD="podman"
          else
              echo "Error: Neither docker nor podman is available"
              exit 1
          fi
        '';
        get_image_name = ''
          ${detect_container}
          IMAGE_NAME=$($CONTAINER_CMD images --format "{{.Repository}}:{{.Tag}}" | grep jpamb | head -1)
          if [ -z "$IMAGE_NAME" ]; then
              echo "No jpamb image found. Run 'nix run .#image.load' first."
              exit 1
          fi
        '';
        makeApp = name: script: {
          type = "app";
          program = "${pkgs.writeShellScript name script}";
        };
      in {
        image = rec {
          type = "app";
          program = load.program;

          load = makeApp "load" ''
            ${detect_container}
            echo "Loading Docker image..."
            $CONTAINER_CMD load < ${packages.x86_64-linux.docker_image}
          '';
          run = makeApp "run" ''
            ${get_image_name}
            set -x
            $CONTAINER_CMD run --rm \
                -v "$(pwd):/workspace" \
                -w /workspace \
                "$IMAGE_NAME" \
                $@
          '';
          jpamb = makeApp "jpamb" ''
            ${get_image_name}
            $CONTAINER_CMD run --rm \
                -v "$(pwd):/workspace" \
                -w /workspace \
                "$IMAGE_NAME" \
                jpamb $@
          '';

          test = makeApp "test" ''
            ${get_image_name}
            echo "Running jpamb test suite in Docker (using pre-built image)..."
            $CONTAINER_CMD run --rm \
                "$IMAGE_NAME" \
                bash -c "cd /workspace && mvn compile && python -m pytest test/ -v -m 'not slow'"
          '';

          test-all = makeApp "test-all" ''
            ${get_image_name}
            echo "Running full jpamb test suite in Docker (including slow tests)..."
            $CONTAINER_CMD run --rm \
                "$IMAGE_NAME" \
                bash -c "cd /workspace && mvn compile && mvn test && python -m pytest test/ -v"
          '';

          test-java = makeApp "test-java" ''
            ${get_image_name}
            echo "Running Java tests in Docker..."
            $CONTAINER_CMD run --rm \
                "$IMAGE_NAME" \
                bash -c "cd /workspace && mvn test"
          '';

          test-python = makeApp "test-python" ''
            ${get_image_name}
            echo "Running Python tests in Docker..."
            $CONTAINER_CMD run --rm \
                "$IMAGE_NAME" \
                bash -c "cd /workspace && python -m pytest test/ -v -m 'not slow'"
          '';
        };
      };
    };
    packages =
      perSystem {
        do = {pkgs, ...}: {
          default = pkgs.jpamb;
          inherit (pkgs) jpamb jvm2json;
        };
      }
      // perSystem {
        systems = ["x86_64-linux"];
        do = {pkgs, ...}: let
          pythonWithPackages = pkgs.python313.withPackages (ps: with ps; [
            pytest
            hypothesis
            click
            pyyaml
            loguru
            matplotlib
            tree-sitter
            tree-sitter-grammars.tree-sitter-java
            z3-solver
            z3
          ]);

          # Bundle source files for testing
          testBundle = pkgs.runCommand "jpamb-test-bundle" {} ''
            mkdir -p $out/workspace
            cp -r ${self}/test $out/workspace/
            cp -r ${self}/src $out/workspace/
            cp -r ${self}/stats $out/workspace/
            cp -r ${self}/decompiled $out/workspace/
            cp -r ${self}/solutions $out/workspace/
            cp ${self}/pom.xml $out/workspace/
          '';
        in {
          docker_image = pkgs.dockerTools.buildImage {
            name = "jpamb";
            tag = "latest";

            copyToRoot = pkgs.buildEnv {
              name = "jpamb-test-env";
              paths = [
                pkgs.bash
                pkgs.coreutils
                pkgs.maven
                pkgs.jdk
                pythonWithPackages
                pkgs.jpamb
                testBundle
              ];
            };

            config = {
              Cmd = ["/bin/jpamb"];
              WorkingDir = "/workspace";
              Env = [
                "JAVA_HOME=${pkgs.jdk}"
                "PYTHONPATH=${pkgs.jpamb}/${pkgs.python313.sitePackages}"
              ];
            };
          };
        };
      };
  };
}
