"""Domain laws, Java string behavior, and the public analyzer options."""

import os
import subprocess
import sys
from pathlib import Path

import pytest
import static
from abstractions import BooleanSet, SignSet, StringSet, is_lattice
from configuration import AnalysisConfig, parse_options
from hypothesis import given
from hypothesis import strategies as st
from string_methods import AbstractReference, equals

import jpamb
import jvm
import sexpr

ROOT = Path(__file__).resolve().parents[3]
STRING_CONFIG = AnalysisConfig(strings=True)
METHOD = "jpamb.cases.Strings.sayHello:(Ljava/lang/String;)V"
string_sets = st.one_of(st.none(), st.frozensets(st.text(max_size=5), max_size=10)).map(
    StringSet
)


@given(string_sets, string_sets, string_sets)
def test_string_lattice(a, b, c):
    is_lattice(a, b, c)
    assert a | b == b | a
    assert a & b == b & a
    assert (a | b) | c == a | (b | c)
    assert a | (a & b) == a
    assert a & (a | b) == a
    assert a <= a | b and b <= a | b


@given(
    st.frozensets(st.text(max_size=5), max_size=12),
    st.frozensets(st.text(max_size=5), max_size=12),
)
def test_string_equality_covers_concrete_answers(left, right):
    a, b = StringSet.abstract(left), StringSet.abstract(right)
    assert all(text in a for text in left)
    assert {x == y for x in left for y in right} <= a.equals(b)


def test_string_bottom_empty_text_and_cap():
    empty_text = StringSet.abstract([""])
    assert empty_text != StringSet.bot()
    assert empty_text.equals(empty_text) == {True}
    assert StringSet.bot().equals(StringSet.top()) == set()
    assert StringSet.abstract(map(str, range(9))) == StringSet.top()
    assert StringSet.abstract(map(str, range(8))) != StringSet.top()
    # A literal named 'top' must serialize differently from the top value.
    assert sexpr.sexpr(StringSet.abstract(["top"])) != sexpr.sexpr(StringSet.top())


def test_reference_null_and_content_equality():
    hello = StringSet.abstract(["hello"])
    heap = {"parameter:0": hello, "parameter:1": hello}
    a = AbstractReference(frozenset({"parameter:0"}))
    b = AbstractReference(frozenset({"parameter:1"}))
    null = AbstractReference(frozenset(), True)
    assert equals(a, b, heap) == ({True}, set())
    assert a.compare(b, jvm.CmpOpr.Eq) == {True, False}
    assert equals(a, null, heap) == ({False}, set())
    assert equals(null, a, heap) == (set(), {"null pointer"})
    assert equals(a | null, b, heap) == ({True}, {"null pointer"})


def test_interned_literal_identity():
    a = AbstractReference(frozenset({"literal:hello"}))
    b = AbstractReference(frozenset({"literal:bye"}))
    assert a.compare(a, jvm.CmpOpr.Eq) == {True}
    assert a.compare(b, jvm.CmpOpr.Eq) == {False}


def test_state_joins_and_heap_updates():
    initial = static.State((None,), ())
    a, left = initial.string_reference("parameter:0", StringSet.abstract(["hello"]))
    b, right = initial.string_reference("parameter:0", StringSet.abstract(["bye"]))
    combined = left.store(0, a) | right.store(0, b)
    assert initial.heap == {}
    assert left.heap["parameter:0"] == StringSet.abstract(["hello"])
    assert combined.heap["parameter:0"] == StringSet.abstract(["hello", "bye"])
    assert (combined | initial).locals == (None,)
    with pytest.raises(NotImplementedError):
        (combined | initial).load(0)


@pytest.mark.parametrize(
    "selection, strings",
    [
        ("sign", False),
        ("string", True),
        ("sign,string", True),
        ("string,sign", True),
    ],
)
def test_options(selection, strings):
    config, remaining = parse_options(["--abstractions", selection, "info"])
    assert config.strings == strings
    assert config.integer_domain is (None if selection == "string" else SignSet)
    assert remaining == ["info"]


@pytest.mark.parametrize(
    "arguments",
    [
        ["--abstractions", "interval"],
        ["--abstractions", ""],
        ["--abstractions", "sign,typo"],
        ["--typo"],
    ],
)
def test_invalid_options(arguments):
    with pytest.raises(SystemExit) as error:
        parse_options(arguments)
    assert error.value.code == 2


@pytest.mark.parametrize(
    "input_text, outcomes",
    [
        ("(s'hello')", {"ok"}),
        ("(s'not hello')", {"assertion error"}),
        ("ALL", {"ok", "assertion error", "null pointer"}),
    ],
)
@pytest.mark.parametrize("selection", ["string", "sign,string"])
def test_benchmark_execution(monkeypatch, input_text, outcomes, selection):
    config, _ = parse_options(["--abstractions", selection])
    if selection == "string":

        def forbidden(*args, **kwargs):
            pytest.fail("String-only execution must not use SignSet")

        for name in ("abstract", "top", "bot", "arithmetic", "compare", "__or__"):
            monkeypatch.setattr(SignSet, name, forbidden)
    monkeypatch.chdir(ROOT)
    suite, effect = jpamb.setup()
    bc = jpamb.Bytecode(suite, effect, {})
    ai = static.AbstractInterpreter.initial(
        bc, jpamb.parse_methodid(METHOD), jpamb.parse_input(input_text), config
    )
    found = set()
    for _ in range(100):
        if not ai.worklist:
            break
        _, finals = ai.step()
        found |= finals
    assert not ai.worklist
    assert found == outcomes


