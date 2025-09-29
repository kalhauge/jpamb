import jpamb
from jpamb import jvm
from dataclasses import dataclass
import numpy

import sys
from loguru import logger

logger.remove()
logger.add(sys.stderr, format="[{level}] {message}")


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
    heap_items: int
    frames: Stack[Frame]

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
        case jvm.Load(type=type, index=i):
            local = frame.locals[i]
            assert local.type == type, f"Expected type {type}, got {local.type}"
            frame.stack.push(local)
            frame.pc += 1
            return state
        case jvm.ArrayLoad(type=type):
            idx, ref = frame.stack.pop(), frame.stack.pop()
            arr = state.heap[ref.value]

            if arr == None:
                return "null pointer"

            assert arr.type.contains == type, f"Expected type {type}, got {local.type}"

            if len(arr.value) <= idx.value:
                return "out of bounds"

            frame.stack.push(jvm.Value.int(arr.value[idx.value]))
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
        case jvm.Binary(type=jvm.Int(), operant=jvm.BinaryOpr.Rem):
            v2, v1 = frame.stack.pop(), frame.stack.pop()
            assert v1.type is jvm.Int(), f"expected int, but got {v1}"
            assert v2.type is jvm.Int(), f"expected int, but got {v2}"
            frame.stack.push(jvm.Value.int(v1.value % v2.value))
            frame.pc += 1
            return state
        case jvm.Binary(type=jvm.Int(), operant=jvm.BinaryOpr.Mul):
            v2, v1 = frame.stack.pop(), frame.stack.pop()
            assert v1.type is jvm.Int(), f"expected int, but got {v1}"
            assert v2.type is jvm.Int(), f"expected int, but got {v2}"
            frame.stack.push(jvm.Value.int(v1.value * v2.value))
            frame.pc += 1
            return state
        case jvm.Binary(type=jvm.Int(), operant=jvm.BinaryOpr.Add):
            v2, v1 = frame.stack.pop(), frame.stack.pop()
            assert v1.type is jvm.Int(), f"expected int, but got {v1}"
            assert v2.type is jvm.Int(), f"expected int, but got {v2}"
            frame.stack.push(jvm.Value.int(v1.value + v2.value))
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
            v1 = state.frames.pop()
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
                frame.stack.push(jvm.Value.int(0))
                frame.pc += 1
                return state
            else:
                raise NotImplementedError(f"Don't know how to handle get that is not $assertionsDisabled: {field!r}")
        case jvm.Ifz(condition=condition, target=target) | jvm.If(condition=condition, target=target):
            v2 = 0 if isinstance(opr, jvm.Ifz) else frame.stack.pop().value
            v1 = frame.stack.pop()
            match condition:
                case "ne":
                    if v1.value != v2:
                        frame.pc.replace(target)
                    else:
                        frame.pc += 1
                case "eq":
                    if v1.value == v2:
                        frame.pc.replace(target)
                    else:
                        frame.pc += 1
                case "gt":
                    if v1.value > v2:
                        frame.pc.replace(target)
                    else:
                        frame.pc += 1
                case "lt":
                    if v1.value < v2:
                        frame.pc.replace(target)
                    else:
                        frame.pc += 1
                case "ge":
                    if v1.value >= v2:
                        frame.pc.replace(target)
                    else:
                        frame.pc += 1
                case "le":
                    if v1.value <= v2:
                        frame.pc.replace(target)
                    else:
                        frame.pc += 1
                case _:
                    raise NotImplementedError(f"Don't know how to handle condition of type: {condition!r}")
            return state
        case jvm.New(classname=cname):
            # look at heap_append 
            idx = state.heap_append(cname.name)
            frame.stack.push(jvm.Value.reference(idx))
            frame.pc += 1
            return state
        case jvm.InvokeSpecial(method=m, is_interface=is_interface):
            if len(m.extension.params._elements) == 0:
                v1 = frame.stack.pop()
                frame.pc += 1
                return state
            raise NotImplementedError("Don't know how to handle special invocations with more than 0 elements")
        case jvm.Throw():
            v1 = frame.stack.pop()
            if state.heap[v1.value] == "java/lang/AssertionError":
                return 'assertion error'
            else:
                raise NotImplementedError(f"Don't know how to handle non-assertion error error: {state.heap[v1]!r}")
        case jvm.Store(type=type, index=idx):
            v = frame.stack.pop()
            assert v.type == type, f"Expected type {type}, got {v.type}"
            frame.locals[idx] = v
            frame.pc += 1
            return state
        case jvm.ArrayStore(type=jvm.Int()):
            v, idx, ref = frame.stack.pop(), frame.stack.pop(), frame.stack.pop()
            assert ref.type == jvm.Reference(), f"Expected reference, got {ref.type}"
            assert idx.type == jvm.Int(), f"Expected integer, got {idx.type}"

            if ref.value == None:
                return "null pointer"

            arr = state.heap[ref.value]
            assert v.type == arr.type.contains, f"Expected {arr.type}, got {v.type}"
            if len(arr.value) <= idx.value:
                return "out of bounds"

            # Array content is stored as tuple (immutable) and array.value is frozen (immutable)
            # so we need to overwrite the whole content in the heap
            new_content = list(arr.value)
            new_content[idx.value] = v.value
            state.heap[ref.value] = jvm.Value.array(v.type, new_content)

            frame.pc += 1
            return state
        case jvm.Goto(target=target):
            frame.pc.replace(target)
            return state
        case jvm.Cast(from_=from_, to_=to_):
            v = frame.stack.pop()
            assert v.type == from_, f"Expected type {from_}, got {v.type}"
            match to_:
                case jvm.Short():
                        frame.stack.push(jvm.Value.int(numpy.short(v.value))) 
                case _:
                    raise NotImplementedError(f"Don't know how to cast to: {to_}")
            frame.pc += 1
            return state
        case jvm.NewArray(type=type, dim=dim):
            v = frame.stack.pop()
            assert v.type == jvm.Int(), f"Expected operand to be of type int, got {v.type}"
            match type:
                case jvm.Int():
                    heap_pos = state.heap_append(jvm.Value.array(type, [0 for _ in range(v.value)]))
                    frame.stack.push(jvm.Value.reference(heap_pos))
                case t:
                    raise NotImplementedError(f"Don't know how to handle arrays of type {t}")
            frame.pc += 1
            return state
        case jvm.ArrayLength():
            ref = frame.stack.pop()

            assert ref.type == jvm.Reference(), f"Expected reference got {ref.type}"
            
            if ref.value == None:
                return "null pointer"

            frame.stack.push(jvm.Value.int(len(state.heap[ref.value].value)))

            frame.pc += 1
            return state
        case a:
            raise NotImplementedError(f"Don't know how to handle: {a!r}")

def execute(methodid, input):
    frame = Frame.from_method(methodid)
    heap = {}
    heap_items = 0
    for i, v in enumerate(input.values):
        match v:
            case jvm.Value(type=jvm.Boolean(), value=value):
                v = jvm.Value.int(1 if value else 0)
            case jvm.Value(type=jvm.Int(), value=value) | jvm.Value(jvm.Float(), value=value) | jvm.Value(jvm.Double(), value=value):
                pass
            case jvm.Value(type=jvm.Array(), value=value):
                heap[heap_items] = jvm.Value.array(v.type.contains, value)
                idx = heap_items
                heap_items += 1
                v = jvm.Value.reference(idx)
            case _:
                raise NotImplementedError(f"Don't know how to handle {v}")
        frame.locals[i] = v

    state = State(heap, heap_items, Stack.empty().push(frame))

    for x in range(1000):
        state = step(state)
        logger.debug("------------" + str(state))
        if isinstance(state, str):
            return state
    else:
        return "*"

if __name__ == "__main__":
    methodid, input = jpamb.getcase()
    state = execute(methodid, input)
    print(state)
    