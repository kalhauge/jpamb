from jpamb import jvm, model

from hypothesis import given, strategies as st

suite = model.Suite()


def st_casemethods():
    methods = [m[0] for m in model.Suite().case_methods()]
    return st.sampled_from(methods)


@given(st_casemethods())
def test_findmethod(method):
    assert isinstance(suite.findmethod(method), dict)


def st_caseopcodes():
    opcodes = sorted(set(suite.case_opcodes()), key=str)
    return st.sampled_from(opcodes)


@given(st_casemethods())
def test_parse_opcode(method):
    for opcode in suite.findmethod(method)["code"]["bytecode"]:
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
