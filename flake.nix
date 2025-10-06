{
  description = "JPAMB: Java Program Analysis Micro Benchmarks";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/ca77296380960cd497a765102eeb1356eb80fed0";
    flake-utils.url = "github:numtide/flake-utils";
    jvm2json.url = "github:kalhauge/jvm2json";
    jvm2json.inputs.nixpkgs.follows = "nixpkgs";
  };
  outputs =
    {
      nixpkgs,
      flake-utils,
      jvm2json,
      ...
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs { inherit system; };
        jvm2jsonPkg = jvm2json.packages.${system}.default;
        basePackages = with pkgs; [
          jdt-language-server
          jdk
          maven
          uv
        ];
        allPackages = basePackages ++ [ jvm2jsonPkg ];
      in
      {
        devShells = {
          default = pkgs.mkShell {
            name = "jpamb";
            packages = allPackages;
          };
        };

        packages = {
          default = pkgs.dockerTools.buildImage {
            name = "jpamb";
            tag = "latest";

            copyToRoot = pkgs.buildEnv {
              name = "jpamb-env";
              paths = allPackages ++ (with pkgs; [
                python3
                bash
                coreutils
              ]);
            };

            config = {
              Cmd = [ "${pkgs.bash}/bin/bash" ];
              WorkingDir = "/workspace";
              Env = [
                "PATH=${pkgs.jdk}/bin:${pkgs.maven}/bin:${jvm2jsonPkg}/bin:${pkgs.uv}/bin:${pkgs.python3}/bin:${pkgs.bash}/bin:${pkgs.coreutils}/bin"
                "JAVA_HOME=${pkgs.jdk}"
              ];
            };
          };
        };
      }
    );
}
