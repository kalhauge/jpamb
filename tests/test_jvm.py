from hypothesis import given, note
from hypothesis import strategies as st

import jvm
import sexpr


def test_singletons():
    assert jvm.Boolean() is jvm.Boolean()
    assert jvm.Int() is jvm.Int()
    assert jvm.Char() is jvm.Char()
    assert jvm.Int() is not jvm.Boolean()

    assert jvm.Array(jvm.Boolean()) is jvm.Array(jvm.Boolean())
    assert jvm.Array(jvm.Boolean()) is not jvm.Array(jvm.Int())


# def test_value_parser():
#     assert jvm.ValueParser.parse("1, 's', [I:10, 32]") == [
#         jvm.Value.int(1),
#         jvm.Value.char("s"),
#         jvm.Value.array(jvm.Int(), [10, 32]),
#     ]


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
def st_methodid(draw, params: jvm.Parameters | None = None):
    if params is None:
        params = draw(st_parameter_types())
    return jvm.MethodID(
        name=draw(st.sampled_from(["main", "<init>", "equals", "tostring"])),
        params=params,
        return_type=draw(st.none() | st_types()),
    )


@given(st_methodid())
def test_methodid_decode(it):
    code = it.encode()
    note(code)
    assert jvm.MethodID.decode(code) == it


@st.composite
def st_absmethodids(draw, params: jvm.Parameters | None = None):
    return jvm.AbsMethodID(
        classname=draw(st_classnames()),
        extension=draw(st_methodid(params=params)),
    )


@given(st_absmethodids())
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
    return st.recursive(
        st_primtypes(),
        extend=lambda r: r.map(jvm.Array),
        max_leaves=2,
    )


@given(st_types())
def test_types_math_should_return_string(tp):
    assert isinstance(tp.math(), str)


@given(st_types())
def test_types_sexpr(it):
    expr = sexpr.sexpr(it)
    note(expr)
    assert it == jvm.Type.from_sexpr(expr)
