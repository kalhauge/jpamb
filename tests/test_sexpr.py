from dataclasses import dataclass

from hypothesis import assume, given, note
from hypothesis import strategies as st

import sexpr


def test_pretty():
    assert sexpr.pretty("ref 0") == "|ref 0|"
    assert sexpr.pretty("hello") == "hello"
    assert (
        sexpr.pretty([sexpr.item([]), sexpr.option("hello", "world")])
        == "(() :hello world)"
    )


@st.composite
def st_options(draw, values):
    key = draw(st.text())
    value = draw(values)
    return sexpr.Option(key, value)


def st_sexpr():
    return st.recursive(st.text(), extend=lambda xs: st.lists(st_options(xs)))


@given(st_sexpr())
def test_tripping(expr):
    string = sexpr.pretty(expr)
    note(f"{string=}")
    items = sexpr.from_string(string)
    note(f"{items=}")
    assert len(items) == 1
    assert items[0] == expr


@given(st_sexpr())
def test_tripping_indent(expr):
    note(f"{expr=}")
    string = sexpr.pretty(expr, indent=1)
    note(f"{string=}")
    items = sexpr.from_string(string)
    assert len(items) == 1
    assert items[0] == expr


def test_data():
    assert sexpr.data("hello", key="value") == [
        sexpr.Option.unkeyed("hello"),
        sexpr.Option("key", "value"),
    ]


@given(
    st.text(),
    st.lists(st_sexpr()),
    st.dictionaries(st.text(min_size=1), st_sexpr()),
)
def test_data_tripping(key, args, kwargs):
    data = sexpr.data(key, *args, **kwargs)

    note(data)

    (key2, args2, kwargs2) = sexpr.data_from_sexpr(data)

    assert key == key2
    assert args == args2
    assert kwargs == kwargs2


@given(st.floats())
def test_float_tripping(value):
    data = sexpr.sexpr(value)
    assert repr(value) == repr(sexpr.float_from_sexpr(data))


@given(st.integers())
def test_int_tripping(value):
    data = sexpr.sexpr(value)
    assert value == sexpr.int_from_sexpr(data)
