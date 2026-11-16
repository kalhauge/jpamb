"""Concrete containment and interpreter regressions for branch refinement."""

from collections import deque
from dataclasses import replace

import pytest
import static
from abstractions import (
    I32_MAX,
    I32_MIN,
    BooleanSet,
    Interval,
    SignInterval,
    SignSet,
    StringSet,
)
from configuration import parse_options
from hypothesis import given
from hypothesis import strategies as st
from refinement import Local, StringEquals, branch, filter_pair
from string_methods import AbstractReference
from test_abstractions import compare

import jpamb
import jvm
from jvm.state import StackInt

DOMAINS = [SignSet, Interval, SignInterval]
CONFIGS = [
    "sign",
    "interval",
    "string",
    "sign,interval",
    "sign,string",
    "interval,string",
    "sign,interval,string",
]
NUMBERS = st.one_of(
    st.integers(I32_MIN, I32_MAX), st.sampled_from([I32_MIN, I32_MAX, -1, 0, 1])
)


@pytest.mark.parametrize("domain", DOMAINS)
@pytest.mark.parametrize("op", list(jvm.CmpOpr))
@given(
    st.lists(NUMBERS, min_size=1, max_size=6),
    st.lists(NUMBERS, min_size=1, max_size=6),
    st.booleans(),
)
def test_filters_preserve_every_satisfying_concrete_pair(domain, op, xs, ys, answer):
    a = domain.abstract(map(StackInt, xs))
    b = domain.abstract(map(StackInt, ys))
    left, right = filter_pair(a, b, op, answer)
    assert left <= a and right <= b
    for x in xs:
        for y in ys:
            if compare(op, StackInt(x), StackInt(y)) == answer:
                assert StackInt(x) in left and StackInt(y) in right


@pytest.mark.parametrize("op", list(jvm.CmpOpr))
@pytest.mark.parametrize("answer", [False, True])
def test_boolean_filters(op, answer):
    both = BooleanSet(frozenset({False, True}))
    left, right = filter_pair(both, both, op, answer)
    for x in (False, True):
        for y in (False, True):
            if compare(op, StackInt(int(x)), StackInt(int(y))) == answer:
                assert x in left.values and y in right.values


def run_program(instructions, config, initial):
    method = jpamb.parse_methodid("Test.run:()V")
    pc = static.PC(method, 0)
    bc = {pc % i: instruction for i, instruction in enumerate(instructions)}
    ai = static.AbstractInterpreter(bc, deque([pc]), {pc: initial}, config)
    outcomes = set()
    for _ in range(300):
        if not ai.worklist:
            return outcomes, ai
        _, results = ai.step()
        outcomes |= results
    pytest.fail("Synthetic program did not converge")


def load(i):
    return jvm.Load(offset=0, type=jvm.Int(), index=i)


def push(n):
    return jvm.Push(offset=0, type=jvm.Int(), value=n)


@pytest.mark.parametrize("selection", [c for c in CONFIGS if c != "string"])
def test_positive_guard_removes_zero_from_division(selection):
    config, _ = parse_options(["--abstractions", selection])
    ops = [
        load(0),
        jvm.Ifz(offset=0, condition=jvm.CmpOpr.Le, target=6),
        push(10),
        load(0),
        jvm.Binary(offset=0, type=jvm.Int(), operant=jvm.BinaryOpr.Div),
        jvm.Return(offset=0, type=jvm.Int()),
        jvm.Return(offset=0, type=None),
    ]
    outcomes, _ = run_program(
        ops, config, static.State((config.integer_domain.top(),), ())
    )
    assert outcomes == {"ok"}


@pytest.mark.parametrize("domain", DOMAINS)
def test_hole_precision_and_both_operands(domain):
    top = domain.top()
    zero = domain.abstract([StackInt(0)])
    left, _ = filter_pair(top, zero, jvm.CmpOpr.Ne, True)
    assert (StackInt(0) in left) == (domain is Interval)
    a = domain.abstract([StackInt(-5), StackInt(5)])
    b = domain.abstract([StackInt(0)])
    x, y = filter_pair(a, b, jvm.CmpOpr.Lt, True)
    assert StackInt(-5) in x and StackInt(5) not in x
    assert StackInt(0) in y


def test_local_origin_invalidation_and_join():
    value = Interval(-5, 5)
    state = static.State((value, value), ()).push(value, Local(0))
    changed = state.store(0, Interval(0, 0))
    assert changed.origins == (None,)
    other = replace(state, origins=(Local(1),))
    assert (state | other).origins == (None,)
    assert state.widen(state | other).origins == (None,)
    # An unrelated assignment preserves provenance.
    assert state.store(1, Interval(1, 1)).origins == (Local(0),)


@pytest.mark.parametrize("domain", DOMAINS)
def test_same_local_comparison_and_duplicate(domain):
    value = domain.top()
    state = static.State((value,), ()).push(value, Local(0))
    assert branch(state, value, value, Local(0), Local(0), jvm.CmpOpr.Ne, True) is None
    zero = domain.abstract([StackInt(0)])
    after = branch(state, value, zero, Local(0), None, jvm.CmpOpr.Eq, True)
    assert after.locals[0] == after.stack[0] == zero


