"""
These test, check that the output of the tests remain the same.
"""

import shutil

import pytest
from click.testing import CliRunner

import cli

solutions = [
    "jpamb-analysis-dummy",
    "basic",
    "syntactic-regex",
]


@pytest.mark.slow
@pytest.mark.parametrize("solution", solutions)
def test_analyse(solution):
    exe = shutil.which(solution)
    if exe is None:
        pytest.skip(f"Could not find {solution} on path")

    runner = CliRunner()
    result = runner.invoke(
        cli.cli,
        [
            "analyse",
            "-f",
            "Simple",
            solution,
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output


@pytest.mark.slow
def test_analyse_report(tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        cli.cli,
        [
            "analyse",
            "--report",
            (tmp_path / "report.sexp"),
            "jpamb-analysis-dummy",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output


@pytest.mark.slow
def test_interpret(tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        cli.cli,
        [
            "interpret",
            "jpamb-interpreter-dummy",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output


methods = [
    "jpamb.cases.Simple.assertBoolean:(Z)V",
]

formats = ["pretty", "real", "repr", "json"]


@pytest.mark.slow
@pytest.mark.parametrize("method", methods)
@pytest.mark.parametrize("format", formats)
def test_inspect(method, format):
    runner = CliRunner()
    result = runner.invoke(
        cli.cli,
        ["-v", "inspect", "--format", format, method],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output


@pytest.mark.slow
@pytest.mark.parametrize("format", ["autolab", "user"])
@pytest.mark.parametrize(
    "report", ["tests/data/analysis-report.sexp", "tests/data/interpret-report.sexp"]
)
def test_validate(format, report):
    runner = CliRunner()
    result = runner.invoke(
        cli.cli,
        [
            "-v",
            "validate",
            "--format",
            format,
            report,
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output
