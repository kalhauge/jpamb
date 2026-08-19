import jpamb
import subprocess
import pytest
from pathlib import Path
import logging

suite = jpamb.Suite(Path("../..").absolute())

import dynamic

logger = logging.getLogger(__name__)


def test_dynamic():
    subprocess.run(
        "jpamb --workdir ../.. interpret -f Simple dynamic_test > tests/expected/test",
        shell=True,
        check=True,
    )


def test_dynamic():
    subprocess.run(
        "jpamb --workdir ../.. test -f Simple dynamic_analysis > tests/expected/analysis",
        shell=True,
        check=True,
    )


@pytest.mark.parametrize(
    "case",
    [s for s in suite.cases if "Simple" == s.methodid.classname.name],
    ids=lambda x: f"{x.methodid}:{x.input.encode()}",
)
def test_run(case):
    output = dynamic.run(suite, case.methodid, case.input.values)
    assert output == case.result
