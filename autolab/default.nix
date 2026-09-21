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
          scoreboard =
            if "analyse" == config.kind then ./analyse-scoreboard.json else ./interpret-scoreboard.json;

          makefile = pkgs.replaceVars ./autograde-Makefile {
            kind = config.kind;
          };
          configrb = if "analyse" == config.kind then ./analyse.rb else ./interpret.rb;
        in
        pkgs.runCommand "${config.name}.tar"
          {
            json = builtins.toJSON config.configuration;
            passthru = {
              config = config.configuration;
              inherit makefile scoreboard;
            };
          }
          ''
            name=${config.name}
            mkdir "$name"

            cp ${makefile} "$name/autograde-Makefile"
            cp ${autograder} "$name/autograde.tar"
            echo "$json" > "$name/${config.name}.yml"
            cp ${configrb} "$name/${config.name}.rb"

            chmod a+rw -R "$name"
            ${pkgs.gnutar}/bin/tar -cf $out "$name"
          '';

    in
    {

      config.packages =
        let
          syntactic = mkAssignment ./assignments/syntactic.nix;
          dynamic = mkAssignment ./assignments/dynamic.nix;
          static = mkAssignment ./assignments/static.nix;
          concrete = mkAssignment ./assignments/concrete.nix;
          abstract = mkAssignment ./assignments/abstract.nix;
        in
        {
          assignments =
            pkgs.runCommand "assignments"
              {
                passthru = {
                  inherit
                    syntactic
                    autograder
                    dynamic
                    static
                    concrete
                    abstract
                    ;
                };
              }
              ''
                mkdir -p $out
                cp ${syntactic} $out/syntactic.tar
                cp ${dynamic} $out/dynamic.tar
                cp ${static} $out/static.tar
                cp ${concrete} $out/concrete.tar
                cp ${abstract} $out/abstract.tar
              '';
        };
    };
}
