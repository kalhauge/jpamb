from hypothesis import given, note
from hypothesis import strategies as st

from dataclasses import dataclass

import jvm
import jpamb
import jpamb.case


@dataclass
class Draw:
    code: bytes
    offset: int = 0

    def next_32bit_signed_int(self) -> int:
        v = int.from_bytes(self.code[self.offset : self.offset + 4])
        self.offset += 4
        return v


def fuzz_type(draw: Draw, target: jvm.Type) -> jpamb.case.Value:
    match target:
        case jvm.Int():
            v = draw.next_32bit_signed_int()
            return jpamb.case.Int(v)
        case _:
            raise NotImplementedError(f"{target!r}")


def st_types():
    return st.sampled_from([jvm.Int(), jvm.Boolean()])


@given(st.binary(), st_types())
def test_fuzz_type(code: bytes, target: jvm.Type):
    draw = Draw(code)

    v = fuzz_type(draw, target)

    assert isinstance(v, jpamb.case.Value)
