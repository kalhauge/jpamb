import pytest
from hypothesis import given, note
from hypothesis import strategies as st

import jvm
import sexpr
from jpamb.case import (
    Array,
    Boolean,
    Char,
    Float,
    Input,
    InputParser,
    Int,
    String,
    Value,
)


@pytest.mark.parametrize(
    "value,expected",
    [
        (Int(42), "42"),
        (Boolean(True), "true"),
        (Boolean(False), "false"),
        (Float(1.5), "1.5"),
        (Char("a"), "'a'"),
        (String("hello"), "s'hello'"),
        (Array(jvm.Int(), (10, 32)), "[I:10, 32]"),
        (Array(jvm.Char(), ("a", "b")), "[C:'a', 'b']"),
    ],
)
def test_encode(value, expected):
    assert value.encode() == expected


@pytest.mark.parametrize(
    "value",
    [
        Int(42),
        Int(-1),
        Boolean(True),
        Boolean(False),
        Float(1.5),
        Float(-0.25),
        Char("a"),
        String("hello world"),
        String(""),
        Array(jvm.Int(), (10, 32)),
        Array(jvm.Int(), ()),
        Array(jvm.Char(), ("a", "b")),
    ],
)
def test_sexpr_roundtrip(value):
    expr = sexpr.sexpr(value)
    assert sexpr.issexpr(expr)
    assert Value.from_sexpr(expr) == value


@pytest.mark.parametrize(
    "value",
    [
        Int(-(2**31)),
        Int(2**31 - 1),
        Char("c"),
        Array(jvm.Int(), (-1, 0, 5)),
    ],
)
def test_sexpr_roundtrip_examples(value):
    expr = sexpr.sexpr(value)
    assert Value.from_sexpr(expr) == value


def st_int_values():
    return st.integers().map(Int)


def st_boolean_values():
    return st.booleans().map(Boolean)


def st_char_values():
    return st.characters(blacklist_characters="'").map(Char)


def st_string_values():
    return st.text(st.characters(blacklist_characters="'")).map(String)


def st_int_array_values():
    return st.lists(st.integers()).map(tuple).map(lambda vs: Array(jvm.Int(), vs))


def st_char_array_values():
    return (
        st.lists(st.characters(blacklist_characters="'"))
        .map(tuple)
        .map(lambda vs: Array(jvm.Char(), vs))
    )


def st_values():
    return st.one_of(
        st_int_values(),
        st_boolean_values(),
        st_char_values(),
        st_string_values(),
        st_int_array_values(),
        st_char_array_values(),
    )


@given(st_values())
def test_value_encode_decode_hypothesis(value):
    assert InputParser.parse(value.encode()) == [value]


@given(st_values())
def test_value_sexpr_roundtrip_hypothesis(value):
    expr = sexpr.sexpr(value)
    note(expr)
    assert Value.from_sexpr(expr) == value


@given(st.lists(st_values()))
def test_input_encode_decode_hypothesis(values):
    input = Input(tuple(values))
    assert Input.decode(input.encode()) == input


def test_char_length_assertion():
    with pytest.raises(AssertionError):
        Char("ab")


def test_type_matches_jvm_type():
    assert Int(1).type is jvm.Int()
    assert Boolean(True).type is jvm.Boolean()
    assert Float(1.0).type is jvm.Float()
    assert Char("a").type is jvm.Char()
    assert String("").type == jvm.Object(jvm.ClassName("java.lang.String"))
    assert Array(jvm.Int(), (1,)).type == jvm.Array(jvm.Int())
