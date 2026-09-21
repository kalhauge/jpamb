from hypothesis import given
from hypothesis import strategies as st

import jpamb
import jvm

suite, eff = jpamb.setup()
benchmark = suite.benchmark(eff=eff)


def st_entries():
    return st.sampled_from(list(benchmark.entries()))


@given(st_entries())
def test_findmethod(entry):
    assert isinstance(suite.findmethod(entry, eff=eff), dict)


@given(st_entries())
def test_parse_opcode(method):
    for opcode in suite.findmethod(method, eff=eff)["code"]["bytecode"]:
        op = jvm.Opcode.from_json(opcode)
        assert isinstance(op, jvm.Opcode)


@st.composite
def st_opcodes(draw):
    entry = draw(st_entries())
    opcode = draw(st.sampled_from(suite.findmethod(entry, eff=eff)["code"]["bytecode"]))
    return jvm.Opcode.from_json(opcode)


@given(st_opcodes())
def test_opcode_correct(op):
    assert isinstance(op, jvm.Opcode)


@given(st_opcodes())
def test_opcode_str(op):
    assert str(op)


@given(st_opcodes())
def test_opcode_repr(op):
    assert repr(op)


@given(st_opcodes())
def test_opcode_real(op):
    assert op.real()


@given(st_opcodes())
def test_opcode_hash(op):
    assert hash(op)
