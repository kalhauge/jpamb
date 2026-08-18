import jpamb
from jpamb import jvm
from dataclasses import dataclass
import logging
import sys


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
    methods: dict[jvm.AbsMethodID, list[jvm.Opcode]]

    def __getitem__(self, pc: PC) -> jvm.Opcode:
        try:
            opcodes = self.methods[pc.method]
        except KeyError:
            opcodes = list(self.suite.method_opcodes(pc.method))
            self.methods[pc.method] = opcodes

        return opcodes[pc.offset]


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
        return "".join(f"{v}" for v in self.items)


@dataclass
class Frame:
    locals: dict[int, jvm.Value]
    stack: Stack[jvm.Value]
    pc: PC

    def __str__(self):
        locals = ", ".join(f"{k}:{v}" for k, v in sorted(self.locals.items()))
        return f"<{{{locals}}}, {self.stack}, {self.pc}>"

    def from_method(method: jvm.AbsMethodID) -> "Frame":
        return Frame({}, Stack.empty(), PC(method, 0))


@dataclass
class State:
    heap: dict[int, jvm.Value]
    frames: Stack[Frame]

    def __str__(self):
        return f"{self.heap} {self.frames}"


def step(bc: Bytecode, state: State) -> State | str:
    assert isinstance(state, State), f"expected frame but got {state}"
    frame = state.frames.peek()
    opr = bc[frame.pc]
    logger.debug(f"STEP {opr}\n{state}")
    match opr:
        case jvm.Push(value=v):
            frame.stack.push(v)
            frame.pc += 1
            return state
        case jvm.Load(type=jvm.Int(), index=i):
            frame.stack.push(frame.locals[i])
            frame.pc += 1
            return state
        case jvm.Binary(type=jvm.Int(), operant=jvm.BinaryOpr.Div):
            v2, v1 = frame.stack.pop(), frame.stack.pop()
            assert v1.type is jvm.Int(), f"expected int, but got {v1}"
            assert v2.type is jvm.Int(), f"expected int, but got {v2}"
            if v2.value == 0:
                return "divide by zero"

            frame.stack.push(jvm.Value.int(v1.value // v2.value))
            frame.pc += 1
            return state

        case jvm.Return(type=None):
            state.frames.pop()
            if state.frames:
                frame = state.frames.peek()
                frame.pc += 1
                return state
            else:
                return "ok"

        case jvm.Return(type=jvm.Int()):
            v1 = frame.stack.pop()
            state.frames.pop()
            if state.frames:
                frame = state.frames.peek()
                frame.stack.push(v1)
                frame.pc += 1
                return state
            else:
                return "ok"

        case jvm.Get(static=True, field=field):
            # Hack - Only handle the assertion case
            assert field.extension.name == "$assertionsDisabled"

            # Hack - Assuming assertions are never disabled
            frame.stack.push(jvm.Value.int(0))
            frame.pc += 1

            return state

        case jvm.Ifz(condition="ne", target=target):
            value = frame.stack.pop()
            assert value.type is jvm.Int(), f"expected int, but got {value}"

            if value.value != 0:
                frame.pc.offset = target
                return state

            frame.pc += 1

            return state

        case jvm.New(classname=jvm.ClassName("java/lang/AssertionError")):
            # Hack -- if we create an assertion error, we probably also throw it.
            return "assertion error"

        case a:
            a.help()
            sys.exit(-1)


def run(suite, methodid, input, steps=10):
    bc = Bytecode(suite, dict())

    frame = Frame.from_method(methodid)
    for i, v in enumerate(input):
        # Convert arbitrary values into local values
        match v.type:
            case jvm.Boolean():
                frame.locals[i] = jvm.Value.int(1 if v.value else 0)
            case jvm.Int():
                frame.locals[i] = v
            case a:
                assert False, f"Do not know how to convert {v} to a local value"

    state = State({}, Stack.empty().push(frame))

    for x in range(steps):
        state = step(bc, state)
        if isinstance(state, str):
            return state
    else:
        return "*"


def test():
    """The entry point for the interpreter"""
    logging.basicConfig(level=logging.DEBUG, format="%(message)s")
    suite = jpamb.Suite.from_cwd()
    methodid, input = jpamb.getcase()
    output = run(suite, methodid, input.values)
    print(output)


def analyse():
    """The dynamic analysis, e.g. in this case a (dumb) fuzzer."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    methodid = jpamb.getmethodid(
        "interpreter",
        "1.0",
        "The Rice Theorem Cookers",
        ["dynamic", "python"],
        for_science=True,
    )

    suite = jpamb.Suite.from_cwd()

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

        output = run(suite, methodid, input)

        logger.info(f"Got {output}")
        behaviors.add(output)

    for behavior in behaviors:
        print(f"{behavior};100%")
