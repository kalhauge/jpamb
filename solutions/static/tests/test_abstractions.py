import abstractions as ab
import pytest
from hypothesis import given
from hypothesis import strategies as st

import jvm
import jvm.state as jvms


def st_i32():
    return st.integers(min_value=-(2**31), max_value=2**31 - 1)


def st_u32():
    return st.integers(min_value=0, max_value=2**32)


def st_stack_ints():
    return st_i32().map(jvms.StackInt)


def st_stack_refs():
    return st_u32().map(jvms.StackReference)


def st_signset():
    return (
        st.sets(st.integers(min_value=-1, max_value=1)).map(frozenset).map(ab.SignSet)
    )


@given(st_signset(), st_signset(), st_signset())
def test_signset_is_poset(a: ab.SignSet, b: ab.SignSet, c: ab.SignSet):
    ab.is_poset(a, b, c)


@given(st_signset(), st_signset(), st_signset())
def test_signset_is_lattice(a: ab.SignSet, b: ab.SignSet, c: ab.SignSet):
    ab.is_lattice(a, b, c)


@given(st.sets(st_stack_ints()), st_signset())
def test_signset_is_galoi(a: set[jvms.StackInt], b: ab.SignSet):
    ab.is_galoi(a, b)


def arithmetic(opr, x, y):
    left, right = x.value, y.value
    match opr:
        case jvm.BinaryOpr.Add:
            value = left + right
        case jvm.BinaryOpr.Sub:
            value = left - right
        case jvm.BinaryOpr.Mul:
            value = left * right
        case jvm.BinaryOpr.Div | jvm.BinaryOpr.Rem:
            quotient = abs(left) // abs(right)
            if (left < 0) != (right < 0):
                quotient = -quotient
            if opr == jvm.BinaryOpr.Div:
                value = quotient
            else:
                value = left - quotient * right
    # Java int results wrap to the signed 32-bit range.
    return jvms.StackInt((value + 2**31) % 2**32 - 2**31)


@given(
    st.sampled_from(list(jvm.BinaryOpr)),
    st.sets(st_stack_ints()),
    st.sets(st_stack_ints()),
)
def test_signset_arithmetic(opr, xs, ys):
    expected_values = []
    expected_errors = set()
    for left in xs:
        for right in ys:
            try:
                expected_values.append(arithmetic(opr, left, right))
            except ZeroDivisionError:
                expected_errors.add("divide by zero")
    result, errors = ab.SignSet.abstract(xs).arithmetic(ab.SignSet.abstract(ys), opr)
    assert ab.SignSet.abstract(expected_values) <= result
    assert errors == expected_errors


@pytest.mark.parametrize("operation", list(jvm.BinaryOpr))
def test_arithmetic_boundaries_and_empty_sets(operation):
    values = [-2**31, -2**31 + 1, -65536, -2, -1, 0, 1, 2, 65536, 2**31 - 1]
    for left in values:
        for right in values:
            x, y = jvms.StackInt(left), jvms.StackInt(right)
            result, errors = ab.SignSet.abstract([x]).arithmetic(
                ab.SignSet.abstract([y]), operation
            )
            try:
                expected = arithmetic(operation, x, y)
            except ZeroDivisionError:
                assert errors == {"divide by zero"}
                assert result == ab.SignSet.bot()
            else:
                assert expected in result
                assert errors == set()
    assert ab.SignSet.bot().arithmetic(ab.SignSet.top(), operation) == (ab.SignSet.bot(), set())
    assert ab.SignSet.top().arithmetic(ab.SignSet.bot(), operation) == (ab.SignSet.bot(), set())


def compare(opr, x, y):
    match opr:
        case jvm.CmpOpr.Eq:
            return x.value == y.value
        case jvm.CmpOpr.Ne:
            return x.value != y.value
        case jvm.CmpOpr.Lt:
            return x.value < y.value
        case jvm.CmpOpr.Le:
            return x.value <= y.value
        case jvm.CmpOpr.Gt:
            return x.value > y.value
        case jvm.CmpOpr.Ge:
            return x.value >= y.value
        case _:
            raise NotImplementedError("TODO")


@given(
    st.sampled_from(list(jvm.CmpOpr)),
    st.sets(st_stack_ints()),
    st.sets(
        st_stack_ints(),
    ),
)
def test_signset_compare(
    opr: jvm.CmpOpr, xs: set[jvms.StackInt], ys: set[jvms.StackInt]
):
    real = {compare(opr, x, y) for x in xs for y in ys}
    abstracted = set(ab.SignSet.abstract(xs).compare(ab.SignSet.abstract(ys), opr))
    assert real <= abstracted


@st.composite
def st_interval(draw):
    if draw(st.booleans()):
        return ab.Interval.bot()
    lower, upper = sorted([draw(st_i32()), draw(st_i32())])
    return ab.Interval(lower, upper)


@given(st_interval(), st_interval(), st_interval())
def test_interval_is_poset(a: ab.Interval, b: ab.Interval, c: ab.Interval):
    ab.is_poset(a, b, c)


@given(st_interval(), st_interval(), st_interval())
def test_interval_is_lattice(a: ab.Interval, b: ab.Interval, c: ab.Interval):
    ab.is_lattice(a, b, c)


@given(st.sets(st_stack_ints()), st_interval())
def test_interval_is_galoi(a: set[jvms.StackInt], b: ab.Interval):
    ab.is_galoi(a, b)


@pytest.mark.parametrize("operation", list(jvm.CmpOpr))
def test_signset_compare_all_sign_combinations(operation):
    # Two representatives of each nonzero sign exercise <, == and >.
    values = [jvms.StackInt(value) for value in (-2, -1, 0, 1, 2)]
    sign_sets = []
    for mask in range(8):
        signs = frozenset(sign for bit, sign in enumerate((-1, 0, 1)) if mask & (1 << bit))
        sign_sets.append(ab.SignSet(signs))

    for left in sign_sets:
        for right in sign_sets:
            expected = {
                compare(operation, x, y)
                for x in values if x in left
                for y in values if y in right
            }
            assert set(left.compare(right, operation)) == expected
