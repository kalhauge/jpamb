from abc import ABC, abstractmethod
from dataclasses import dataclass

import jvm
import sexpr


@dataclass(frozen=True)
class PC:
    method: jvm.AbsMethodID
    offset: int

    def __iadd__(self, delta):
        return self + delta

    def __add__(self, delta):
        return PC(self.method, self.offset + delta)

    def __str__(self):
        return f"{self.method}:{self.offset}"

    def __sexpr__(self):
        return str(self)


@dataclass
class Stack[T]:
    items: list[T]

    def __bool__(self) -> bool:
        return len(self.items) > 0

    @classmethod
    def empty(cls):
        return cls([])

    def peek(self) -> T:
        return self.items[-1]

    def pop(self) -> T:
        return self.items.pop(-1)

    def push(self, value):
        self.items.append(value)
        return self


@dataclass
class OperandStack(Stack[jvm.Value]):
    def push(self, value):
        assert isinstance(value, jvm.Value)
        assert isinstance(value.type, jvm.StackType)
        return super().push(value)

    def __sexpr__(self):
        x = len(self.items)
        out = []
        for k, v in enumerate(self.items):
            out += [f":{x - k}", sexpr.sexpr(v)]
        return out


@dataclass
class Frame:
    locals: list[jvm.Value | None]
    stack: OperandStack
    pc: PC

    def __str__(self):
        locals = ", ".join(f"{k}:{v}" for k, v in enumerate(self.locals))
        return f"<{{{locals}}}, {self.stack}, {self.pc}>"

    def from_method(method: jvm.Method) -> "Frame":
        return Frame(
            [None] * method.max_locals,
            OperandStack.empty(),
            PC(method.id, 0),
        )

    def __sexpr__(self) -> sexpr.SExpr:
        return sexpr.data(
            "frame",
            locals=sexpr.sequence(sexpr.sexpr(a) for a in self.locals),
            stack=sexpr.sexpr(self.stack),
            pc=sexpr.sexpr(self.pc),
        )


@dataclass
class CallStack(Stack[Frame]):
    def push(self, value):
        assert isinstance(value, Frame)
        return super().push(value)

    def __sexpr__(self):
        x = len(self.items)
        out = []
        for k, v in enumerate(self.items):
            out += [f":{x - k}", sexpr.sexpr(v)]
        return out


@dataclass
class HeapValue(ABC):
    @abstractmethod
    def __sexpr__(self) -> sexpr.SExpr: ...


@dataclass
class HeapArray(HeapValue):
    contains: jvm.Type
    values: list[jvm.Value]

    def __sexpr__(self) -> sexpr.SExpr:
        type = [f"array:{self.contains}"]
        values = [sexpr.sexpr(v) for v in self.values] if self.values != [] else []
        return type + values


@dataclass
class HeapObject(HeapValue):
    classname: jvm.ClassName
    fields: dict[jvm.FieldID, jvm.Value]

    def __sexpr__(self) -> sexpr.SExpr:
        return [f"class:{self.classname}"] + [
            item for v in self.fields for item in v.__sexpr__()
        ]


@dataclass
class HeapString(HeapValue):
    content: str

    def __sexpr__(self) -> sexpr.SExpr:
        return f"{self.content}"


@dataclass
class State:
    heap: list[HeapValue]
    frames: CallStack

    def create(self, value: HeapValue) -> jvm.Value:
        assert isinstance(value, HeapValue)
        index = len(self.heap)
        self.heap.append(value)
        return jvm.Value.reference(index)

    def __str__(self):
        return (
            f"{''.join(f'{i:0}: {x}\n' for i, x in enumerate(self.heap))}{self.frames}"
        )

    def __sexpr__(self) -> sexpr.SExpr:
        return sexpr.data(
            "state",
            heap=sexpr.data(
                "heap",
                **{f"0x{k + 1:04x}": sexpr.sexpr(v) for k, v in enumerate(self.heap)},
            ),
            callstack=sexpr.sexpr(self.frames),
        )
