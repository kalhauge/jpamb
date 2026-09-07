{ lib, config, ... }:
let
  inherit (lib) types mkOption;
in
{
  options = {
    name = mkOption {
      type = types.str;
    };

    general.display_name = mkOption {
      type = types.str;
    };

    general.category_name = mkOption {
      type = types.str;
    };

    dates = {
      due_at = mkOption { type = types.str; };
      end_at = mkOption { type = types.str; };
      start_at = mkOption { type = types.str; };
    };

    problems = mkOption {
      type = types.listOf (
        types.submodule (
          { name, ... }:
          {
            options = {
              name = mkOption {
                type = types.str;
              };
              decription = mkOption {
                type = types.str;
                default = "";
              };
              max_score = mkOption {
                type = types.float;
              };
              optional = mkOption {
                type = types.bool;
                default = false;
              };
              starred = mkOption {
                type = types.bool;
                default = false;
              };
            };
          }
        )
      );
    };

    configuration = mkOption {
      type = types.attrs;
    };
  };
  config = {
    configuration = {
      autograder = {
        autograde_image = "autograding_image";
        autograde_timeout = 180;
        release_score = true;
      };
      inherit (config) dates problems;
      general = {
        inherit (config.general) category_name display_name;
        allow_student_assign_group = true;
        disable_network = true;
        github_submission_enabled = true;
        group_size = 1;
        handin_directory = "handin";
        handin_filename = "report.sexp";
        is_positive_grading = false;
        max_grace_days = 0;
        max_size = 2;
        max_submissions = -1;
      };
    };
  };
}
