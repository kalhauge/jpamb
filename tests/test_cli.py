"""
These test, check that the output of the tests remain the same.
"""

import shutil

import pytest
from click.testing import CliRunner

import cli

analyses = [
    "jpamb-analysis-dummy",
    "basic",
    "syntactic-regex",
    "solution-dynamic-analysis",
]


@pytest.mark.slow
@pytest.mark.parametrize("solution", analyses)
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
def test_checkhealth(tmp_path):
    runner = CliRunner()
    result = runner.invoke(
        cli.cli,
        [
            "checkhealth",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output


interpreters = [
    "solution-dynamic-interpreter",
]


@pytest.mark.slow
@pytest.mark.parametrize("solution", interpreters)
def test_interpret(tmp_path, solution):
    exe = shutil.which(solution)
    if exe is None:
        pytest.skip(f"Could not find {solution} on path")

    runner = CliRunner()
    result = runner.invoke(
        cli.cli,
        [
            "interpret",
            "--report",
            (tmp_path / "report.sexp"),
            solution,
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
def test_validate_analysis(format):
    runner = CliRunner()
    result = runner.invoke(
        cli.cli,
        [
            "-v",
            "validate",
            "analysis",
            "--format",
            format,
            "tests/data/analysis-report.sexp",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output


@pytest.mark.slow
@pytest.mark.parametrize("format", ["autolab", "user"])
def test_validate_interpret(format):
    runner = CliRunner()
    result = runner.invoke(
        cli.cli,
        [
            "-v",
            "validate",
            "interpret",
            "--format",
            format,
            "tests/data/interpret-report.sexp",
        ],
        catch_exceptions=False,
    )

    assert result.exit_code == 0, result.output
