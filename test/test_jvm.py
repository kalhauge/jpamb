from jpamb import jvm

from hypothesis import given, strategies as st


def test_singletons():
    assert jvm.Boolean() is jvm.Boolean()
    assert jvm.Int() is jvm.Int()
    assert jvm.Char() is jvm.Char()
    assert jvm.Int() is not jvm.Boolean()

    assert jvm.Array(jvm.Boolean()) is jvm.Array(jvm.Boolean())
    assert jvm.Array(jvm.Boolean()) is not jvm.Array(jvm.Int())


def test_value_parser():
    assert jvm.ValueParser.parse("1, 's', [I:10, 32]") == [
        jvm.Value.int(1),
        jvm.Value.char("s"),
        jvm.Value.array(jvm.Int(), [10, 32]),
    ]


def jvm_classnames():
    return st.sampled_from(["java.lang.Object", "a.simple.ClassName"]).map(
        jvm.ClassName.decode
    )


def jvm_primtypes():
    return st.sampled_from(
        [
            jvm.Boolean(),
            jvm.Int(),
            jvm.Char(),
            jvm.Double(),
            jvm.Long(),
            jvm.Reference(),
        ]
    ) | jvm_classnames().map(jvm.Object)


def jvm_types():
    return st.recursive(jvm_primtypes(), extend=lambda r: r.map(jvm.Array))


def jvm_values():
    return (
        st.integers().map(jvm.Value.int)
        | st.booleans().map(jvm.Value.boolean)
        | st.text(min_size=1, max_size=1).map(jvm.Value.char)
    )


@given(jvm_types())
def test_types_math_should_return_string(tp):
    assert isinstance(tp.math(), str)


@given(jvm_values())
def test_values_math_should_return_string(v):
    assert isinstance(v.math(), str)
