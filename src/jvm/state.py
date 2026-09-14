from abc import ABC
from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Self

import jvm
import sexpr


@dataclass(frozen=True, slots=True)
class PC:
    """The program counter.

    Contains a method and an offset into that methods bytecode.
    """

    method: jvm.AbsMethodID
    offset: int

    def __add__(self, delta):
        return PC(self.method, self.offset + delta)

    def __mod__(self, new_offset):
        """pc % t == PC(pc.method, t)"""
        return PC(self.method, new_offset)

    def __str__(self):
        return self.encode()

    def encode(self) -> str:
        return f"{self.method.encode()}:{self.offset}"

    @classmethod
    def decode(cls, code: str) -> str:
        method, offset = code.rsplit(":", 1)
        return cls(jvm.AbsMethodID.decode(method), int(offset))

    def __sexpr__(self):
        return self.encode()

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> Self:
        return cls.decode(sexpr.to_str(expr))


class StackValue(ABC):
    def __sexpr__(self) -> sexpr.SExpr:
        return sexpr.from_dataclass_values(self)

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> Self:
        if cls is StackValue:
            return sexpr.to_union(
                expr, targets=[StackInt, StackFloat, StackReference]
            )

        return sexpr.to_dataclass(expr, target=cls)


@dataclass(frozen=True, slots=True)
class StackInt(StackValue):
    __sexprtag__ = "int"

    value: int

    def __post_init__(self):
        assert isinstance(self.value, int), f"expected int but got {self.value!r}"


@dataclass(frozen=True, slots=True)
class StackFloat(StackValue):
    __sexprtag__ = "float"

    value: float

    def __post_init__(self):
        assert isinstance(self.value, float), f"expected float but got {self.value!r}"


@dataclass(frozen=True, slots=True)
class StackReference(StackValue):
    __sexprtag__ = "ref"

    value: int

    def __post_init__(self):
        assert isinstance(self.value, int), f"expected int but got {self.value!r}"


@dataclass(frozen=True)
class OperandStack:
    operands: deque[StackValue] = field(default_factory=deque)

    @classmethod
    def from_values(cls, values: Iterable[StackValue]):
        self = cls()
        for value in values:
            self.push(value)
        return self

    def pop(self) -> StackValue:
        return self.operands.pop()

    def __bool__(self) -> bool:
        return bool(self.operands)

    def push(self, value) -> Self:
        assert isinstance(value, StackValue), f"expected value but got {value!r}"

        self.operands.append(value)
        return self

    def __sexpr__(self) -> sexpr.SExpr:
        return sexpr.items(enumerate(self.operands), keyfmt="{:02}".format)

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> Self:
        items = []
        for option in sexpr.to_options(expr):
            items.append(StackValue.from_sexpr(option.value))

        return cls(deque(items))


@dataclass
class Locals:
    locals: list[StackValue | None]

    def __sexpr__(self) -> sexpr.SExpr:
        return sexpr.items(enumerate(self.locals), keyfmt="{:02}".format)

    def __getitem__(self, key: int) -> StackValue:
        value = self.locals[key]
        if value is None:
            raise IndexError(key)
        return self.locals[key]

    def __setitem__(self, key: int, value: StackValue):
        assert isinstance(value, StackValue)
        self.locals[key] = value

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> Self:
        items = []
        for option in sexpr.to_options(expr):
            if option.value == "-":
                items.append(None)
            else:
                items.append(StackValue.from_sexpr(option.value))

        return cls(list(items))


@dataclass
class Frame:
    locals: Locals
    stack: OperandStack
    pc: PC

    def __post_init__(self):
        assert isinstance(self.locals, Locals)

    def __str__(self):
        return sexpr.pretty(sexpr.sexpr(self), indent=2)

    def from_method(method: jvm.Method) -> "Frame":
        return Frame(
            Locals([None] * method.max_locals),
            OperandStack.from_values([]),
            PC(method.id, 0),
        )

    def __sexpr__(self) -> sexpr.SExpr:
        return sexpr.from_dataclass(self)

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> Self:
        return sexpr.to_dataclass(expr, target=cls)


@dataclass
class CallStack:
    frames: deque[Frame] = field(default_factory=deque)

    @classmethod
    def from_frames(cls, values: Iterable[Frame]):
        self = cls()
        for value in values:
            self.push(value)
        return self

    def pop(self) -> Frame:
        return self.frames.pop()

    def peek(self) -> Frame:
        return self.frames[-1]

    def __bool__(self) -> bool:
        return bool(self.frames)

    def push(self, value) -> Self:
        assert isinstance(value, Frame), f"expected Frame, but got {value!r}"
        self.frames.append(value)
        return self

    def __sexpr__(self) -> sexpr.SExpr:
        return sexpr.items(enumerate(self.frames), keyfmt="{:02}".format)

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> Self:
        items = []
        for option in sexpr.to_options(expr):
            items.append(Frame.from_sexpr(option.value))

        return cls(deque(items))


class HeapValue(ABC):
    def __sexpr__(self) -> sexpr.SExpr:
        return sexpr.from_dataclass(self)

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> Self:
        if cls is HeapValue:
            return sexpr.to_union(
                expr, targets=[StackInt, StackFloat, StackReference]
            )

        return sexpr.to_dataclass(expr, target=cls)


@dataclass
class HeapArray(HeapValue):
    __sexprtag__ = "array"
    contains: jvm.Type
    values: list[int]


@dataclass
class HeapObject(HeapValue):
    __sexprtag__ = "object"
    classname: jvm.ClassName
    fields: dict[jvm.FieldID, StackValue]


@dataclass
class HeapString(HeapValue):
    __sexprtag__ = "string"
    content: str

    def __sexpr__(self) -> sexpr.SExpr:
        return f"{self.content}"

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> Self:
        return cls(sexpr.to_str(expr))


@dataclass
class Heap:
    memory: list[HeapValue] = field(default_factory=list)

    def new(self, value: HeapValue) -> StackValue:
        assert isinstance(value, HeapValue)
        index = len(self.memory)
        self.memory.append(value)
        return StackReference(index + 1)

    def __getitem__(self, key: StackReference) -> HeapValue:
        assert isinstance(key, StackReference), f"expected reference but got {key!r}"
        if key.value == 0:
            raise IndexError("Null pointer dereference")
        return self.memory[key.value - 1]

    def __sexpr__(self) -> sexpr.SExpr:
        return sexpr.items(enumerate(self.memory), keyfmt="0x{:04x}".format)

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> Self:
        items = []
        for option in sexpr.to_options(expr):
            items.append(HeapValue.from_sexpr(option.value))

        return cls(items)


@dataclass
class State:
    heap: Heap
    frames: CallStack

    def __post_init__(self):
        assert isinstance(self.heap, Heap)
        assert isinstance(self.frames, CallStack)

    def __str__(self):
        return f"{''.join(f'{i + 1:0}: {x}\n' for i, x in enumerate(self.heap.memory))}{self.frames}"

    def __sexpr__(self) -> sexpr.SExpr:
        return sexpr.from_dataclass(self)

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> Self:
        return sexpr.to_dataclass(expr, target=cls)
