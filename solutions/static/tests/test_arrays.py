"""Array summary soundness and integration with each selectable integer domain."""

from pathlib import Path

import array_methods as arrays
import pytest
import static
from abstractions import I32_MAX, Interval, SignInterval, SignSet, StringSet
from configuration import AnalysisConfig
from hypothesis import given
from hypothesis import strategies as st
from string_methods import AbstractReference
from test_strings import run_entrypoint

import jpamb
import jvm
from jvm.state import StackInt

DOMAINS = [SignSet, Interval, SignInterval]
ROOT = Path(__file__).resolve().parents[3]


def abstract(domain, *values):
    return domain.abstract(StackInt(value) for value in values)


def reference():
    return AbstractReference(frozenset({"array"}))


@pytest.mark.parametrize("domain", DOMAINS)
def test_creation_and_default_values(domain):
    array = arrays.allocate(jvm.Int(), abstract(domain, 3), domain)
    assert array.length == abstract(domain, 3)
    assert array.elements == abstract(domain, 0)
    empty = arrays.allocate(jvm.Int(), abstract(domain, 0), domain)
    assert empty.elements == domain.bot()
    assert arrays.allocate(jvm.Int(), domain.bot(), domain) is None
    with pytest.raises(NotImplementedError, match="negative array size"):
        arrays.allocate(jvm.Int(), abstract(domain, -1, 2), domain)


@pytest.mark.parametrize("domain", DOMAINS)
@given(
    st.lists(st.integers(0, 20), min_size=1, max_size=5),
    st.lists(st.integers(-2, 22), min_size=1, max_size=5),
)
def test_access_covers_concrete_bounds(domain, lengths, indices):
    array = arrays.AbstractArray(jvm.Int(), abstract(domain, *lengths), domain.top())
    valid, errors = arrays.access(
        reference(), abstract(domain, *indices), {"array": array}, domain, jvm.Int()
    )
    for length in lengths:
        for index in indices:
            if 0 <= index < length:
                assert valid
            else:
                assert "out of bounds" in errors


@pytest.mark.parametrize("domain", DOMAINS)
def test_empty_negative_and_null_access(domain):
    empty = arrays.allocate(jvm.Int(), abstract(domain, 0), domain)
    value, errors = arrays.load(
        reference(), abstract(domain, 0), {"array": empty}, domain, jvm.Int()
    )
    assert value == domain.bot() and errors == {"out of bounds"}
    array = arrays.allocate(jvm.Int(), abstract(domain, 2), domain)
    value, errors = arrays.load(
        reference(), abstract(domain, -1), {"array": array}, domain, jvm.Int()
    )
    assert value == domain.bot() and errors == {"out of bounds"}
    null = AbstractReference(frozenset(), True)
    value, errors = arrays.load(null, abstract(domain, -1), {}, domain, jvm.Int())
    assert value == domain.bot() and errors == {"null pointer"}
    value, errors = arrays.length(null, {}, domain)
    assert value == domain.bot() and errors == {"null pointer"}
    nullable = reference() | null
    value, errors = arrays.load(
        nullable, abstract(domain, 0), {"array": array}, domain, jvm.Int()
    )
    assert StackInt(0) in value and errors == {"null pointer"}


@pytest.mark.parametrize("domain", [Interval, SignInterval])
def test_definite_and_uncertain_index_bounds(domain):
    array = arrays.allocate(jvm.Int(), abstract(domain, 2), domain)
    heap = {"array": array}
    value, errors = arrays.load(
        reference(), abstract(domain, 3), heap, domain, jvm.Int()
    )
    assert value == domain.bot() and errors == {"out of bounds"}
    value, errors = arrays.load(
        reference(), abstract(domain, 1), heap, domain, jvm.Int()
    )
    assert value == abstract(domain, 0) and not errors
    value, errors = arrays.load(
        reference(), abstract(domain, 1, 3), heap, domain, jvm.Int()
    )
    assert StackInt(0) in value and errors == {"out of bounds"}