def test_reference_store_and_unknown_call():
    pc = static.PC(jpamb.parse_methodid(METHOD), 0)
    ref = AbstractReference(frozenset({"parameter:0"}))
    state = static.State((None,), (ref,), {"parameter:0": StringSet.top()})
    instruction = jvm.Store(offset=0, type=jvm.Reference(), index=0)
    [(position, after)] = static.manystep({pc: instruction}, pc, state, STRING_CONFIG)
    assert position == pc + 1
    assert after.locals == (ref,) and after.stack == () and after.heap == state.heap
    call = jvm.InvokeVirtual(
        offset=0, method=jpamb.parse_methodid("java.lang.String.length:()I")
    )
    with pytest.raises(NotImplementedError, match="Unsupported call"):
        list(static.manystep({pc: call}, pc, state, STRING_CONFIG))


def run_entrypoint(name, arguments):
    # Use this interpreter and source tree, independent of another checkout's PATH.
    env = dict(
        os.environ,
        PYTHONPATH=os.pathsep.join(
            [str(ROOT / "solutions/static/src"), str(ROOT / "src")]
        ),
    )
    return subprocess.run(
        [sys.executable, "-c", f"import static; static.{name}()", *arguments],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )


def test_cli_metadata_and_predictions():
    info = run_entrypoint("analyse", ["--abstractions", "string", "info"])
    assert "static,string,python" in info.stdout
    combined = run_entrypoint("analyse", ["--abstractions", "sign,string", "info"])
    assert "static,sign,string,python" in combined.stdout
    result = run_entrypoint("analyse", ["--abstractions", "sign,string", METHOD])
    predictions = dict(line.split(";") for line in result.stdout.splitlines())
    assert predictions["ok"] == predictions["assertion error"] == "maybe"
    assert predictions["null pointer"] == "maybe"
    assert predictions["*"] == "unknown"
    disabled = run_entrypoint("analyse", ["--abstractions", "sign", METHOD])
    assert all(line.endswith(";unknown") for line in disabled.stdout.splitlines())


@pytest.mark.parametrize("selection", ["string", "sign,string"])
def test_interpreter_trace_roundtrip(selection):
    from jpamb.interpret import Response

    result = run_entrypoint(
        "interpret", ["--abstractions", selection, METHOD, "(s'hello')", "100"]
    )
    response, warnings = Response.parse(result.stdout)
    assert response is not None and not warnings
    assert response.steps


@pytest.mark.parametrize(
    "method",
    [
        "jpamb.cases.Simple.divideByN:(I)I",
        "jpamb.cases.Simple.divideByZero:()I",
    ],
)
def test_string_only_does_not_analyze_integer_methods(method):
    result = run_entrypoint("analyse", ["--abstractions", "string", method])
    assert all(line.endswith(";unknown") for line in result.stdout.splitlines())
    combined = run_entrypoint("analyse", ["--abstractions", "sign,string", method])
    assert "divide by zero;maybe" in combined.stdout


@pytest.mark.parametrize(
    "instruction",
    [
        jvm.Binary(offset=0, type=jvm.Int(), operant=jvm.BinaryOpr.Add),
        jvm.Incr(offset=0, index=0, amount=1),
        jvm.Negate(offset=0, type=jvm.Int()),
        jvm.Push(offset=0, type=jvm.Int(), value=2),
    ],
)
def test_string_only_rejects_integer_operations(instruction):
    config, _ = parse_options(["--abstractions", "string"])
    boolean = BooleanSet(frozenset({False, True}))
    state = static.State((boolean,), (boolean, boolean))
    pc = static.PC(jpamb.parse_methodid(METHOD), 0)
    with pytest.raises(NotImplementedError, match="Integer"):
        list(static.manystep({pc: instruction}, pc, state, config))


def test_boolean_join_and_branches():
    false = BooleanSet(frozenset({False}))
    true = BooleanSet(frozenset({True}))
    both = false | true
    assert both.compare(false, jvm.CmpOpr.Ne) == {False, True}
    assert false.compare(false, jvm.CmpOpr.Eq) == {True}
    config, _ = parse_options(["--abstractions", "string"])
    pc = static.PC(jpamb.parse_methodid(METHOD), 0)
    instruction = jvm.Ifz(offset=0, condition=jvm.CmpOpr.Ne, target=5)
    successors = list(
        static.manystep({pc: instruction}, pc, static.State((), (both,)), config)
    )
    assert {position for position, _ in successors} == {pc + 1, pc % 5}


def test_string_only_boolean_parameter(monkeypatch):
    monkeypatch.chdir(ROOT)
    suite, effect = jpamb.setup()
    bc = jpamb.Bytecode(suite, effect, {})
    method = jpamb.parse_methodid("jpamb.cases.Simple.assertBoolean:(Z)V")
    config, _ = parse_options(["--abstractions", "string"])
    states = static.initialstate(bc, method, None, config)
    assert next(iter(states.values())).locals == (BooleanSet(frozenset({False, True})),)
