from hypothesis import given
from hypothesis import note, strategies as st

from jpamb import jvm


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


def st_classnames():
    return st.sampled_from(["java.lang.Object", "a.simple.ClassName"]).map(
        jvm.ClassName.decode
    )


@given(st_classnames())
def test_classname_decode(it):
    code = it.encode()
    note(code)
    assert jvm.ClassName.decode(code) == it


@st.composite
def st_parameter_types(draw):
    return jvm.ParameterType(draw(st.lists(st_types(), max_size=8).map(tuple)))


@given(st_parameter_types())
def test_parameter_type_decode(it):
    code = it.encode()
    note(code)
    assert jvm.ParameterType.decode(code) == it


@st.composite
def st_methodid(draw):
    return jvm.MethodID(
        name=draw(st.sampled_from(["main", "<init>", "equals", "tostring"])),
        params=draw(st_parameter_types()),
        return_type=draw(st.none() | st_types()),
    )


@given(st_methodid())
def test_methodid_decode(it):
    code = it.encode()
    note(code)
    assert jvm.MethodID.decode(code) == it


@st.composite
def st_absmethodid(draw):
    return jvm.AbsMethodID(
        classname=draw(st_classnames()),
        extension=draw(st_methodid()),
    )


@given(st_absmethodid())
def test_absmethodid_decode(it):
    code = it.encode()
    note(code)
    assert jvm.AbsMethodID.decode(code) == it


def st_primtypes():
    return st.sampled_from(
        [
            jvm.Boolean(),
            jvm.Int(),
            jvm.Char(),
            jvm.Double(),
            jvm.Long(),
            jvm.Reference(),
        ]
    ) | st_classnames().map(jvm.Object)


def st_types():
    return st.recursive(st_primtypes(), extend=lambda r: r.map(jvm.Array))


def st_values():
    return (
        st.integers().map(jvm.Value.int)
        | st.booleans().map(jvm.Value.boolean)
        | st.text(min_size=1, max_size=1).map(jvm.Value.char)
    )


@given(st_types())
def test_types_math_should_return_string(tp):
    assert isinstance(tp.math(), str)


@given(st_values())
def test_values_math_should_return_string(v):
    assert isinstance(v.math(), str)
