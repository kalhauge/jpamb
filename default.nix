{
  buildPythonPackage,
  setuptools,
  gcc,
  pyyaml,
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
