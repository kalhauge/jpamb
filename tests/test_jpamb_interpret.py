from hypothesis import HealthCheck, given, note, settings
from hypothesis import strategies as st

import jpamb.case
import jpamb.interpret
import sexpr

from . import test_jvm, test_jvm_state
from .test_jpamb import (
    st_analysis_infos,
    st_durations,
)
from .test_jpamb_case import st_values
from .test_sexpr import st_edits, st_sexpr


@st.composite
def st_inputs(draw):
    return jpamb.case.Input(
        values=draw(st.lists(st_values()).map(tuple)),
    )


@st.composite
def st_experiments(draw):
    input = draw(st_inputs() | st.none())
    if input is not None:
        entry = draw(test_jvm.st_absmethodids(params=input.parameter_types()))
    else:
        entry = draw(test_jvm.st_absmethodids())

    return jpamb.case.Experiment(
        entry=entry,
        input=input,
    )


@given(st_experiments())
def test_experiment_from_sexpr(it):
    expr = sexpr.sexpr(it)
    note(expr)
    assert it == jpamb.case.Experiment.from_sexpr(expr)


@st.composite
def st_cases(draw):
    return jpamb.case.Case(
        experiment=draw(st_experiments()),
        result=draw(st.text()),
    )


@st.composite
def st_steps(draw):
    return jpamb.interpret.Step(
        pc=draw(test_jvm_state.st_pcs()),
        edits=tuple(draw(st_edits())),
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
        experiment=draw(st_experiments()),
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
        experiments=draw(st.lists(st_experiments())),
        timeout=draw(st.floats(min_value=0)),
        max_steps=draw(st.integers(min_value=0)),
        abstract=draw(st.booleans()),
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
