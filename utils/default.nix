{
  buildPythonPackage,
  setuptools,
  gcc,
  pyyaml,
  loguru,
  click,
  pytest,
  pytestCheckHook,
  hypothesis,
}:
buildPythonPackage rec {
  name = "jpamb";
  src = ./.;
  pyproject = true;

  buildInputs = [
    gcc
    pyyaml
    pytest
  ]
  ++ propagatedBuildInputs;

  propagatedBuildInputs = [
    loguru
    click
  ];

  build-system = [
    setuptools
  ];

  nativeCheckInputs = [
    pytestCheckHook
    hypothesis
  ];

  meta.mainProgram = "jpamb";
}
