from collections import OrderedDict

from hypothesis import HealthCheck, given, note, settings
from hypothesis import strategies as st

import jpamb
import jpamb.analyse
import sexpr

from . import test_jvm
from .test_jpamb import (
    st_analysis_infos,
    st_categories,
    st_durations,
    st_predictions,
    st_queries,
    st_trackers,
)


@st.composite
def st_responses(draw):
    return jpamb.analyse.Response(
        predictions=draw(st.dictionaries(st_queries(), st_predictions())),
    )


@given(st_responses())
def test_responses_from_sexpr(response):
    expr = sexpr.sexpr(response)
    note(expr)
    assert response == jpamb.analyse.Response.from_sexpr(expr)


@st.composite
def st_analysis_results(draw):
    return jpamb.analyse.Result(
        response=draw(st_responses()),
        duration=draw(st_durations()),
        calibrates=draw(st.lists(st.integers(min_value=0)).map(tuple)),
    )


@given(st_analysis_results())
def test_analysis_results_from_sexpr(it):
    expr = sexpr.sexpr(it)
    note(expr)
    out = jpamb.analyse.Result.from_sexpr(expr)
    note(f"{it.response.predictions=}")
    note(f"{out.response == it.response=}")
    note(f"{type(out.response)=}")
    note(f"{type(it.response)=}")
    assert type(out.response) == type(it.response)
    assert out == it


@st.composite
def st_analysis_configs(draw):
    return jpamb.analyse.Config(
        cmd=draw(st.lists(st.text()).map(tuple)),
        analysis=draw(st_analysis_infos()),
        experiments=draw(
            st.lists(
                st.tuples(
                    test_jvm.st_absmethodids(),
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
    assert it == jpamb.analyse.Config.from_sexpr(expr)


@st.composite
def st_analysis_summaries(draw):
    return jpamb.analyse.Summary(
        config=draw(st_analysis_configs()),
        results=draw(
            st.dictionaries(
                test_jvm.st_absmethodids(),
                st.lists(st_analysis_results()),
            )
        ),
    )


@settings(suppress_health_check=[HealthCheck.too_slow])
@given(st_analysis_summaries())
def test_analysis_summary_from_sexpr(it):
    expr = sexpr.sexpr(it)
    note(expr)
    assert it == jpamb.analyse.Summary.from_sexpr(expr)


@st.composite
def st_analysis_states(draw):
    config = draw(st_analysis_configs())
    return jpamb.analyse.State(
        config=config,
        progress=draw(st.integers(min_value=0, max_value=len(config.experiments))),
        results=draw(
            st.dictionaries(
                test_jvm.st_absmethodids(),
                st.lists(st_analysis_results()),
            )
        ),
        categories=draw(st.dictionaries(st_categories(), st_trackers())),
    )


@settings(suppress_health_check=[HealthCheck.too_slow])
@given(st_analysis_states())
def test_analysis_states_from_sexpr(it):
    expr = sexpr.sexpr(it)
    note(expr)
    assert it == jpamb.analyse.State.from_sexpr(expr)
