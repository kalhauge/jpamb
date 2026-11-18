from unittest.mock import patch

from hypothesis import given, strategies as st

import fuzzer
import jvm
import jvm.state as jvmc

@given(st.integers(min_value=-(2**31), max_value=2**31 - 1))
def test_int_roundtrip(n):
    # placeholder: replace with a real property of your code
    assert -(2**31) <= n < 2**31


INT32 = st.integers(min_value=-(2**31), max_value=2**31 - 1)


@given(INT32)
def test_returns_bool(n):
    assert isinstance(fuzzer.n_larger_5(n), bool)

@given(st.integers(min_value=6, max_value=2**31 - 1))
def test_true_above_5(n):
    assert fuzzer.n_larger_5(n) is True


def test_run_with_coverage_includes_each_executed_pc_once():
    state = jvmc.State(jvmc.Heap(), jvmc.CallStack())
    method = jvm.AbsMethodID.decode("Example.test:()V")
    pc0 = jvmc.PC(method, 0)
    pc1 = jvmc.PC(method, 1)
    pc2 = jvmc.PC(method, 2)

    with patch(
        "fuzzer.step",
        side_effect=[
            (pc0, state),
            (pc1, state),
            (pc0, state),
            (pc2, "ok"),
        ],
    ) as step:
        outcome, coverage = fuzzer.run_with_coverage(None, state, max_steps=10)

    assert outcome == "ok"
    assert coverage == frozenset({pc0, pc1, pc2})
    assert step.call_count == 4


def test_run_with_coverage_stops_at_max_steps():
    state = jvmc.State(jvmc.Heap(), jvmc.CallStack())
    method = jvm.AbsMethodID.decode("Example.test:()V")
    pc0 = jvmc.PC(method, 0)
    pc1 = jvmc.PC(method, 1)

    with patch(
        "fuzzer.step",
        side_effect=[(pc0, state), (pc1, state)],
    ) as step:
        outcome, coverage = fuzzer.run_with_coverage(None, state, max_steps=2)

    assert outcome is state
    assert coverage == frozenset({pc0, pc1})
    assert step.call_count == 2
