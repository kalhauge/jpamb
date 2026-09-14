from hypothesis import given, note
from hypothesis import strategies as st

import jvm
import sexpr
from jvm import state

from . import test_jvm


@st.composite
def st_pcs(draw):
    return state.PC(draw(test_jvm.st_absmethodids()), draw(st.integers(min_value=0)))


@given(st_pcs())
def test_pc_decodeencode(it):
    code = it.encode()
    note(f"{code=}")
    assert it == state.PC.decode(code)


@given(st_pcs())
def test_pc_sexpr(it):
    code = sexpr.sexpr(it)
    note(f"{code=}")
    assert it == state.PC.from_sexpr(code)


def st_stack_values():
    return (
        st.integers().map(state.StackInt)
        | (st.integers(min_value=0)).map(state.StackReference)
        | st.floats(allow_nan=False).map(state.StackFloat)
    )


def st_operand_stacks():
    return st.lists(st_stack_values()).map(state.OperandStack.from_values)


@given(st_operand_stacks())
def test_operand_stacks_sexpr(it):
    code = sexpr.sexpr(it)
    note(f"{code=}")
    assert it == state.OperandStack.from_sexpr(code)


def st_fieldids():
    return st.builds(
        jvm.FieldID,
        name=st.text(
            min_size=1,
            max_size=16,
            alphabet=st.characters(
                whitelist_categories=("L",), whitelist_characters="_"
            ),
        ),
        type=test_jvm.st_types(),
    )


def st_heap_arrays():
    return st.builds(
        state.HeapArray,
        contains=test_jvm.st_types(),
        values=st.lists(st.integers()),
    )


def st_heap_objects():
    return st.builds(
        state.HeapObject,
        classname=test_jvm.st_classnames(),
        fields=st.dictionaries(st_fieldids(), st_stack_values()),
    )


def st_heap_strings():
    return st.builds(state.HeapString, content=st.text())


def st_heap_values():
    return st_heap_arrays() | st_heap_objects() | st_heap_strings()


def st_frames():
    return st.builds(
        state.Frame,
        locals=st.lists(st.none() | st_stack_values()).map(state.Locals),
        stack=st_operand_stacks(),
        pc=st_pcs(),
    )


def st_call_stacks():
    return st.lists(st_frames(), max_size=8).map(state.CallStack.from_frames)


def st_states():
    return st.builds(
        state.State,
        heap=st.lists(st_heap_values()),
        frames=st_call_stacks(),
    )


@given(st_heap_arrays())
def test_heap_array_sexpr(it):
    code = sexpr.sexpr(it)
    note(f"{code=}")
    assert it == state.HeapArray.from_sexpr(code)


@given(st_heap_objects())
def test_heap_object_sexpr(it):
    code = sexpr.sexpr(it)
    note(f"{code=}")
    assert it == state.HeapObject.from_sexpr(code)


@given(st_heap_strings())
def test_heap_string_sexpr(it):
    code = sexpr.sexpr(it)
    note(f"{code=}")
    assert it == state.HeapString.from_sexpr(code)


@given(st_frames())
def test_frame_sexpr(it):
    code = sexpr.sexpr(it)
    note(f"{code=}")
    assert it == state.Frame.from_sexpr(code)


@given(st_call_stacks())
def test_call_stack_sexpr(it):
    code = sexpr.sexpr(it)
    note(f"{code=}")
    assert it == state.CallStack.from_sexpr(code)
