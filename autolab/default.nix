{ self, lib, ... }:

{
  perSystem =
    {
      config,
      pkgs,
      self',
      ...
    }:
    let
      autograder = pkgs.runCommand "autograder.tar" { } ''
        cp -r ${self} jpamb
        chmod a+rw -R jpamb
        ${pkgs.gnutar}/bin/tar -cf $out jpamb
      '';
      mkAssignment =
        file:
        let
          evaluated = lib.evalModules {
            modules = [
              ./module.nix
              file
            ];
          };
          config = evaluated.config;
        in
        pkgs.runCommand "${config.name}.tar"
          {
            json = builtins.toJSON config.configuration;
            passthru = {
              config = config.configuration;
            };
          }
          ''
            name=${config.name}
            mkdir "$name"

            cp ${./autograde-Makefile} "$name/autograde-Makefile"
            cp ${autograder} "$name/autograde.tar"
            echo "$json" > "$name/${config.name}.yml"

            chmod a+rw -R "$name"
            ${pkgs.gnutar}/bin/tar -cf $out "$name"
          '';

    in
    {

      config.packages = {
        syntactic = mkAssignment ./syntactic;
        assignments_all = pkgs.runCommand "assignments" { } ''
          mkdir -p $out
          cp ${self'.assignments.syntactic} $out/syntactic.tar
        '';
      };
    };
}
