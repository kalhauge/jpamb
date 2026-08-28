import jvm, jpamb, jpamb_utils

import sys

from hypothesis import given, strategies as st

suite, eff = jpamb.setup()


def st_casemethods():
    methods = list(suite.case_methods().keys())
    return st.sampled_from(methods)


@given(st_casemethods())
def test_findmethod(method):
    assert isinstance(suite.findmethod(method, eff=eff), dict)


def st_caseopcodes():
    opcodes = sorted(set(suite.case_opcodes(eff=eff)), key=str)
    return st.sampled_from(opcodes)


@given(st_casemethods())
def test_parse_opcode(method):
    for opcode in suite.findmethod(method, eff=eff)["code"]["bytecode"]:
        op = jvm.Opcode.from_json(opcode)
        assert isinstance(op, jvm.Opcode)


@given(st_caseopcodes())
def test_opcode_correct(op):
    assert isinstance(op, jvm.Opcode)


@given(st_caseopcodes())
def test_opcode_str(op):
    assert str(op)


@given(st_caseopcodes())
def test_opcode_repr(op):
    assert repr(op)


@given(st_caseopcodes())
def test_opcode_real(op):
    assert op.real()


@given(st_caseopcodes())
def test_opcode_hash(op):
    assert hash(op)
