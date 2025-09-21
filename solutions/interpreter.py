import jpamb
from jpamb import jvm
from dataclasses import dataclass

import sys
from loguru import logger

logger.remove()
logger.add(sys.stderr, format="[{level}] {message}")

methodid, input = jpamb.getcase()


@dataclass
class PC:
    method: jvm.AbsMethodID
    offset: int

    def __iadd__(self, delta):
        self.offset += delta
        return self

    def __add__(self, delta):
        return PC(self.method, self.offset + delta)
    
    def replace(self, val):
        self.offset = val

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


suite = jpamb.Suite()
bc = Bytecode(suite, dict())


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
    heap_items = 0
    frames: Stack[Frame]

    # currently takes in classname as 'val' and pushes it directly into the heap - this might be the wrong datatype
    # also don't know if we should use heap or locals
    def heap_append(self, val):
        self.heap[self.heap_items] = val
        idx = self.heap_items
        self.heap_items += 1
        return idx

    def __str__(self):
        return f"{self.heap} {self.frames}"


def step(state: State) -> State | str:
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
        case jvm.Binary(type=jvm.Int(), operant=jvm.BinaryOpr.Sub):
            v2, v1 = frame.stack.pop(), frame.stack.pop()
            assert v1.type is jvm.Int(), f"expected int, but got {v1}"
            assert v2.type is jvm.Int(), f"expected int, but got {v2}"
            frame.stack.push(jvm.Value.int(v1.value - v2.value))
            frame.pc += 1
            return state
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
        case jvm.Return(type=None):
            state.frames.pop()
            if state.frames:
                frame = state.frames.peek()
                frame.stack.push(v1)
                frame.pc += 1
                return state
            else:
                return "ok"
        case jvm.Dup():
            v1 = frame.stack.peek()
            frame.stack.push(v1)
            frame.pc += 1
            return state
        case jvm.Get(field=field, static=static):
            if field.extension.name == "$assertionsDisabled":
                frame.stack.push(False)
                frame.pc += 1
                return state
            else:
                raise NotImplementedError(f"Don't know how to handle get that is not $assertionsDisabled: {field!r}")
        case jvm.Ifz(condition=condition, target=target):
            v1 = frame.stack.pop()
            match v1:
                case jvm.Value(jvm.Boolean()):
                            match condition:
                                case "ne":
                                    if v1.value:
                                        frame.pc.replace(target)
                                    else:
                                        frame.pc += 1
                                case "eq":
                                    if not v1.value:
                                        frame.pc.replace(target)
                                    else:
                                        frame.pc += 1
                                case _:
                                    raise NotImplementedError(f"Don't know how to handle condition of type: {condition!r}")
                case jvm.Value(jvm.Int()) | int():
                    value = v1.value if isinstance(v1, jvm.Value) else v1
                    match condition:
                        case "ne":
                            if value != 0:
                                frame.pc.replace(target)
                            else:
                                frame.pc += 1
                        case "eq":
                            if value == 0:
                                frame.pc.replace(target)
                            else:
                                frame.pc += 1
                        case "gt":
                            if value > 0:
                                frame.pc.replace(target)
                            else:
                                frame.pc += 1
                        case "lt":
                            if value < 0:
                                frame.pc.replace(target)
                            else:
                                frame.pc += 1
                        case "ge":
                            if value >= 0:
                                frame.pc.replace(target)
                            else:
                                frame.pc += 1
                        case "le":
                            if value <= 0:
                                frame.pc.replace(target)
                            else:
                                frame.pc += 1
                        case _:
                            raise NotImplementedError(f"Don't know how to handle condition of type: {condition!r}")
                case _:
                    raise NotImplementedError(f"Don't know how to handle Ifz for v1: {v1!r}")
            return state
        case jvm.New(classname=cname):
            # look at heap_append 
            idx = state.heap_append(cname.name)
            frame.stack.push(idx)
            frame.pc += 1
            logger.debug(cname)
            return state
        case jvm.InvokeSpecial(method=m, is_interface=is_interface):
            if len(m.extension.params._elements) == 0:
                v1 = frame.stack.pop()
                frame.pc += 1
                return state
            raise NotImplementedError("Don't know how to handle special invocations with more than 0 elements")
        case jvm.Throw():
            v1 = frame.stack.pop()
            if state.heap[v1] == "java/lang/AssertionError":
                return 'assertion error'
            else:
                raise NotImplementedError(f"Don't know how to handle non-assertion error error: {state.heap[v1]!r}")
        case jvm.If(condition=condition, target=target):
            v2, v1 = frame.stack.pop(), frame.stack.pop()
            # v1 and v2 can also be references
            assert v1.type is jvm.Int(), f"expected int, but got {v1}"
            assert v2.type is jvm.Int(), f"expected int, but got {v2}"
            match condition:
                case "gt":
                    if v1.value > v2.value:
                        frame.pc.replace(target)
                    else:
                        frame.pc += 1
                case _:
                    raise NotImplementedError(f"Don't know how to handle if-statement condition of type: {condition!r}")
            return state
        case a:
            raise NotImplementedError(f"Don't know how to handle: {a!r}")


frame = Frame.from_method(methodid)
for i, v in enumerate(input.values):
    frame.locals[i] = v

state = State({}, Stack.empty().push(frame))

for x in range(1000):
    state = step(state)
    if isinstance(state, str):
        print(state)
        break
else:
    print("*")
