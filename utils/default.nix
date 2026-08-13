{
  buildPythonApplication,
  setuptools,
  gcc,
  pyyaml,
  loguru,
  click,
}:
buildPythonApplication rec {
  name = "jpamb";
  src = ./.;
  pyproject = true;

  buildInputs = [
    setuptools
    gcc
    pyyaml
  ]
  ++ propagatedBuildInputs;

  propagatedBuildInputs = [
    loguru
    click
  ];

  meta.mainProgram = "jpamb";
}
