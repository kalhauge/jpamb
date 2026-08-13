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
  runit,
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
    runit
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
