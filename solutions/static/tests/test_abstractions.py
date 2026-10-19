import abstractions as ab
import pytest
from hypothesis import given
from hypothesis import strategies as st

import jvm
import jvm.state as jvms


def st_i32():
    return st.integers(min_value=-(2**31) - 1, max_value=2**31)


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
    match opr:
        case jvm.BinaryOpr.Add:
            return jvms.StackInt(x.value + y.value)
        case _:
            raise NotImplementedError("TODO")



@given(
    st.sampled_from([jvm.BinaryOpr.Add]),
    st.sets(st_stack_ints()),
    st.sets(
        st_stack_ints(),
    ),
)
def test_signset_arithmetic(
    opr: jvm.BinaryOpr, xs: set[jvms.StackInt], ys: set[jvms.StackInt]
):
    real = ab.SignSet.abstract(arithmetic(opr, x, y) for x in xs for y in ys)
    (abstracted, _errs) = ab.SignSet.abstract(xs).arithmetic(
        ab.SignSet.abstract(ys), opr
    )
    assert real <= abstracted

def test_sign_arithmetic_sub():
    positive = ab.SignSet.abstract([jvms.StackInt(2)])
    negative = ab.SignSet.abstract([jvms.StackInt(-3)])

    result, errors = positive.arithmetic(
        negative,
        jvm.BinaryOpr.Sub,
    )

    assert result == ab.SignSet.abstract([jvms.StackInt(1)])
    assert errors == set()


def test_sign_arithmetic_mul():
    positive = ab.SignSet.abstract([jvms.StackInt(2)])
    negative = ab.SignSet.abstract([jvms.StackInt(-3)])

    result, errors = positive.arithmetic(
        negative,
        jvm.BinaryOpr.Mul,
    )

    assert result == ab.SignSet.abstract([jvms.StackInt(-1)])
    assert errors == set()


def test_sign_arithmetic_div():
    positive = ab.SignSet.abstract([jvms.StackInt(4)])
    negative = ab.SignSet.abstract([jvms.StackInt(-2)])

    result, errors = positive.arithmetic(
        negative,
        jvm.BinaryOpr.Div,
    )

    assert result == ab.SignSet(frozenset({-1, 0}))
    assert errors == set()


def test_sign_arithmetic_div_by_zero():
    positive = ab.SignSet.abstract([jvms.StackInt(4)])
    zero = ab.SignSet.abstract([jvms.StackInt(0)])

    result, errors = positive.arithmetic(
        zero,
        jvm.BinaryOpr.Div,
    )

    assert "divide by zero" in errors


def test_sign_arithmetic_rem():
    positive = ab.SignSet.abstract([jvms.StackInt(5)])
    positive_divisor = ab.SignSet.abstract([jvms.StackInt(2)])

    result, errors = positive.arithmetic(
        positive_divisor,
        jvm.BinaryOpr.Rem,
    )

    assert result == ab.SignSet(frozenset({0, 1}))
    assert errors == set()
    
def compare(opr, x, y):
    match opr:
        case jvm.CmpOpr.Le:
            return x.value <= y.value
        case _:
            raise NotImplementedError("TODO")


@given(
    st.sampled_from([jvm.CmpOpr.Le]),
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
    kind = draw(st.integers(min_value=0, max_value=3))

    if kind == 0:
        # finite interval
        min_value, max_value = sorted([draw(st_i32()), draw(st_i32())])
        return ab.Interval(min_value, max_value)

    elif kind == 1:
        # [-inf, max]
        return ab.Interval(None, draw(st_i32()))

    elif kind == 2:
        # [min, +inf]
        return ab.Interval(draw(st_i32()), None)

    else:
        # [-inf, +inf]
        return ab.Interval(None, None)


@given(st_interval(), st_interval(), st_interval())
def test_interval_is_poset(a: ab.Interval, b: ab.Interval, c: ab.Interval):
    ab.is_poset(a, b, c)


@given(st_interval(), st_interval(), st_interval())
def test_interval_is_lattice(a: ab.Interval, b: ab.Interval, c: ab.Interval):
    ab.is_lattice(a, b, c)


@given(st.sets(st_stack_ints()), st_interval())
def test_lnterval_is_galoi(a: set[jvms.StackInt], b: ab.Interval):
    ab.is_galoi(a, b)

@given(
    st.sets(st_stack_ints()),
    st.sets(st_stack_ints()),
)
def test_interval_arithmetic_add(
    xs: set[jvms.StackInt],
    ys: set[jvms.StackInt],
):
    real = ab.Interval.abstract(
        jvms.StackInt(x.value + y.value)
        for x in xs
        for y in ys
    )

    abstracted, _errs = ab.Interval.abstract(xs).arithmetic(
        ab.Interval.abstract(ys),
        jvm.BinaryOpr.Add,
    )

    assert real <= abstracted

@given(
    st.sets(st_stack_ints()),
    st.sets(st_stack_ints()),
)
def test_interval_arithmetic_sub(
    xs: set[jvms.StackInt],
    ys: set[jvms.StackInt],
):
    real = ab.Interval.abstract(
        jvms.StackInt(x.value - y.value)
        for x in xs
        for y in ys
    )

    abstracted, _errs = ab.Interval.abstract(xs).arithmetic(
        ab.Interval.abstract(ys),
        jvm.BinaryOpr.Sub,
    )

    assert real <= abstracted

@given(
    st.sets(st_stack_ints()),
    st.sets(st_stack_ints()),
)
def test_interval_arithmetic_mul(
    xs: set[jvms.StackInt],
    ys: set[jvms.StackInt],
):
    real = ab.Interval.abstract(
        jvms.StackInt(x.value * y.value)
        for x in xs
        for y in ys
    )

    abstracted, _errs = ab.Interval.abstract(xs).arithmetic(
        ab.Interval.abstract(ys),
        jvm.BinaryOpr.Mul,
    )

    assert real <= abstracted

@given(
    st.sets(st_stack_ints()),
    st.sets(st_stack_ints()),
)
def test_interval_arithmetic_div(
    xs: set[jvms.StackInt],
    ys: set[jvms.StackInt],
): 
    def trunc_div(a: int, b: int) -> int:
        result = abs(a) // abs(b)
        return result if (a >= 0) == (b >= 0) else -result

    real = ab.Interval.abstract(
        jvms.StackInt(trunc_div(x.value, y.value))
        for x in xs
        for y in ys
        if y.value != 0
    )

    abstracted, errors = ab.Interval.abstract(xs).arithmetic(
        ab.Interval.abstract(ys),
        jvm.BinaryOpr.Div,
    )

    assert real <= abstracted

    if xs and any(y.value == 0 for y in ys):
        assert "divide by zero" in errors

    
