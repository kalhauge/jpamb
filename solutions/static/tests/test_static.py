import jpamb
import subprocess
import pytest
from pathlib import Path
import logging

suite = jpamb.Suite(Path("../..").absolute())

import static

logger = logging.getLogger(__name__)


def test_static():
    subprocess.run(
        "jpamb --workdir ../.. interpret -f Simple static_interpret > tests/expected/interpret",
        shell=True,
    )


@pytest.mark.parametrize(
    "case",
    [s for s in suite.cases if "Simple" == s.methodid.classname.name],
    ids=lambda x: f"{x.methodid}:{x.input.encode()}",
)
def test_run(case):
    output = static.run(suite, case.methodid, case.input.values)
    assert case.result in output


@pytest.mark.parametrize(
    "method, results",
    [x for x in suite.case_methods().items() if "Simple" == x[0].classname.name],
    ids=lambda x: f"{x}",
)
def test_analyse(method, results):
    output = static.run(suite, method, None)
    print(output)
    assert output >= results
