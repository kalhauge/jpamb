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
        "jpamb --workdir ../.. test -f Simple static > tests/expected/analysis",
        shell=True,
        check=True,
    )


@pytest.mark.parametrize(
    "method, results",
    [x for x in suite.case_methods().items() if "Simple" == x[0].classname.name],
    ids=lambda x: f"{x}",
)
def test_run(method, results):
    output = static.run(suite, method)
    print(output)
    assert output >= results
