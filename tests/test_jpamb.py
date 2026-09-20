from hypothesis import given, note
from hypothesis import strategies as st

import jpamb
import sexpr


@st.composite
def st_analysis_infos(draw):
    return jpamb.AnalysisInfo(
        name=draw(st.text()),
        version=draw(st.text()),
        group=draw(st.text()),
        tags=draw(st.tuples(st.text())),
        system=draw(st.text()),
    )


@given(st_analysis_infos())
def test_analysis_info_from_sexpr(analysis):
    expr = sexpr.sexpr(analysis)
    note(expr)
    assert analysis == jpamb.AnalysisInfo.from_sexpr(expr)


@st.composite
def st_queries(draw):
    return draw(st.sampled_from(jpamb.QUERIES))


@st.composite
def st_durations(draw):
    return jpamb.Duration(
        absolute=draw(st.integers(min_value=0)),
        relative=draw(st.floats(allow_nan=False)),
    )


@given(st_durations())
def test_durations_from_sexpr(it):
    expr = sexpr.sexpr(it)
    note(expr)
    assert it == jpamb.Duration.from_sexpr(expr)


# suite, _eff = jpamb.setup()
#
#
# def st_cases():
#     return st.sampled_from(suite.cases)
#
#
# @given(st_cases())
# def test_cases_from_sexpr(it):
#     expr = sexpr.sexpr(it)
#     note(expr)
#     assert it == jpamb.Case.from_sexpr(expr)
