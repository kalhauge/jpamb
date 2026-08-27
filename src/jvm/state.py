from abc import abstractmethod, ABC
from dataclasses import dataclass, field
import jvm
import sexpr
import sys


@dataclass
class PC:
    method: jvm.AbsMethodID
    offset: int

    def __iadd__(self, delta):
        self.offset += delta
        return self

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

    def __str__(self):
        if not self:
            return "ϵ"
        return "\n".join(f"{v}" for v in self.items)

    def __sexpr__(self):
        x = len(self.items)
        return sum(
            ([f":{x - k}", sexpr.sexpr(v)] for k, v in enumerate(self.items)), start=[]
        )


@dataclass
class OperantStack(Stack[jvm.Value]):
    def push(self, value):
        assert isinstance(value, jvm.Value)
        assert isinstance(value.type, jvm.StackType)

        return super().push(value)

    def __str__(self):
        if not self:
            return "ϵ"
        return "".join(f"{v}" for v in self.items)


@dataclass
class Frame:
    locals: list[jvm.Value]
    stack: OperantStack
    pc: PC

    def __str__(self):
        locals = ", ".join(f"{k}:{v}" for k, v in enumerate(self.locals))
        return f"<{{{locals}}}, {self.stack}, {self.pc}>"

    def from_method(method: jvm.Method) -> "Frame":
        return Frame(
            [None] * method.max_locals,
            OperantStack.empty(),
            PC(method.id, 0),
        )

    def __sexpr__(self) -> sexpr.SExpr:
        return sexpr.data(
            "frame",
            locals=sexpr.sequence((sexpr.sexpr(a) for a in self.locals)),
            stack=sexpr.sexpr(self.stack),
            pc=sexpr.sexpr(self.pc),
        )


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
        values = [v for v in self.values] if self.values != [] else []
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
    frames: Stack[Frame]

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

    @classmethod
    def from_sexpr(cls, expr, context=list[str]) -> "State":
        # if not isinstance(expr, list):
        #     raise ParseError("...", context)

        (key, args, kwargs) = sexpr.undata(expr)

        if not key == "state":
            raise RuntimeError("...")

        if not args == []:
            raise RuntimeError("...")

        # heap = sexpr.getkey("heap", kwargs, context, handler=Heap.from_sexpr)
        # callstack = sexpr.getkey("callstack", kwargs, context, handler=Stack.from_sexpr)

        # return cls(heap=heap, callstack=callstack)

    def display(self):
        print("", file=sys.stderr)
        print(f"Heap : {self.heap}", file=sys.stderr)
        print(f"Depth: {len(self.frames.items)}", file=sys.stderr)
        print(f"Top: {self.frames.items[-1].locals}", file=sys.stderr)
        print(f"Top: {self.frames.items[-1].stack}", file=sys.stderr)
