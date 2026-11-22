from unittest.mock import patch

from hypothesis import given, strategies as st

import fuzzer
import jvm
import jvm.state as jvmc
import syntaxAnalyser

@given(st.integers(min_value=-(2**31), max_value=2**31 - 1))
def test_int_roundtrip(n):
    # placeholder: replace with a real property of your code
    assert -(2**31) <= n < 2**31


INT32 = st.integers(min_value=-(2**31), max_value=2**31 - 1)

def test_intConstExtraction():
    src = """
        public static int multiError(boolean b) {
        assert b;
        return 1 / 0;
      }

      @Case("() -> ok")
      public static int earlyReturn() {
        if (true) {
          return 0;
        }
        assert false;
        return 0;
      }
      """
    intConsts = syntaxAnalyser.getDictFromSrc(src)
    if not isinstance(intConsts, list):
        print ("could not parse (no closing bracket?)")

    assert intConsts == [1,0]
    # for i in intConsts:
    #     print(f"got: {i}")


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


def test_intConstFromTS():
    src = """
    @Case("(0, 400, 12014) -> ok")
    @Case("(24691, 0, 0) -> ok")
    @Case("(24691, 400, 12013) -> ok")
    @Case("(24691, 400, 12014) -> assertion error")
    @Case("(24691, 400, 12015) -> ok")
    public static void fuzzCombinedGuidance(
        int gate, int base, int candidate) {
    if (gate != 24691) {
        return;
    }
    if (base < 400) {
        return;
    }
    if (base > 900) {
        return;
    }

    int target = base * 30 + 13;
    if (candidate > target) {
        if (candidate < target + 13) {
        assert false;
        }
    }
    """

    intConsts = syntaxAnalyser.getIntsFromSrcTS(src.encode('utf-8'), "fuzzCombinedGuidance")
    if not isinstance(intConsts, list):
        print ("could not parse (no closing bracket?)")

    augmentedIntConsts = syntaxAnalyser.augmentWithBoundryValues(intConsts)
    assert intConsts == set([24691, 400, 900, 30, 13])
    assert augmentedIntConsts == set([0,1,-1, 24691, 400, 900, 30, 13, -2147483648, -2147483647, 2, 899, 901, 12, 14, 399, 401, 24690, 24692, 2147483646, 2147483647, 29, -2, 31])