@pytest.mark.parametrize("domain", DOMAINS)
def test_store_is_weak_and_does_not_mutate_predecessor(domain):
    original = arrays.allocate(jvm.Int(), abstract(domain, 2), domain)
    heap = {"array": original}
    updated, errors = arrays.store(
        reference(), abstract(domain, 0), abstract(domain, 10), heap, domain, jvm.Int()
    )
    assert not errors
    assert heap["array"] == original
    assert StackInt(0) in updated["array"].elements
    assert StackInt(10) in updated["array"].elements
    # A second reference to the same target observes the write.
    alias = AbstractReference(frozenset({"array"}))
    value, errors = arrays.load(alias, abstract(domain, 0), updated, domain, jvm.Int())
    assert StackInt(10) in value and not errors


@pytest.mark.parametrize("domain", DOMAINS)
@given(st.integers(-(2**31), 2**31 - 1))
def test_char_store_covers_unsigned_16_bit_conversion(domain, integer):
    heap = {"array": arrays.allocate(jvm.Char(), abstract(domain, 1), domain)}
    updated, _ = arrays.store(
        reference(),
        abstract(domain, 0),
        abstract(domain, integer),
        heap,
        domain,
        jvm.Char(),
    )
    value, _ = arrays.load(
        reference(), abstract(domain, 0), updated, domain, jvm.Char()
    )
    assert StackInt(integer % 65536) in value


@pytest.mark.parametrize("domain", DOMAINS)
def test_parameter_abstraction(domain):
    supplied = jpamb.case.Array(jvm.Int(), (2, 5))
    array = arrays.parameter(jvm.Int(), supplied, domain)
    assert array.length == abstract(domain, 2)
    assert StackInt(2) in array.elements and StackInt(5) in array.elements
    chars = arrays.parameter(
        jvm.Char(), jpamb.case.Array(jvm.Char(), ("h", "\x00")), domain
    )
    assert StackInt(ord("h")) in chars.elements and StackInt(0) in chars.elements
    unknown = arrays.parameter(jvm.Int(), None, domain)
    assert StackInt(0) in unknown.length and StackInt(I32_MAX) in unknown.length
    assert StackInt(-1) not in unknown.length
    assert unknown.elements == domain.top()


@pytest.mark.parametrize("domain", DOMAINS)
def test_unknown_parameters_may_alias(domain):
    method = jpamb.parse_methodid("Example.alias:([I[I)V")

    class BC:
        def getmethod(self, method):
            from types import SimpleNamespace

            return SimpleNamespace(max_locals=2)

    state = next(
        iter(
            static.initialstate(
                BC(), method, None, AnalysisConfig(integer_domain=domain)
            ).values()
        )
    )
    assert state.locals[0] == state.locals[1]
    assert state.locals[0].may_be_null


@pytest.mark.parametrize("domain", DOMAINS)
def test_array_heap_join_and_widen(domain):
    a = arrays.AbstractArray(jvm.Int(), abstract(domain, 1), abstract(domain, 0))
    b = arrays.AbstractArray(jvm.Int(), abstract(domain, 1, 2), abstract(domain, 0, 1))
    left = static.State((), (), {"array": a, "literal:x": StringSet.abstract(["x"])})
    right = static.State((), (), {"array": b})
    joined = left | right
    widened = left.widen(joined)
    assert StackInt(2) in widened.heap["array"].length
    assert StackInt(-1) not in widened.heap["array"].length
    assert StackInt(1) in widened.heap["array"].elements
    assert widened.heap["literal:x"] == left.heap["literal:x"]
    assert left.heap["array"] == a


