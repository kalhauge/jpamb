"""Check intervals against concrete Java integers, then exercise the interpreter.

The combined domain must preserve holes such as nonzero [-5, 5], not merely
report the same result as two unrelated analyzer runs.
"""

from pathlib import Path
from types import SimpleNamespace

import pytest
import static
from abstractions import I32_MAX, I32_MIN, Interval, SignInterval, SignSet
from configuration import AnalysisConfig, parse_options
from hypothesis import given
from hypothesis import strategies as st
from test_abstractions import arithmetic, compare, st_interval

import jpamb
import jvm
from jvm.state import StackInt

DOMAINS = [Interval, SignInterval]
integers = st.one_of(
    st.sampled_from([I32_MIN, I32_MAX, -1, 0, 1]), st.integers(I32_MIN, I32_MAX)
)
values = st.lists(integers, max_size=6).map(lambda xs: [StackInt(x) for x in xs])
products = st.builds(
    SignInterval,
    st.sets(st.sampled_from([-1, 0, 1])).map(frozenset).map(SignSet),
    st_interval(),
)


@pytest.mark.parametrize("domain", DOMAINS)
@pytest.mark.parametrize("operation", list(jvm.BinaryOpr))
@given(values, values)
def test_arithmetic_covers_java_results(domain, operation, xs, ys):
    a, b = domain.abstract(xs), domain.abstract(ys)
    result, errors = a.arithmetic(b, operation)
    for x in xs:
        for y in ys:
            try:
                expected = arithmetic(operation, x, y)
            except ZeroDivisionError:
                assert "divide by zero" in errors
            else:
                assert expected in result
    expected_error = (
        a != domain.bot()
        and StackInt(0) in b
        and operation in (jvm.BinaryOpr.Div, jvm.BinaryOpr.Rem)
    )
    assert errors == ({"divide by zero"} if expected_error else set())


@pytest.mark.parametrize("domain", DOMAINS)
@pytest.mark.parametrize("operation", list(jvm.CmpOpr))
@given(values, values)
def test_comparisons_cover_java_results(domain, operation, xs, ys):
    result = domain.abstract(xs).compare(domain.abstract(ys), operation)
    assert {compare(operation, x, y) for x in xs for y in ys} <= result


@given(products, products, products)
def test_product_lattice(a, b, c):
    assert a <= a | b and b <= a | b
    assert a & b <= a and a & b <= b
    assert a | b == b | a
    assert a & b == b & a
    assert (a | b) | c == a | (b | c)
    assert (a & b) & c == a & (b & c)
    assert a | (a & b) == a
    assert a & (a | b) == a
    assert a | a.top() == a.top()
    assert a & a.bot() == a.bot()
    assert a | a.bot() == a
    assert a & a.top() == a


@given(products, products)
def test_product_widen_contains_both_inputs(a, b):
    widened = a.widen(a | b)
    assert a <= widened and b <= widened


@given(st_interval(), st_interval())
def test_interval_widen_contains_both_inputs(a, b):
    widened = a.widen(a | b)
    assert a <= widened and b <= widened


def test_reduction_and_nonzero_division():
    nonzero = SignInterval.abstract([StackInt(-5), StackInt(5)])
    assert nonzero.interval == Interval(-5, 5)
    assert nonzero.signs == SignSet.from_sign("-+")
    assert StackInt(0) not in nonzero
    assert nonzero.compare(SignInterval.abstract([StackInt(0)]), jvm.CmpOpr.Eq) == {
        False
    }
    result, errors = SignInterval.abstract([StackInt(10)]).arithmetic(
        nonzero, jvm.BinaryOpr.Div
    )
    assert errors == set()
    assert StackInt(0) not in result
    assert StackInt(-2) in result and StackInt(10) in result
    assert Interval(10, 10).arithmetic(Interval(-5, 5), jvm.BinaryOpr.Div)[1] == {
        "divide by zero"
    }
    assert SignInterval(SignSet.from_sign("+"), Interval(-5, -1)) == SignInterval.bot()
    assert SignInterval(SignSet.from_sign("+"), Interval(-5, 5)).interval == Interval(
        1, 5
    )


