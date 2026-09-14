from hypothesis import HealthCheck, given, note, settings
from hypothesis import strategies as st

import jpamb.case
import jpamb.interpret
import sexpr

from . import test_jvm, test_jvm_state
from .test_jpamb import (
    st_analysis_infos,
    st_categories,
    st_durations,
    st_trackers,
)
from .test_jpamb_case import st_values
from .test_sexpr import st_sexpr


@st.composite
def st_inputs(draw):
    return jpamb.case.Input(
        values=draw(st.lists(st_values()).map(tuple)),
    )


@st.composite
def st_cases(draw):
    return jpamb.case.Case(
        methodid=draw(test_jvm.st_absmethodids()),
        input=draw(st_inputs()),
        result=draw(st.text()),
    )


@st.composite
def st_steps(draw):
    return jpamb.interpret.Step(
        before=draw(st_sexpr()),
        pc=draw(test_jvm_state.st_pcs()),
        after=draw(st_sexpr()),
    )


@given(st_steps())
def test_steps_from_sexpr(it):
    expr = sexpr.sexpr(it)
    note(expr)
    assert it == jpamb.interpret.Step.from_sexpr(expr)


@st.composite
def st_interpret_responses(draw):
    return jpamb.interpret.Response(
        init=draw(st_sexpr().map(jpamb.interpret.Init)),
        steps=draw(st.lists(st_steps())),
    )


@st.composite
def st_interpret_results(draw):
    return jpamb.interpret.Result(
        case=draw(st_cases()),
        response=draw(st_interpret_responses()),
        duration=draw(st_durations()),
        calibrates=draw(st.lists(st.integers(min_value=0)).map(tuple)),
    )


@settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large])
@given(st_interpret_results())
def test_interpret_results_from_sexpr(it):
    expr = sexpr.sexpr(it)
    note(expr)
    assert it == jpamb.interpret.Result.from_sexpr(expr)


@st.composite
def st_interpret_configs(draw):
    return jpamb.interpret.Config(
        cmd=draw(st.lists(st.text()).map(tuple)),
        analysis=draw(st_analysis_infos()),
        experiments=draw(st.lists(st_cases())),
        timeout=draw(st.floats(min_value=0)),
        max_steps=draw(st.integers(min_value=0)),
    )


@settings(suppress_health_check=[HealthCheck.too_slow])
@given(st_interpret_configs())
def test_interpret_configs_from_sexpr(it):
    expr = sexpr.sexpr(it)
    note(expr)
    assert it == jpamb.interpret.Config.from_sexpr(expr)


@st.composite
def st_interpret_states(draw):
    config = draw(st_interpret_configs())
    return jpamb.interpret.State(
        config=config,
        progress=draw(st.integers(min_value=0)),
        results=draw(st.lists(st_interpret_results())),
        categories=draw(st.dictionaries(st_categories(), st_trackers())),
    )


@settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large])
@given(st_interpret_states())
def test_interpret_states_from_sexpr(it):
    expr = sexpr.sexpr(it)
    note(expr)
    assert it == jpamb.interpret.State.from_sexpr(expr)


@st.composite
def st_interpret_summaries(draw):
    return jpamb.interpret.Summary(
        config=draw(st_interpret_configs()),
        results=draw(st.lists(st_interpret_results())),
    )


@settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large])
@given(st_interpret_summaries())
def test_interpret_summaries_from_sexpr(it):
    expr = sexpr.sexpr(it)
    note(expr)
    assert it == jpamb.interpret.Summary.from_sexpr(expr)
