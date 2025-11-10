"""
These test, check that the output of the tests remain the same.
"""

import pytest

from glob import glob
from pathlib import Path

from click.testing import CliRunner

from jpamb import cli


solutions = [
    # Path("solutions") / "apriori.py",
    Path("solutions") / "bytecoder.py",
    # Path("solutions") / "cheater.py",
    Path("solutions") / "syntaxer.py",
    Path("solutions") / "my_analyzer.py",
]


@pytest.mark.slow
@pytest.mark.parametrize("solution", solutions)
def test_solutions(solution):
    runner = CliRunner()
    solreport = Path("test") / "expected" / (solution.stem + ".txt")
    result = runner.invoke(
        cli.cli,
        [
            "test",
            "-f",
            "Simple",
            "-r",
            str(solreport),
            "--with-python",
            str(solution),
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0


@pytest.mark.slow
def test_interpret_i():
    runner = CliRunner()
    sol = Path("solutions") / "interpreter.py"
    solreport = Path("test") / "expected" / (sol.stem + ".txt")
    result = runner.invoke(
        cli.cli,
        [
            "interpret",
            "-f",
            "Simple",
            "-r",
            str(solreport),
            "--with-python",
            str(sol),
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0
