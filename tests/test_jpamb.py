from collections import OrderedDict

from hypothesis import given, note
from hypothesis import strategies as st

import jpamb
import sexpr

from . import test_jvm


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
def st_responses(draw):
    return jpamb.Response(
        predictions=draw(st.dictionaries(st_queries(), st_predictions())),
    )


@given(st_responses())
def test_responses_from_sexpr(response):
    expr = sexpr.sexpr(response)
    note(expr)
    assert response == jpamb.Response.from_sexpr(expr)


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
def st_analysis_results(draw):
    return jpamb.AnalysisResult(
        response=draw(st_responses()),
        duration=draw(st_durations()),
        calibrates=draw(st.lists(st.integers(min_value=0)).map(tuple)),
    )


@given(st_analysis_results())
def test_analysis_results_from_sexpr(it):
    expr = sexpr.sexpr(it)
    note(expr)
    assert it == jpamb.AnalysisResult.from_sexpr(expr)


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


@st.composite
def st_analysis_configs(draw):
    return jpamb.AnalysisConfig(
        cmd=draw(st.lists(st.text()).map(tuple)),
        analysis=draw(st_analysis_infos()),
        experiments=draw(
            st.lists(
                st.tuples(
                    test_jvm.st_absmethodid(),
                    st.sets(st_queries()),
                )
            ).map(OrderedDict)
        ),
        iterations=draw(st.integers(min_value=0)),
        timeout=draw(st.floats(min_value=0)),
    )


@given(st_analysis_configs())
def test_analysis_configs_from_sexpr(it):
    expr = sexpr.sexpr(it)
    note(expr)
    assert it == jpamb.AnalysisConfig.from_sexpr(expr)


@st.composite
def st_analysis_summaries(draw):
    return jpamb.AnalysisSummary(
        config=draw(st_analysis_configs()),
        results=draw(
            st.dictionaries(
                test_jvm.st_absmethodid(),
                st.lists(st_analysis_results()),
            )
        ),
    )


@given(st_analysis_summaries())
def test_analysis_symmary_from_sexpr(it):
    expr = sexpr.sexpr(it)
    note(expr)
    assert it == jpamb.AnalysisSummary.from_sexpr(expr)


@st.composite
def st_analysis_states(draw):
    config = draw(st_analysis_configs())
    return jpamb.AnalysisState(
        config=config,
        progress=draw(st.integers(min_value=0, max_value=len(config.experiments))),
        results=draw(
            st.dictionaries(
                test_jvm.st_absmethodid(),
                st.lists(st_analysis_results()),
            )
        ),
        categories=draw(st.dictionaries(st_categories(), st_trackers())),
    )


@given(st_analysis_states())
def test_analysis_states_from_sexpr(it):
    expr = sexpr.sexpr(it)
    note(expr)
    assert it == jpamb.AnalysisState.from_sexpr(expr)
