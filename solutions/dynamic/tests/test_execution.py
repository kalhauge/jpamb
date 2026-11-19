"""Interpreter regressions and optional checks against built JPAMB cases."""

import os
from pathlib import Path

import dynamic
import pytest

import jpamb
import jvm
from jvm import state


@pytest.mark.parametrize(
    "op,left,right,expected",
    [
        (jvm.BinaryOpr.Add, 2147483647, 1, -2147483648),
        (jvm.BinaryOpr.Sub, -2147483648, 1, 2147483647),
        (jvm.BinaryOpr.Mul, 1073741824, 4, 0),
        (jvm.BinaryOpr.Div, -7, 3, -2),
        (jvm.BinaryOpr.Div, 7, -3, -2),
        (jvm.BinaryOpr.Div, -2147483648, -1, -2147483648),
        (jvm.BinaryOpr.Rem, -7, 3, -1),
        (jvm.BinaryOpr.Rem, 7, -3, 1),
        (jvm.BinaryOpr.Div, 1, 0, "divide by zero"),
        (jvm.BinaryOpr.Rem, 1, 0, "divide by zero"),
    ],
)
def test_java_integer_semantics(op, left, right, expected):
    assert dynamic.binary(op, left, right) == expected


def bytecode(*instructions):
    method = jvm.AbsMethodID.decode("Example.run:(I)I")
    body = jvm.Method(method, list(instructions), 1)
    return jpamb.Bytecode(None, None, {method: body}), method


@pytest.mark.parametrize(
    "value,expected", [(0, "divide by zero"), (2, "ok"), (-2, "ok")]
)
def test_argument_load_division_and_value_return(value, expected):
    bc, method = bytecode(
        jvm.Push(type=jvm.Int(), value=1, offset=0),
        jvm.Load(type=jvm.Int(), index=0, offset=1),
        jvm.Binary(type=jvm.Int(), operant=jvm.BinaryOpr.Div, offset=2),
        jvm.Return(type=jvm.Int(), offset=3),
    )
    assert (
        dynamic.execute_input(bc, method, jpamb.Input([jpamb.case.Int(value)]), 20)
        == expected
    )


def test_infinite_loop_returns_bounded_timeout():
    bc, method = bytecode(jvm.Goto(target=0, offset=0))
    assert dynamic.execute_input(bc, method, jpamb.Input([jpamb.case.Int(0)]), 5) == "*"


@pytest.mark.parametrize(
    "target,value,expected",
    [
        (jvm.Short(), 32768, -32768),
        (jvm.Byte(), 255, -1),
        (jvm.Char(), -1, 65535),
    ],
)
def test_integer_cast(target, value, expected):
    bc, method = bytecode(jvm.Cast(from_=jvm.Int(), to_=target, offset=0))
    current = dynamic.initial(bc, method, jpamb.Input([jpamb.case.Int(0)]))
    current.frames.peek().stack.push(state.StackInt(value))
    dynamic.step(bc, current)
    assert current.frames.peek().stack.pop().value == expected


def test_array_negative_index_is_not_python_indexing():
    bc, method = bytecode(jvm.ArrayLoad(type=jvm.Int(), offset=0))
    current = dynamic.initial(bc, method, jpamb.Input([jpamb.case.Int(0)]))
    ref = current.heap.new(state.HeapArray(jvm.Int(), [42]))
    current.frames.peek().stack.push(ref).push(state.StackInt(-1))
    assert dynamic.step(bc, current)[1] == "out of bounds"


def test_unsupported_execution_preserves_results_and_continues(monkeypatch, capsys):
    import sys

    monkeypatch.setattr(
        sys, "argv", ["dynamic-analysis", "--random", "--small", "Example.run:(I)I"]
    )
    monkeypatch.setattr(jpamb, "getmethodid", lambda *a, **kw: None)
    monkeypatch.setattr(jpamb, "setup", lambda: (None, None))
    monkeypatch.setattr(jpamb, "Bytecode", lambda *a: None)
    monkeypatch.setattr(
        dynamic, "random_inputs", lambda *a: iter(["ok", "unsupported"])
    )
    monkeypatch.setattr(dynamic, "fuzz_small", lambda *a: iter(["assertion error"]))

    def execute(bc, method, value, steps):
        if value == "unsupported":
            raise NotImplementedError("example unsupported instruction")
        return value

    monkeypatch.setattr(dynamic, "execute_input", execute)
    dynamic.analyse()
    captured = capsys.readouterr()
    assert "ok;found" in captured.out
    assert "assertion error;found" in captured.out
    assert "Unsupported execution" in captured.err


def test_built_benchmark_concrete_cases(monkeypatch):
    workdir = os.environ.get("JPAMB_TEST_WORKDIR")
    if not workdir:
        pytest.skip("Set JPAMB_TEST_WORKDIR to a built JPAMB checkout")
    monkeypatch.chdir(Path(workdir))
    suite, eff = jpamb.setup()
    bc = jpamb.Bytecode(suite, eff, {})
    checked = 0
    for experiment, control in suite.benchmark(eff=eff).experiments.items():
        if experiment.input is None:
            continue
        # Larger than production fuzzing budget: validate execution semantics,
        # not whether a random strategy discovers the supplied witness.
        outcome = dynamic.execute_input(
            bc, experiment.entry, experiment.input, 1_000_000
        )
        assert outcome in control.results, (experiment, outcome, control.results)
        checked += 1
    assert checked > 0
