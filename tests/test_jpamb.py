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
def st_wagers(draw):
    return jpamb.Wager(draw(st.floats(allow_nan=False)))


@given(st_wagers())
def test_wagers_from_sexpr(wager):
    expr = sexpr.sexpr(wager)
    assert sexpr.issexpr(expr)
    note(f"{expr=}")
    assert wager == jpamb.Wager.from_sexpr(expr)


def test_wagers_examples():
    assert sexpr.sexpr(jpamb.Wager(0.0)) == "0.0"


def isfloat(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


@st.composite
def st_categories(draw):
    return jpamb.Category(draw(st.text().filter(lambda a: not isfloat(a))))


@given(st_categories())
def test_categories_from_sexpr(category):
    expr = sexpr.sexpr(category)
    note(expr)
    assert category == jpamb.Category.from_sexpr(expr)


@st.composite
def st_predictions(draw):
    return draw(st_wagers() | st_categories())


@given(st_predictions())
def test_predictions_from_sexpr(prediction):
    expr = sexpr.sexpr(prediction)
    note(expr)
    assert prediction == jpamb.Prediction.from_sexpr(expr)


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


@st.composite
def st_trackers(draw):
    return jpamb.Tracker(
        hits=draw(st.integers(min_value=0)),
        counts=draw(st.integers(min_value=0)),
    )


@given(st_trackers())
def test_tracker_from_sexpr(it):
    expr = sexpr.sexpr(it)
    note(expr)
    assert it == jpamb.Tracker.from_sexpr(expr)


suite, _eff = jpamb.setup()


def st_cases():
    return st.sampled_from(suite.cases)


@given(st_cases())
def test_cases_from_sexpr(it):
    expr = sexpr.sexpr(it)
    note(expr)
    assert it == jpamb.Case.from_sexpr(expr)
