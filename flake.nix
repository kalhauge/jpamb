{
  description = "JPAMB: Java Program Analysis Micro Benchmarks";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/ca77296380960cd497a765102eeb1356eb80fed0";
    jvm2json.url = "github:kalhauge/jvm2json";
    jvm2json.inputs.nixpkgs.follows = "nixpkgs";
  };
  outputs =
    {
      nixpkgs,
      jvm2json,
      ...
    }:
    let
      perSystem =
        {
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
                    uv
                    final.jvm2json
                  ];
                })
              ];
            };
          }
        );
    in
    rec {
      devShells = perSystem {
        do =
          { pkgs, ... }:
          {
            default = pkgs.mkShell {
              name = "jpamb";
              packages = pkgs.needed;
            };
          };
      };
      apps = perSystem {
        do =
          { pkgs, ... }:
          let
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
          in
          {
            image = {
              load = makeApp "load" ''
                ${detect_container}
                echo "Loading Docker image..."
                $CONTAINER_CMD load < ${packages.x86_64-linux.docker_image}
              '';
              run = makeApp "run" ''
                ${get_image_name}
                $CONTAINER_CMD run --rm "$IMAGE_NAME"\
                    -v "$(pwd):/workspace" \
                    -w /workspace \
                    $@
              '';
              jpamb = makeApp "jpamb" ''
                ${get_image_name}
                $CONTAINER_CMD run --rm "$IMAGE_NAME"\
                    -v "$(pwd):/workspace" \
                    -w /workspace \
                    uv run jpamb $@
              '';
            };
          };
      };
      packages = perSystem {
        systems = [ "x86_64-linux" ];
        do =
          { pkgs, ... }:
          {
            default = packages.docker_image;
            docker_image = pkgs.dockerTools.buildImage {
              name = "jpamb";
              tag = "latest";

              copyToRoot = pkgs.buildEnv {
                name = "jpamb-env";
                paths =
                  pkgs.needed
                  ++ (with pkgs; [
                    python3
                    bash
                    coreutils
                  ]);
              };

              config = {
                Cmd = [ "${pkgs.bash}/bin/bash" ];
                WorkingDir = "/workspace";
                Env = [
                  #  "PATH=${pkgs.jdk}/bin:${pkgs.maven}/bin:${jvm2jsonPkg}/bin:${pkgs.uv}/bin:${pkgs.python3}/bin:${pkgs.bash}/bin:${pkgs.coreutils}/bin"
                  "JAVA_HOME=${pkgs.jdk}"
                ];
              };
            };
          };
      };
    };
}
