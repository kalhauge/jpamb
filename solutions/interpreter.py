import jpamb
from jpamb import jvm
from dataclasses import dataclass, field

import sys
from loguru import logger

from jpamb.jvm.base import Value

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
    frames: Stack[Frame]

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
        
        case jvm.Binary(type=jvm.Int(), operant=jvm.BinaryOpr.Div): # Binary Division
            v2, v1 = frame.stack.pop(), frame.stack.pop()
            # assert v2.value > 0, "Helooooo we need to do something here!!!"
            assert v1.type is jvm.Int(), f"expected int, but got {v1}"
            assert v2.type is jvm.Int(), f"expected int, but got {v2}"
            if v2.value == 0:
                return "divide by zero"

            frame.stack.push(jvm.Value.int(v1.value // v2.value))
            frame.pc += 1
            return state
        
        case jvm.Binary(type=jvm.Int(), operant=jvm.BinaryOpr.Sub): # Binary subtraction
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
                frame.pc += 1
                return state
            else:
                return "ok"
            
        case jvm.Get(static=val):
            if frame.locals and (0 in frame.locals or 1 in frame.locals):
                if frame.locals[0] == Value.int(0) or frame.locals[0] == Value.int(1):
                    frame.pc += 1
                    return state
                else:
                    return "assertion error"
            else:
                return "assertion error"
            # assert val is True, f"expected boolean, but got {val}"
            # assert val >= 0
            # logger.debug(f"Get static field value: {val}")
            if val is True:
                frame.stack.push(1)
            else: 
                frame.stack.push(0)
            frame.pc += 1
            return state
            
            # return f"{val}"
            
        case jvm.Ifz(condition=cond, target=val):
            
            v = frame.locals[0]
            if cond == 'eq': 
                if v == Value.int(0):
                    #logger.debug(f"Jumping to {val}")
                    frame.pc = PC(frame.pc.method, val)
                else:
                    #logger.debug(f"Not jumping")
                    frame.pc += 1
            if cond == 'ne':
                # logger.debug(f"Stack items: , {frame.stack.items}")
                # logger.debug(f"comparing v: {v} to 0")
                if v != Value.int(0):
                    #logger.debug(f"Jumping to {val}")
                    frame.pc = PC(frame.pc.method, val)
                else:
                    #logger.debug(f"Not jumping")
                    frame.pc += 1
            return state         
        
        case jvm.New(classname=name):
            obj_ref = len(state.heap)
            state.heap[obj_ref] = {"class": name}
            frame.stack.push(obj_ref)
            frame.pc += 1
            return state
        
        case jvm.Dup():
            v = frame.stack.peek()
            frame.stack.push(Value.int(v))
            frame.pc += 1
            return state
        
        case jvm.InvokeSpecial(method=mid):
            method_name = mid.extension.name
            if method_name == "<init>":
                # Simulate object creation (same as jvm.New)
                obj_ref = len(state.heap)
                state.heap[obj_ref] = {"class": mid.classname._as_string}
                frame.stack.push(obj_ref)
                frame.pc += 1
                return state
            else:
                # Handle other special methods
                frame.pc += 1
                return state
            
        case jvm.Throw():            
            # return f"Stack items: , {frame.stack.items}"
            assertionsDisabled = frame.locals[0]
            # logger.debug(f"Stack items: , {frame.stack.items}")
            # logger.debug(f"assertionsDisabled: {assertionsDisabled}")
            if assertionsDisabled == Value.int(0):

                return "assertion error"
            else:
                frame.pc += 1
                return state
            
            # classname = "java/lang/RuntimeException"
            # obj_ref = len(state.heap)
            # state.heap[obj_ref] = {"class": classname}
            # frame.stack.items.clear()
            # frame.stack.push(obj_ref)
            # frame.pc += 1
            # return state
            
        case jvm.If(condition=cond, target=val):
            if cond == 'gt':
                v2, v1 = frame.stack.pop(), frame.stack.pop()
                if v1.value > v2.value:
                    # logger.debug(f"Jumping to {val}")
                    frame.pc = PC(frame.pc.method, val)
                else:
                    # logger.debug(f"Not jumping")
                    frame.pc += 1
            return state

        case a:
            raise NotImplementedError(f"Don't know how to handle: {a!r}")


frame = Frame.from_method(methodid)
for i, v in enumerate(input.values):
    
    match v: 
        case jvm.Value(type=jvm.Int(), value = value):
            v = v
        case jvm.Value(type=jvm.Boolean(), value = value):
            logger.debug(f"converting boolean {value} to int")
            v = jvm.Value.int(1 if value else 0)
        case _:
            raise NotImplementedError(f"Don't know how to handle input value: {v!r}")
    frame.locals[i] = v

state = State({}, Stack.empty().push(frame))

for x in range(1000):
    state = step(state)
    if isinstance(state, str):
        print(state)
        break
else:
    print("*")
