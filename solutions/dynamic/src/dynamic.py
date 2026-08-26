import jpamb
import jpamb_utils
import copy
from abc import abstractmethod
from dataclasses import dataclass, field
import logging
import sys
import jvm
from sexpr import SExpr, pretty_print

logger = logging.getLogger(__name__)


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


@dataclass
class Bytecode:
    suite: jpamb.Suite
    eff: jpamb_utils.Effect
    methods: dict[jvm.AbsMethodID, jvm.Method] = field(default_factory=dict)

    def getmethod(self, methodid: jvm.AbsMethodID) -> jvm.Method:
        try:
            method = self.methods[methodid]
        except KeyError:
            opcodes = list(self.suite.method_opcodes(methodid, eff=self.eff))
            max_locals = self.suite.method_max_locals(methodid, eff=self.eff)
            method = jvm.Method(methodid, opcodes, max_locals)
            self.methods[methodid] = method
        return method

    def __getitem__(self, pc: PC) -> jvm.Opcode:
        return self.getmethod(pc.method).opcodes[pc.offset]

    def __contains__(self, pc: PC) -> bool:
        return pc.offset < len(self.getmethod(pc.method).opcodes)

    def __sexpr__(self, pc) -> SExpr:
        opcode = self.getmethod(pc.method).opcodes[pc.offset]
        return opcode.__sexpr__()


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

    def __sexpr__(self) -> SExpr:
        slocals = (
            ["(", "LOCALS"]
            + [ls.__sexpr__() for ls in self.locals if ls is not None]
            + [")"]
            if self.locals != []
            else []
        )
        sstack = (
            ["(", "STACK"] + [s.__sexpr__() for s in self.stack.items] + [")"]
            if self.stack.items != []
            else []
        )
        return slocals + sstack  # f"<{{{slocals}}}, {self.stack}, {self.pc}>"


@dataclass
class HeapValue:
    @abstractmethod
    def __sexpr__(self) -> SExpr: ...

    pass


@dataclass
class HeapArray(HeapValue):
    contains: jvm.Type
    values: list[jvm.Value]

    def __sexpr__(self) -> SExpr:
        type = [f"Array:{self.contains.__sexpr__()}"]
        values = [v for v in self.values] if self.values != [] else []
        return type + values


@dataclass
class HeapObject(HeapValue):
    classname: jvm.ClassName
    fields: dict[jvm.FieldID, jvm.Value]

    def __sexpr__(self) -> SExpr:
        return (
            ["(", f"Class:{self.classname}"]
            + [item for v in self.fields for item in v.__sexpr__()]
            + [")"]
        )


@dataclass
class HeapString(HeapValue):
    content: str

    def sexpr(self) -> SExpr:
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
        return f"{''.join(f'{i:04x}: {x}\n' for i, x in enumerate(self.heap))}{self.frames}"

    def __sexpr__(self) -> SExpr:
        sexpr_heap = (
            ["("] + [item for h in self.heap for item in h.__sexpr__()] + [")"]
            if self.heap != []
            else []
        )
        sexpr_stack = (
            ["(", "FRAME"]
            + [item for f in self.frames.items for item in f.__sexpr__()]
            + [")"]
        )
        return ["("] + sexpr_heap + sexpr_stack + [")"]


