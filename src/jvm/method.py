import jvm.base
import jvm.opcode

from dataclasses import dataclass


@dataclass(frozen=True)
class Method:
    """A java method, (still) partial"""

    id: jvm.base.AbsMethodID
    opcodes: list[jvm.opcode.Opcode]
    max_locals: int

    @classmethod
    def from_json(cls, id: jvm.base.AbsMethodID, json) -> "Method":
        opcodes = [jvm.opcode.Opcode.from_json(op) for op in json["code"]["bytecode"]]
        max_locals = json["code"]["max_locals"]

        return Method(
            id=id,
            opcodes=opcodes,
            max_locals=max_locals,
        )
