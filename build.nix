{
  lib,
  python3Packages,
  self,
  jdk,
  maven,
  jvm2json,
}: let
  pyproject = lib.importTOML ./pyproject.toml;
in
  python3Packages.buildPythonApplication {
    pname = pyproject.project.name;
    version = pyproject.project.version;
    pyproject = true;
    src = self;

    build-system = with python3Packages; [setuptools];

    dontCheckRuntimeDeps = true;

    dependencies =
      [
        maven
        jvm2json
        jdk
      ]
      ++ (with python3Packages; [
        pyyaml
        click
        hypothesis
        loguru
        matplotlib
        tree-sitter-grammars.tree-sitter-java
        tree-sitter
        z3
      ]);

    pythonImportCheck = [
      "tree_sitter"
      "tree_sitter_java"
      "z3"
      "jpamb"
    ];

    makeWrapperArgs = [
      "--set"
      "JAVA_HOME"
      jdk
    ];
  }