@pytest.mark.parametrize("domain", DOMAINS)
@pytest.mark.parametrize("operation", list(jvm.BinaryOpr))
def test_empty_operands_and_java_boundaries(domain, operation):
    assert domain.bot().arithmetic(domain.top(), operation) == (domain.bot(), set())
    assert domain.top().arithmetic(domain.bot(), operation) == (domain.bot(), set())
    boundaries = [I32_MIN, I32_MIN + 1, -65536, -2, -1, 0, 1, 2, 65536, I32_MAX]
    for x in boundaries:
        for y in boundaries:
            a, b = StackInt(x), StackInt(y)
            result, errors = domain.abstract([a]).arithmetic(
                domain.abstract([b]), operation
            )
            if y == 0 and operation in (jvm.BinaryOpr.Div, jvm.BinaryOpr.Rem):
                assert result == domain.bot() and errors == {"divide by zero"}
            else:
                assert arithmetic(operation, a, b) in result
                assert errors == set()


@pytest.mark.parametrize("domain", DOMAINS)
def test_interval_precision_and_overflow(domain):
    def abstract(*xs):
        return domain.abstract(StackInt(x) for x in xs)

    result, errors = abstract(2, 5).arithmetic(abstract(3), jvm.BinaryOpr.Add)
    assert errors == set()
    assert result.compare(abstract(10), jvm.CmpOpr.Lt) == {True}
    result, _ = abstract(I32_MAX).arithmetic(abstract(1), jvm.BinaryOpr.Add)
    assert result == abstract(I32_MIN)
    result, _ = abstract(I32_MAX - 1, I32_MAX).arithmetic(
        abstract(1), jvm.BinaryOpr.Add
    )
    assert StackInt(I32_MIN) in result and StackInt(I32_MAX) in result
    result, _ = abstract(I32_MIN, 0).arithmetic(abstract(-1), jvm.BinaryOpr.Div)
    assert StackInt(I32_MIN) in result and StackInt(1) in result


@pytest.mark.parametrize(
    "selection, domain, strings",
    [
        ("sign", SignSet, False),
        ("string", None, True),
        ("interval", Interval, False),
        ("sign,interval", SignInterval, False),
        ("interval,string", Interval, True),
        ("sign,string", SignSet, True),
        ("sign,interval,string", SignInterval, True),
        ("string,interval,sign", SignInterval, True),
    ],
)
def test_all_selections(selection, domain, strings):
    config, remaining = parse_options(["--abstractions", selection, "info"])
    assert config.integer_domain is domain and config.strings == strings
    assert set(config.tags) == {"static", "python", *selection.split(",")}
    assert remaining == ["info"]


class Bytecode(dict):
    """Small decoded-bytecode fixture; no benchmark annotations are read."""

    def __init__(self, method, instructions, locals_count):
        super().__init__(
            (static.PC(method, i), op) for i, op in enumerate(instructions)
        )
        self.locals_count = locals_count

    def getmethod(self, method):
        return SimpleNamespace(max_locals=self.locals_count)


def execute(instructions, config, signature="Example.test:(Z)V", locals_count=2):
    method = jpamb.parse_methodid(signature)
    bc = Bytecode(method, instructions, locals_count)
    ai = static.AbstractInterpreter.initial(bc, method, None, config)
    outcomes = set()
    for _ in range(100):
        if not ai.worklist:
            return outcomes, ai
        _, finals = ai.step()
        outcomes |= finals
    pytest.fail("Worklist did not converge within 100 steps")


def choose(left, right):
    # Branches assign either left or right to local 1; both join at instruction 7.
    return [
        jvm.Load(offset=0, type=jvm.Int(), index=0),
        jvm.Ifz(offset=0, condition=jvm.CmpOpr.Eq, target=5),
        jvm.Push(offset=0, type=jvm.Int(), value=left),
        jvm.Store(offset=0, type=jvm.Int(), index=1),
        jvm.Goto(offset=0, target=7),
        jvm.Push(offset=0, type=jvm.Int(), value=right),
        jvm.Store(offset=0, type=jvm.Int(), index=1),
    ]


@pytest.mark.parametrize(
    "domain, errors",
    [
        (Interval, {"divide by zero"}),
        (SignInterval, set()),
    ],
)
def test_branch_join_and_division_in_interpreter(domain, errors):
    instructions = choose(-5, 5) + [
        jvm.Push(offset=0, type=jvm.Int(), value=10),
        jvm.Load(offset=0, type=jvm.Int(), index=1),
        jvm.Binary(offset=0, type=jvm.Int(), operant=jvm.BinaryOpr.Div),
        jvm.Return(offset=0, type=jvm.Int()),
    ]
    outcomes, _ = execute(instructions, AnalysisConfig(integer_domain=domain))
    assert outcomes == {"ok"} | errors