@pytest.mark.parametrize("selection", [c for c in CONFIGS if "string" in c])
@pytest.mark.parametrize("stored", [False, True])
def test_string_equals_branch_refines_contents_and_nullness(selection, stored):
    config, _ = parse_options(["--abstractions", selection])
    ref = AbstractReference(frozenset({"parameter:0"}), True)
    initial = static.State((ref, None), (), {"parameter:0": StringSet.top()})
    call = jvm.InvokeVirtual(
        offset=0,
        method=jpamb.parse_methodid("java.lang.String.equals:(Ljava/lang/Object;)Z"),
    )
    literal = jvm.Push(
        offset=0, type=jvm.Object(jvm.ClassName("java.lang.String")), value="hello"
    )
    ops = [load(0), literal, call]
    if stored:
        ops.extend([jvm.Store(offset=0, type=jvm.Int(), index=1), load(1)])
    branch_index = len(ops)
    ops.extend(
        [
            jvm.Ifz(offset=0, condition=jvm.CmpOpr.Eq, target=branch_index + 6),
            load(0),
            literal,
            call,
            jvm.Ifz(offset=0, condition=jvm.CmpOpr.Eq, target=branch_index + 7),
            jvm.Return(offset=0, type=None),
            jvm.Return(offset=0, type=None),
            jvm.New(offset=0, classname=jvm.ClassName("java.lang.AssertionError")),
        ]
    )
    outcomes, _ = run_program(ops, config, initial)
    assert outcomes == {"ok", "null pointer"}


def test_false_string_branch_and_stale_predicate():
    a = AbstractReference(frozenset({"parameter:0"}))
    b = AbstractReference(frozenset({"literal:hello"}))
    state = static.State(
        (a, None),
        (),
        {
            "parameter:0": StringSet.abstract(["hello", "bye"]),
            "literal:hello": StringSet.abstract(["hello"]),
        },
    )
    pred = StringEquals(a, b, Local(0), None)
    state = state.store(1, BooleanSet(frozenset({False, True})), pred)
    false = BooleanSet(frozenset({False}))
    after = branch(state, state.locals[1], false, Local(1), None, jvm.CmpOpr.Eq, True)
    assert after.heap["parameter:0"] == StringSet.abstract(["bye"])
    assert after.locals[1] == false
    assert state.heap["parameter:0"] == StringSet.abstract(["hello", "bye"])
    assert state.store(0, b).predicates == (None, None)


def test_reference_guard_does_not_confuse_summary_ids_with_identity():
    a = AbstractReference(frozenset({"parameter:0"}), True)
    b = AbstractReference(frozenset({"parameter:1"}))
    left, right = filter_pair(a, b, jvm.CmpOpr.Eq, True)
    assert left.targets == a.targets and right.targets == b.targets
    assert not left.may_be_null
    null = AbstractReference(frozenset(), True)
    state = static.State((a,), ())
    after = branch(state, a, null, Local(0), None, jvm.CmpOpr.Ne, True)
    assert after.locals[0] == replace(a, may_be_null=False)


@pytest.mark.parametrize("answer", [False, True])
@given(
    st.sets(st.sampled_from(["a", "b", "c"]), min_size=1),
    st.sets(st.sampled_from(["a", "b", "c"]), min_size=1),
    st.booleans(),
)
def test_string_refinement_preserves_satisfying_contents(answer, xs, ys, nullable):
    a = AbstractReference(frozenset({"parameter:0"}))
    b = AbstractReference(frozenset({"parameter:1"}), nullable)
    state = static.State(
        (a, b),
        (),
        {"parameter:0": StringSet.abstract(xs), "parameter:1": StringSet.abstract(ys)},
    )
    predicate = StringEquals(a, b, Local(0), Local(1))
    from refinement import refine_strings

    after = refine_strings(state, predicate, answer)
    for x in xs:
        for y in [*ys, *([None] if nullable else [])]:
            if (x == y) == answer:
                assert after is not None
                assert x in after.heap["parameter:0"]
                if y is None:
                    assert after.locals[1].may_be_null
                else:
                    assert y in after.heap["parameter:1"]


def test_trace_schema_omits_provenance():
    import sexpr

    state = static.State((Interval(0, 1),), ()).push(Interval(0, 1), Local(0))
    assert state.__sexpr__() == sexpr.data(
        "state", locals=state.locals, stack=state.stack, heap=state.heap
    )


def test_join_drops_conflicting_string_predicates():
    a = AbstractReference(frozenset({"parameter:0"}))
    b = AbstractReference(frozenset({"literal:a"}))
    c = AbstractReference(frozenset({"literal:b"}))
    both = BooleanSet(frozenset({False, True}))
    state = static.State((a, both), ())
    left = state.store(1, both, StringEquals(a, b, Local(0), None))
    right = state.store(1, both, StringEquals(a, c, Local(0), None))
    assert (left | right).predicates == (None, None)
