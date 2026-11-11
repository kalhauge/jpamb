from hypothesis import given
from hypothesis import strategies as st

import jpamb
import jvm


def test_long_opcodes():
    cases = [
        (
            {
                "opr": "push",
                "offset": 0,
                "value": {"type": "long", "value": 100},
            },
            "ldc2_w [100]",
        ),
        (
            {"opr": "binary", "offset": 1, "type": "long", "operant": "div"},
            "ldiv",
        ),
        (
            {"opr": "binary", "offset": 2, "type": "long", "operant": "rem"},
            "lrem",
        ),
        ({"opr": "cast", "offset": 3, "from": "int", "to": "long"}, "i2l"),
        ({"opr": "cast", "offset": 4, "from": "long", "to": "int"}, "l2i"),
        ({"opr": "load", "offset": 5, "type": "long", "index": 1}, "lload_1"),
        ({"opr": "store", "offset": 6, "type": "long", "index": 1}, "lstore_1"),
    ]

    for data, expected in cases:
        assert jvm.Opcode.from_json(data).real() == expected


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