@pytest.mark.parametrize("domain", DOMAINS)
def test_interval_arithmetic_proves_bounded_assertion(domain):
    instructions = choose(2, 5) + [
        jvm.Load(offset=0, type=jvm.Int(), index=1),
        jvm.Push(offset=0, type=jvm.Int(), value=3),
        jvm.Binary(offset=0, type=jvm.Int(), operant=jvm.BinaryOpr.Add),
        jvm.Push(offset=0, type=jvm.Int(), value=10),
        jvm.If(offset=0, condition=jvm.CmpOpr.Lt, target=13),
        jvm.New(offset=0, classname=jvm.ClassName("java.lang.AssertionError")),
        jvm.Return(offset=0, type=None),
    ]
    outcomes, _ = execute(instructions, AnalysisConfig(integer_domain=domain))
    assert outcomes == {"ok"}


@pytest.mark.parametrize("domain", DOMAINS)
def test_loop_widening_converges(domain):
    instructions = [
        jvm.Push(offset=0, type=jvm.Int(), value=0),
        jvm.Store(offset=0, type=jvm.Int(), index=0),
        jvm.Incr(offset=0, index=0, amount=1),
        jvm.Goto(offset=0, target=2),
    ]
    outcomes, ai = execute(
        instructions,
        AnalysisConfig(integer_domain=domain),
        signature="Example.loop:()V",
        locals_count=1,
    )
    assert outcomes == set()
    assert max(ai.updates.values()) > 3
    assert not ai.worklist


@pytest.mark.parametrize("domain", DOMAINS)
@pytest.mark.parametrize(
    "input_text, expected",
    [
        ("(s'hello')", {"ok"}),
        ("(s'not hello')", {"assertion error"}),
        ("ALL", {"ok", "assertion error", "null pointer"}),
    ],
)
def test_string_execution_with_new_domains(monkeypatch, domain, input_text, expected):
    monkeypatch.chdir(Path(__file__).resolve().parents[3])
    suite, effect = jpamb.setup()
    method = jpamb.parse_methodid("jpamb.cases.Strings.sayHello:(Ljava/lang/String;)V")
    ai = static.AbstractInterpreter.initial(
        jpamb.Bytecode(suite, effect, {}),
        method,
        jpamb.parse_input(input_text),
        AnalysisConfig(integer_domain=domain, strings=True),
    )
    outcomes = set()
    for _ in range(100):
        if not ai.worklist:
            break
        _, finals = ai.step()
        outcomes |= finals
    assert not ai.worklist and outcomes == expected


@pytest.mark.parametrize(
    "selection",
    [
        "interval",
        "sign,interval",
        "interval,string",
        "sign,interval,string",
    ],
)
def test_new_cli_modes_and_trace_serialization(selection):
    from test_strings import run_entrypoint

    from jpamb.interpret import Response

    info = run_entrypoint("analyse", ["--abstractions", selection, "info"])
    assert set(info.stdout.splitlines()[3].split(",")) == {
        "static",
        "python",
        *selection.split(","),
    }
    method = "jpamb.cases.Simple.divideByN:(I)I"
    result = run_entrypoint("analyse", ["--abstractions", selection, method])
    predictions = dict(line.split(";") for line in result.stdout.splitlines())
    assert predictions["divide by zero"] == predictions["ok"] == "maybe"
    trace = run_entrypoint(
        "interpret", ["--abstractions", selection, method, "(2)", "100"]
    )
    response, warnings = Response.parse(trace.stdout)
    assert response is not None and response.steps and not warnings


@pytest.mark.parametrize("domain", DOMAINS)
def test_negation_and_increment(domain):
    instructions = [
        jvm.Push(offset=0, type=jvm.Int(), value=4),
        jvm.Store(offset=0, type=jvm.Int(), index=0),
        jvm.Incr(offset=0, index=0, amount=2),
        jvm.Load(offset=0, type=jvm.Int(), index=0),
        jvm.Negate(offset=0, type=jvm.Int()),
        jvm.Return(offset=0, type=jvm.Int()),
    ]
    outcomes, ai = execute(
        instructions,
        AnalysisConfig(integer_domain=domain),
        signature="Example.values:()I",
        locals_count=1,
    )
    assert outcomes == {"ok"}
    returned = next(state for pc, state in ai.states.items() if pc.offset == 5)
    assert returned.stack == (domain.abstract([StackInt(-6)]),)