@pytest.mark.parametrize("domain", [Interval, SignInterval])
def test_heap_element_growth_converges(domain):
    from test_intervals import execute

    # a = new int[1]; forever { a[0] = a[0] + 1; }
    instructions = [
        jvm.Push(offset=0, type=jvm.Int(), value=1),
        jvm.NewArray(offset=0, type=jvm.Int(), dim=1),
        jvm.Store(offset=0, type=jvm.Reference(), index=0),
        jvm.Load(offset=0, type=jvm.Reference(), index=0),
        jvm.Push(offset=0, type=jvm.Int(), value=0),
        jvm.Load(offset=0, type=jvm.Reference(), index=0),
        jvm.Push(offset=0, type=jvm.Int(), value=0),
        jvm.ArrayLoad(offset=0, type=jvm.Int()),
        jvm.Push(offset=0, type=jvm.Int(), value=1),
        jvm.Binary(offset=0, type=jvm.Int(), operant=jvm.BinaryOpr.Add),
        jvm.ArrayStore(offset=0, type=jvm.Int()),
        jvm.Goto(offset=0, target=3),
    ]
    outcomes, ai = execute(
        instructions,
        AnalysisConfig(integer_domain=domain),
        signature="Example.loop:()V",
        locals_count=1,
    )
    assert not outcomes and not ai.worklist


@pytest.mark.parametrize("domain", DOMAINS)
def test_dup_preserves_reference_identity(domain):
    pc = static.PC(jpamb.parse_methodid("Example.test:()V"), 0)
    array = arrays.allocate(jvm.Int(), abstract(domain, 2), domain)
    state = static.State((), (reference(),), {"array": array})
    instruction = jvm.Dup(offset=0, words=1)
    [(next_pc, after)] = static.manystep(
        {pc: instruction}, pc, state, AnalysisConfig(integer_domain=domain)
    )
    assert next_pc == pc + 1 and after.stack == (reference(), reference())
    assert after.heap == state.heap


@pytest.mark.parametrize("domain", DOMAINS)
@pytest.mark.parametrize(
    "method, expected",
    [
        ("arrayIsNull:()V", {"null pointer"}),
        ("arrayIsNullLength:()V", {"null pointer"}),
    ],
)
def test_null_benchmarks(monkeypatch, domain, method, expected):
    monkeypatch.chdir(ROOT)
    suite, effect = jpamb.setup()
    bc = jpamb.Bytecode(suite, effect, {})
    ai = static.AbstractInterpreter.initial(
        bc,
        jpamb.parse_methodid("jpamb.cases.Arrays." + method),
        None,
        AnalysisConfig(integer_domain=domain),
    )
    found = set()
    for _ in range(30):
        if not ai.worklist:
            break
        _, outcomes = ai.step()
        found |= outcomes
    assert not ai.worklist and found == expected


@pytest.mark.parametrize(
    "selection",
    ["interval", "sign,interval", "interval,string", "sign,interval,string"],
)
@pytest.mark.parametrize(
    "method, outcome",
    [
        ("arrayOutOfBounds:()V", "out of bounds"),
        ("arrayInBounds:()V", "ok"),
        ("arrayLength:()V", "ok"),
    ],
)
def test_basic_array_cli_predictions(selection, method, outcome):
    result = run_entrypoint(
        "analyse", ["--abstractions", selection, "jpamb.cases.Arrays." + method]
    )
    predictions = dict(line.split(";") for line in result.stdout.splitlines())
    assert predictions[outcome] == "maybe"
    assert all(
        value == "no" for key, value in predictions.items() if key not in (outcome, "*")
    )


def test_string_only_still_rejects_arrays():
    result = run_entrypoint(
        "analyse", ["--abstractions", "string", "jpamb.cases.Arrays.arrayLength:()V"]
    )
    assert all(line.endswith(";unknown") for line in result.stdout.splitlines())


def test_unsupported_array_types_remain_explicit():
    with pytest.raises(NotImplementedError):
        arrays.allocate(jvm.Boolean(), Interval(1, 1), Interval)
