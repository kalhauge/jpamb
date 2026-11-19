import itertools
import subprocess
import sys
from pathlib import Path

import dynamic
import pytest

import cli
import jpamb

NAMES = ("random", "small", "mutation")
SELECTIONS = [combo for n in range(4) for combo in itertools.combinations(NAMES, n)]


@pytest.mark.parametrize("selected", SELECTIONS)
def test_selected_generators_and_combined_output(selected, monkeypatch, capsys):
    expected = selected or ("random",)
    monkeypatch.setattr(
        sys,
        "argv",
        ["dynamic-analysis", *[f"--{s}" for s in selected], "Example.method:()V"],
    )
    monkeypatch.setattr(jpamb, "getmethodid", lambda *a, **kw: object())
    monkeypatch.setattr(jpamb, "setup", lambda: (None, None))
    monkeypatch.setattr(jpamb, "Bytecode", lambda *a: None)
    called = []
    outcomes = dict(zip(NAMES, ("ok", "divide by zero", "assertion error")))

    def generator(name):
        def inputs(*args):
            called.append(name)
            yield name
            if name == "mutation":
                assert outcomes[name] in args[2]  # Feedback updated before resuming.

        return inputs

    monkeypatch.setattr(dynamic, "random_inputs", generator("random"))
    monkeypatch.setattr(dynamic, "fuzz_small", generator("small"))
    monkeypatch.setattr(dynamic, "fuzz_mutation", generator("mutation"))
    monkeypatch.setattr(
        dynamic, "execute_input", lambda bc, method, value, steps: outcomes[value]
    )
    dynamic.analyse()
    assert called == list(expected)
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == len(jpamb.QUERIES)
    for name in expected:
        assert f"{outcomes[name]};found" in lines


@pytest.mark.parametrize("selected", SELECTIONS)
def test_real_executable_info_protocol(selected):
    executable = Path(sys.executable).with_name("dynamic-analysis")
    result = subprocess.run(
        [str(executable), *[f"--{s}" for s in selected], "info"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    tags = result.stdout.splitlines()[3].split(",")
    for name in NAMES:
        assert (name in tags) == (name in (selected or ("random",)))


@pytest.mark.parametrize("flag", ["--smal", "--unknown", "--small=true"])
def test_invalid_options_rejected(flag):
    with pytest.raises(SystemExit) as error:
        dynamic.parse_options([flag, "info"])
    assert error.value.code == 2


@pytest.mark.parametrize("separator", [[], ["--"]])
def test_jpamb_forwards_flags_and_keeps_own_options(separator):
    # Real Click parser, without running the benchmark or requiring Java.
    args = [
        "--iterations",
        "1",
        *separator,
        "dynamic-analysis",
        "--small",
        "--mutation",
    ]
    with cli.analyse.make_context("analyse", args) as ctx:
        assert ctx.params["iterations"] == 1
        assert ctx.params["program"] == ("dynamic-analysis", "--small", "--mutation")


def test_true_flag_is_a_jpamb_option():
    with cli.analyse.make_context(
        "analyse", ["--true", "dynamic-analysis", "--random"]
    ) as ctx:
        assert ctx.params["correct_known_outcome"] is True
        assert ctx.params["program"] == ("dynamic-analysis", "--random")


def test_correction_changes_only_target_and_preserves_original():
    from collections import OrderedDict

    import jvm

    target = jpamb.case.Experiment(
        jvm.AbsMethodID.decode("jpamb.cases.Dependent.normalizedDistance:(II)I"), None
    )
    other = jpamb.case.Experiment(jvm.AbsMethodID.decode("Example.other:()V"), None)
    original = jpamb.case.Benchmark(
        OrderedDict(
            [
                (target, jpamb.case.Control({}, {"ok"})),
                (other, jpamb.case.Control({}, {"assertion error"})),
            ]
        )
    )
    corrected = cli.benchmark_with_known_correction(original)
    assert original.experiments[target].results == {"ok"}
    assert corrected.experiments[target].results == {"ok", "divide by zero"}
    assert corrected.experiments[other] is original.experiments[other]
    assert cli.benchmark_with_known_correction(corrected) == corrected


def test_true_rejects_incompatible_report(tmp_path):
    from click.testing import CliRunner

    result = CliRunner().invoke(
        cli.cli,
        [
            "analyse",
            "--true",
            "--report",
            str(tmp_path / "report.sexp"),
            "dynamic-analysis",
        ],
    )
    assert result.exit_code == 2
    assert "experimental score view" in result.output


def test_correction_rejects_missing_method():
    from collections import OrderedDict

    import click

    with pytest.raises(click.UsageError, match="requires normalizedDistance"):
        cli.benchmark_with_known_correction(jpamb.case.Benchmark(OrderedDict()))
