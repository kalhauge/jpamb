from hypothesis import assume, given, note
from hypothesis import strategies as st

import sexpr
import jpamb


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