def binary(op, v1: jvm.Value, v2: jvm.Value) -> jvm.Value | str:
    assert isinstance(v1, jvm.Value)
    assert isinstance(v2, jvm.Value)
    match op:
        case jvm.BinaryOpr.Sub:
            return jvm.Value.int(v1.value - v2.value)
        case jvm.BinaryOpr.Add:
            return jvm.Value.int(v1.value + v2.value)
        case jvm.BinaryOpr.Mul:
            return jvm.Value.int(v1.value * v2.value)
        case jvm.BinaryOpr.Rem:
            return jvm.Value.int(v1.value % v2.value)
        case jvm.BinaryOpr.Div:
            try:
                return jvm.Value.int(v1.value // v2.value)
            except ZeroDivisionError:
                return "divide by zero"
        case a:
            raise NotImplementedError(f"Unhandled binary {op!r}")


def compare(op, v1: jvm.Value, v2: jvm.Value) -> bool:
    assert isinstance(v1, jvm.Value)
    assert isinstance(v2, jvm.Value)
    match op:
        case jvm.CmpOpr.Ne:
            return v1 != v2
        case jvm.CmpOpr.Lt:
            return v1 < v2
        case jvm.CmpOpr.Le:
            return v1 <= v2
        case jvm.CmpOpr.Gt:
            return v1 > v2
        case jvm.CmpOpr.Ge:
            return v1 >= v2
        case jvm.CmpOpr.Eq:
            return v1 == v2
        case _:
            raise NotImplementedError(f"Unhandled comparation {op!r}")


def step(bc: Bytecode, state: State) -> State | str:
    assert isinstance(state, State), f"expected state but got {state}"
    frame = state.frames.peek()
    opr = bc[frame.pc]
    output = state
    logger.debug(f"STEP {opr}\n{state}")
    match opr:
        case jvm.Push(value=v):
            if v.type == jvm.Object(jvm.ClassName("java/lang/String")):
                ref = state.create(HeapString(v.value))
                frame.stack.push(ref)
            else:
                assert isinstance(v.type, jvm.StackType), f"{v!r}"
                frame.stack.push(v)
            frame.pc += 1

        case jvm.Load(type=t, index=i):
            frame.stack.push(frame.locals[i])
            frame.pc += 1

        case jvm.Store(type=t, index=i):
            frame.locals[i] = frame.stack.pop()
            frame.pc += 1

        case jvm.Incr(index=i, amount=amount):
            frame.locals[i] = jvm.Value.int(frame.locals[i].value + amount)
            frame.pc += 1

        case jvm.Binary(type=jvm.Int(), operant=op):
            v2, v1 = frame.stack.pop(), frame.stack.pop()
            assert v1.type is jvm.Int(), f"expected int, but got {v1}"
            assert v2.type is jvm.Int(), f"expected int, but got {v2}"

            value = binary(op, v1, v2)

            if isinstance(value, jvm.Value):
                frame.stack.push(value)
                frame.pc += 1
            else:
                output = value

        case jvm.Return(type=t):
            if t is not None:
                v1 = frame.stack.pop()
            state.frames.pop()
            if state.frames:
                frame = state.frames.peek()
                if t is not None:
                    frame.stack.push(v1)
                frame.pc += 1
            else:
                output = "ok"

        case jvm.Get(static=True, field=field):
            # Hack - Only handle the assertion case
            assert field.extension.name == "$assertionsDisabled"

            # Hack - Assuming assertions are never disabled
            frame.stack.push(jvm.Value.int(0))
            frame.pc += 1

        case jvm.Cast(to_=to_, from_=from_):
            # Hack - Do nothing
            assert from_ == jvm.Int()
            assert to_ == jvm.Short()
            frame.pc += 1

        case jvm.InvokeStatic(method=methodid):
            newframe = Frame.from_method(bc.getmethod(methodid))
            params = list(enumerate(methodid.extension.params))
            state.frames.push(newframe)
            for i, p in reversed(params):
                newframe.locals[i] = frame.stack.pop()

        case jvm.InvokeVirtual(method=methodid):
            match methodid.extension.name:
                case "equals":
                    v2, v1 = frame.stack.pop(), frame.stack.pop()

                    x = 1 if state.heap[v2.value] == state.heap[v1.value] else 0
                    frame.stack.push(jvm.Value.int(x))
                    frame.pc += 1
                case x:
                    raise NotImplementedError(f"Can't handle virtual method {methodid}")

        case jvm.Goto(target=target):
            frame.pc.offset = target

        case jvm.Ifz(condition=op, target=target):
            value = frame.stack.pop()
            assert value.type is jvm.Int(), f"expected int, but got {value}"

            if compare(op, value, jvm.Value.int(0)):
                frame.pc.offset = target
            else:
                frame.pc += 1

        case jvm.If(condition=op, target=target):
            v2, v1 = frame.stack.pop(), frame.stack.pop()
            assert v1.type is jvm.Int(), f"expected int, but got {v1}"
            assert v2.type is jvm.Int(), f"expected int, but got {v2}"

            if compare(op, v1, v2):
                frame.pc.offset = target
            else:
                frame.pc += 1

        case jvm.New(classname=jvm.ClassName("java/lang/AssertionError")):
            # Hack -- if we create an assertion error, we probably also throw it.
            output = "assertion error"

        case jvm.Dup(words=1):
            v = frame.stack.pop()
            frame.stack.push(v)
            frame.stack.push(v)
            frame.pc += 1

        case jvm.NewArray(type=type, dim=1):
            assert type == jvm.Int()
            v = frame.stack.pop()

            ref = state.create(HeapArray(type, [0] * v.value))
            frame.stack.push(ref)
            frame.pc += 1

        case jvm.ArrayStore(type=type):
            assert type == jvm.Int()
            val, idx, ref = frame.stack.pop(), frame.stack.pop(), frame.stack.pop()

            assert isinstance(ref.type, jvm.Reference)

            if ref.value == None:
                output = "null pointer"
            else:
                arr = state.heap[ref.value]
                try:
                    arr.values[idx.value] = val.value
                    frame.pc += 1
                except IndexError:
                    output = "out of bounds"

        case jvm.ArrayLoad(type=type):
            idx, ref = frame.stack.pop(), frame.stack.pop()

            assert isinstance(ref.type, jvm.Reference)

            if ref.value == None:
                output = "null pointer"
            else:
                arr = state.heap[ref.value]
                try:
                    assert not isinstance(type, jvm.Reference)
                    frame.stack.push(jvm.Value.int(arr.values[idx.value]))
                    frame.pc += 1
                except IndexError:
                    output = "out of bounds"

        case jvm.ArrayLength():
            ref = frame.stack.pop()
            assert isinstance(ref.type, jvm.Reference)
            if ref.value == None:
                output = "null pointer"
            else:
                arr = state.heap[ref.value]
                frame.stack.push(jvm.Value.int(len(arr.values)))
                frame.pc += 1

        case a:
            a.help()
            sys.exit(-1)

    assert isinstance(output, State) or isinstance(output, str)

    return output


def run(bc, methodid, input, MAX_STEPS=1000):
    frame = Frame.from_method(bc.getmethod(methodid))
    state = State([], Stack.empty().push(frame))
    for i, v in enumerate(input):
        # Convert arbitrary values into local values
        match v.type:
            case jvm.Boolean():
                frame.locals[i] = jvm.Value.int(1 if v.value else 0)
            case jvm.Int():
                frame.locals[i] = v
            case jvm.Array(contains=type):
                match type:
                    case jvm.Char():
                        ref = state.create(HeapArray(type, [ord(a) for a in v.value]))
                    case jvm.Int():
                        ref = state.create(HeapArray(type, [a for a in v.value]))
                frame.locals[i] = ref
            case jvm.Object(name=jvm.ClassName("java/lang/String")):
                ref = state.create(HeapString(v.value))
                frame.locals[i] = ref
            case a:
                raise NotImplementedError(
                    f"Do not know how to convert values of type {a!r} to a local value"
                )

    for x in range(MAX_STEPS):
        frame = state.frames.peek()
        opr = bc[frame.pc].__sexpr__()
        sexpr_out = (
            f"( STEP {' '.join([str(s) for s in state.__sexpr__()])} {' '.join(opr)}"
        )

        state = step(bc, state)
        if isinstance(state, State):
            try:
                sexpr = (
                    sexpr_out + f" {' '.join([str(s) for s in state.__sexpr__()])} )"
                )
                print(sexpr)
            except ValueError:
                print("Failed to sexpr")

        if isinstance(state, str):
            return state

    else:
        return "*"


def interpret():
    """The entry point for the interpreter"""
    logging.basicConfig(level=logging.DEBUG, format="%(message)s")

    suite, eff = jpamb.setup()
    bc = Bytecode(suite, eff, dict())

    methodid, input = jpamb.getcase()
    output = run(suite, methodid, input.values)
    if not isinstance(output, str):
        print(output.__sexpr__())
    else:
        print(output)


def analyse():
    """The dynamic analysis, e.g. in this case a (dumb) fuzzer."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    methodid = jpamb.getmethodid(
        "dynamic",
        "1.0",
        "The Rice Theorem Cookers",
        ["dynamic", "python"],
        for_science=True,
    )

    suite, eff = jpamb.setup()
    bc = Bytecode(suite, eff, dict())

    import random

    # Make the randomness deterministic
    random.seed(0)

    behaviors = set()
    # Try 10 random inputs
    for i in range(10):
        input = []
        # 1. come up with possible inputs
        for p in methodid.extension.params:
            match p:
                case jvm.Int():
                    input.append(jvm.Value.int(random.randint(-(1 << 31), 1 << 31)))
                case jvm.Boolean():
                    input.append(jvm.Value.boolean(1 == random.randint(0, 1)))
                case a:
                    assert False, f"Do not know how generate random values for {a}"

        logger.info(f"Testing {input}")

        output = run(bc, methodid, input)

        logger.info(f"Got {output}")
        behaviors.add(output)

    for query in jpamb.QUERIES:
        if query in behaviors:
            if query == "*":
                print(f"{query};timeout")
            else:
                print(f"{query};found")
        else:
            print(f"{query};not-found")
