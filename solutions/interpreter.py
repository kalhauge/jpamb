"""
jpamb.jvm.opcode

This module contains the decompilation of the output of jvm2json
into a python structure, as well documentation and semantics for
each instruction.

Sample execution:
- `uv run jpamb interpret --stepwise --filter Simple.divideByN: solutions/interpreter.py`
"""
import sys
import re

from dataclasses import dataclass

from loguru import logger

import jpamb
from jpamb.model import Input
from jpamb import jvm


def wrap_value(value: any) -> jvm.Value:
    """Parses the input value to a [jvm.Value] object"""
    match value:
        case bool():
            return jvm.Value.boolean(value)
        case int():
            return jvm.Value.int(value)
        case str() if len(value) == 1:
            return jvm.Value.char(value)
        case tuple():
            # TODO implement for different types, not only int
            return jvm.Value.array(jvm.Int(), value)
        case None:
            return jvm.Value.boolean(False)
        case _:
            raise TypeError(f"Do not know how to wrap {value!r}")


@dataclass
class PC:
    """
    Program Counter of the program.
    It contains the Method Id and the Offset.
    ι = ⟨ι_m, ι_o⟩
    ι + n = ⟨ι_m, ι_o + n⟩
    n/ι = ⟨ι_m, n⟩
    """

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
    """
    Context (bytecode) of the program.
    It performs a simple operation bd[ι] which looks up the bytecode
    instruction at ι.
    """
    suite: jpamb.Suite
    methods: dict[jvm.AbsMethodID, list[jvm.Opcode]]

    def __getitem__(self, pc: PC) -> jvm.Opcode:
        try:
            opcodes = self.methods[pc.method]
        except KeyError:
            opcodes = list(self.suite.method_opcodes(pc.method))
            self.methods[pc.method] = opcodes

        return opcodes[pc.offset]

    def get_static_field(self, pc: PC, field: jvm.AbsFieldID) -> jvm.Value:
        """Returns the static field value given PC and field id."""
        fields = self.suite.findclass(pc.method.classname)["fields"]
        for f in fields:
            if f["name"] == field.fieldid.name:
                return wrap_value(f["value"])
        raise KeyError(f"Static field not found: {field.fieldid.name}")


@dataclass
class Stack[T]:
    """
    The JVM is a stack based machine: it uses an operator stack.

    A stack is a list of values:
    σ = 𝐕_σ*.

    Each value is defined as follows:
    𝐕_σ := (int n) | (float f) | (ref r)
    ('ref' represents a reference to the heap / global memory).
    """
    items: list[T]

    def __bool__(self) -> bool:
        return len(self.items) > 0

    @classmethod
    def empty(cls):
        """Returns an empty instance of [Stack]."""
        return cls([])

    def peek(self) -> T:
        """Peek the last element of the [Stack]."""
        return self.items[-1]

    def pop(self) -> T:
        """Pops the last element of the [Stack]."""
        return self.items.pop(-1)

    def push(self, value: T):
        """Pushes the value in the [Stack]."""
        self.items.append(value)
        return self

    def __str__(self):
        return "ϵ" if not self else "".join(f"{v}" for v in self.items)


@dataclass  # type: ignore
class Frame:
    """
    The state of the JVM is a triplet:
    ⟨λ, σ, ι⟩

    Where:
    - λ is the Locals that stores local variables of type 𝐕_σ
    - σ is the Operational Stack
    - ι is the Program Counter
    """
    locals: dict[int, jvm.Value]
    stack: Stack[jvm.Value]
    pc: PC

    def __str__(self):
        locals_str = ", ".join(f"{k}:{v}" for k, v in self.locals.items())
        return f"<{{{locals_str}}}, {self.stack}, {self.pc}>"

    @classmethod
    def from_method(cls, method: jvm.AbsMethodID) -> "Frame":
        """Returns an empty Frame object from the method id."""
        return Frame({}, Stack.empty(), PC(method, 0))


@dataclass  # type: ignore
class State:
    """
    In the JVM methods are capable of calling other methods.
    The State needs to be a tuple of the heap and the call stack:
    ⟨η,μ⟩

    The heap η is the way for frames to share data.
    The heap is a mapping from memory locations (int) to 𝐕_η (heap values).

    The heap values are defined as follows:
    𝐕_η := 𝐕_σ | (byte b) | (char c) | (short s) | (array t a) | (object cn fs)
    """
    heap: dict[int, jvm.Value]
    frames: Stack[Frame]

class Step_class:

    def __init__(self): 
        self.bytecode = None
        self.frame = None
        self.state = None

    def update_state(self, state: State):
        self.state = state
        self.frame = self.state.frames.peek()

    def update_frame(self):
        self.frame = self.state.frames.peek()
 
    def _push(self, value):
        """bc ⊢ ⟨λ, σ, ι⟩ → ⟨λ, σ‾, ι‾⟩"""
        self.frame.stack.push(value)
        self.frame.pc += 1
        return self.state

    def _load(self, index):
        """
        bc ⊢ ⟨λ, σ, ι⟩ → ⟨λ, σ‾, ι‾⟩
        """
        value = self.frame.locals[index]
        assert value.type is jvm.Int() or jvm.Boolean()
        self.frame.stack.push(value)
        self.frame.pc += 1
        return self.state

    def _binary_add(self):
        """bc ⊢ ⟨λ, σ, ι⟩ → ⟨λ, σ‾, ι‾⟩"""
        v2, v1 = self.frame.stack.pop(), self.frame.stack.pop()
        assert v1.type is jvm.Int(), f"expected int, but got {v1}"
        assert v2.type is jvm.Int(), f"expected int, but got {v2}"
        self.frame.stack.push(jvm.Value.int(v1.value + v2.value))
        self.frame.pc += 1
        return self.state

    def _binary_sub(self):
        """bc ⊢ ⟨λ, σ, ι⟩ → ⟨λ, σ‾, ι‾⟩"""
        v2, v1 = self.frame.stack.pop(), self.frame.stack.pop()
        assert v1.type is jvm.Int(), f"expected int, but got {v1}"
        assert v2.type is jvm.Int(), f"expected int, but got {v2}"
        self.frame.stack.push(jvm.Value.int(v1.value - v2.value))
        self.frame.pc += 1
        return self.state

    def _binary_div(self ):
        """bc ⊢ ⟨λ, σ, ι⟩ → ⟨λ, σ‾, ι‾⟩"""
        v2, v1 = self.frame.stack.pop(), self.frame.stack.pop()
        assert v1.type is jvm.Int(), f"expected int, but got {v1}"
        assert v2.type is jvm.Int(), f"expected int, but got {v2}"
        if v2.value == 0:
            return "divide by zero"
        self.frame.stack.push(jvm.Value.int(v1.value // v2.value))
        self.frame.pc += 1
        return self.state

    def _binary_rem(self ):
        """
        bc ⊢ ⟨λ, σ, ι⟩ → ⟨λ, σ‾, ι‾⟩
        rem = value1 - (value1 / value2) * value2
        """
        v2, v1 = self.frame.stack.pop(), self.frame.stack.pop()
        assert v1.type is jvm.Int(), f"expected int, but got {v1}"
        assert v2.type is jvm.Int(), f"expected int, but got {v2}"
        if v2.value == 0:
            return "divide by zero"
        vv1, vv2 = v1.value, v2.value
        self.frame.stack.push(jvm.Value.int(vv1 - (vv1 // vv2) * vv2))
        self.frame.pc += 1
        return self.state

    def _binary_mul(self):
        """bc ⊢ ⟨λ, σ, ι⟩ → ⟨λ, σ‾, ι‾⟩"""
        v2, v1 = self.frame.stack.pop(), self.frame.stack.pop()
        assert v1.type is jvm.Int(), f"expected int, but got {v1}"
        assert v2.type is jvm.Int(), f"expected int, but got {v2}"

        self.frame.stack.push(self, jvm.Value.int(v1.value * v2.value))
        self.frame.pc += 1
        return self.state

    def _dup(self):
        """bc ⊢ ⟨λ, σ, ι⟩ → ⟨λ, σ‾, ι‾⟩"""
        value = self.frame.stack.peek()
        self.frame.stack.push(value)
        self.frame.pc += 1
        return self.state

    def _get_static(self, field):
        """
        Pushes the value of the specified static field onto the operand stack.
        bc ⊢ ⟨λ, σ, ι⟩ → ⟨λ, σ‾, ι‾⟩
        """
        value = self.bytecode.get_static_field(self.frame.pc, field)
        self.frame.stack.push(value)
        self.frame.pc += 1
        return self.state
    
    def _get_field(self, field):
        """
        Pops an object reference from the stack.
        Pushes the value of the specified field onto the stack
        Throws NullPointerException if object reference is null

        bc ⊢ ⟨λ, σ, ι⟩ → ⟨λ, σ‾, ι‾⟩
        """

        objref = self.frame.stack.pop()

        if objref.value is None:
            return "NullPointerException"
        obj = state.heap.get(objref.value)
        if obj is None:
            raise RuntimeError(f"Invalid object reference {objref}")
        v = obj.value[field.fieldid.name]
        if v is None:
            raise RuntimeError(f"Field {field} not found in object {objref}")
        self.frame.stack.push(v)

        self.frame.pc += 1
        return self.state

    def _if(self, condition: str, target: int, ifz: bool = False):
        """
        1. Pops two values from the operand stack (one in case of [ifz == True]).
        2. Compares them according to the condition (with 0 in case of [ifz == True]).
        3. Jumps to target instruction if condition is true.
        4. Continues to next instruction if condition is false.
        """
        if ifz:
            value = self.frame.stack.pop()
            if value.type is jvm.Boolean():
                v1 = 1 if value.value else 0
            else:
                v1 = value.value
            v2 = 0
        else:
            v2, v1 = self.frame.stack.pop().value, self.frame.stack.pop().value
        match condition:
            case 'ne':
                jump = v1 != v2
            case 'eq':
                jump = v1 == v2
            case 'ne':
                jump = v1 != v2
            case 'ge':
                jump = v1 >= v2
            case 'gt':
                jump = v1 > v2
            case 'lt':
                jump = v1 < v2
            case 'le':
                jump = v1 <= v2
            case unknown:
                raise NotImplementedError(f"Unknown condition: {unknown!r}")

        self.frame.pc.offset = target if jump else self.frame.pc.offset + 1
        return self.state

    def _invoke_static(self, method: jvm.AbsMethodID):
        """The invoke static opcode for calling static methods
        bc ⊢ ⟨λ, σ, ι⟩ → ⟨λ', σ', ι'⟩
        """
        new_frame = self.frame.from_method(method)
        new_frame.pc = PC(method, 0)

        #Note: this loop should technically be reversed, argumennts on the stack itself are put as arg1, arg2, arg3...
        #But it doesn't matter for our "simple" calls
        for index, param in enumerate(method.extension.params):
            local = self.frame.stack.pop()

            # assert isinstance(local.type, type(param)), f'''
            # Inappropriate argument type: {local.type!r}
            # (expected {param!r})
            # '''

            new_frame.locals[index] = local

        state.self.frames.push(new_frame)
        return self.state

    def _invoke_special(self, method: jvm.AbsMethodID, is_interface: bool):
        """
        The invoke special opcode for calling constructors, private methods, and superclass methods.
        bc ⊢ ⟨λ, σ, ι⟩ → ⟨λ', σ', ι'⟩
        """

        if method.classname.name == "java/lang/Object" and method.methodid.name == "<init>":
            self.frame.pc += 1
            return self.state
        
        new_frame = self.frame.from_method(method)
        new_frame.pc = PC(method, 0)

        #technically, we shoudl also determine whether our method is static or not - if it is, we should get our variables from the stack
        #if it is not, we should get it from the heap
        #but let's not overcomplicate it for now

        #params + reference - important especially for new classes
        param_count = len(method.methodid.params) + 1
        
        args = []
        for _ in range(param_count):
            args.insert(0, self.frame.stack.pop())
        
        for i, arg in enumerate(args):
            new_frame.locals[i] = arg
        

        state.self.frames.push(new_frame)
        #important: we don't have self.frame.pc += 1, because return instruction later would do it for us
        return self.state
    
    def _invoke_virtual(self, method: jvm.AbsMethodID):
        """
        The invoke virtual opcode for calling instance methods
        bc ⊢ ⟨λ, σ, ι⟩ → ⟨λ', σ', ι'⟩
        """
        
        new_frame = self.frame.from_method(method)
        new_frame.pc = PC(method, 0)

        param_count = len(method.methodid.params) + 1
        
        args = []
        for _ in range(param_count):
            args.insert(0, self.frame.stack.pop())
        
        for i, arg in enumerate(args):
            new_frame.locals[i] = arg        

        state.self.frames.push(new_frame)
        
        return self.state

    def _return(self, return_type: jvm.Type | None):
        """
        bc ⊢ ⟨λ, σ, ι⟩ → ⟨λ', σ', ι'⟩

        1. Returns control to the invoker of the current method, if present.
        2. If type is present, returns a value of that type to invoker.
        3. If type is None (void return), returns no value.
        """
        state.self.frames.pop()
        if state.self.frames:
            new_frame = state.self.frames.peek()

            if return_type is not None:
                value = self.frame.stack.pop()

                # assert value.type is return_type, f'Return type mismatch {return_type} {value.type}'

                new_frame.stack.push(value)

            new_frame.pc += 1
            return self.state
        return "ok"

    def _new(self, classname: jvm.ClassName):
        """
        The new opcode that creates a new instance of a class.
        bc ⊢ ⟨λ, σ, ι⟩ → ⟨λ, σ', ι'⟩
        """

        match classname.name:
            case 'java/lang/AssertionError':
                return 'assertion error'
            case _:
                suite = jpamb.Suite()
                class_info = suite.findclass(classname)
                #we need to push an reference of this class onto the stack
                #dict -> jvm.AbsMethodID?
                #I don't know exactly how methodID is read later from the stack ....

                instance_fields: dict[str, jvm.Value] = {}
                for f in class_info.get("fields", []):
                    if f.get("static", False):
                        continue
                    
                    field_name = f["name"]
                    field_type = f["type"]["base"]
                    
                    match field_type:
                        case "int":
                            instance_fields[field_name] = jvm.Value.int(0)
                        case "boolean":
                            instance_fields[field_name] = jvm.Value.boolean(False)
                        case _:
                            instance_fields[field_name] = jvm.Value(jvm.Reference(), None)

                ref = max(self.state.heap.keys()) + 1 if self.state.heap else 0
                
                obj_value = jvm.Value(jvm.Object(classname), instance_fields)
                self.state.heap[ref] = obj_value

                self.frame.stack.push(jvm.Value.int(ref))
                self.frame.pc += 1

                return self.state

    def _new_array(self, array_type: jvm.Type):
        assert array_type is jvm.Int(), f'NewArray {array_type} not handled'

        size = self.frame.stack.pop()
        assert size.type is jvm.Int(), 'Size must be of type Int'

        array = [0 for _ in range(size.value)]

        # TODO extract
        ref = max(state.heap.keys()) + 1 if len(state.heap.keys()) > 0 else 0
        state.heap[ref] = jvm.Value.array(array_type, array)

        self.frame.stack.push(jvm.Value.int(ref))
        self.frame.pc += 1
        return self.state

    def _store(self, index: int):
        value = self.frame.stack.pop()
        self.frame.locals[index] = value

        self.frame.pc += 1
        return self.state

    def _array_store(self, array_type: jvm.Type):
        value, index, ref = self.frame.stack.pop(), self.frame.stack.pop(), self.frame.stack.pop()

        if ref.value is None:
            return 'null pointer'

        assert ref.type is jvm.Int(), f'Array ref type mismatch {ref!r}'
        assert index.type is jvm.Int(), f'Index type mismatch {index.type}'
        assert value.type is array_type, f'Value type mismatch {value.type}'

        old_array = state.heap[ref.value]

        if index.value >= len(old_array.value):
            return 'out of bounds'

        new_array = list(old_array.value)
        new_array[index.value] = value.value

        state.heap[ref.value] = jvm.Value.array(array_type, new_array)

        self.frame.pc += 1
        return self.state

    def _array_load(self, array_type: jvm.Type):
        index, ref = self.frame.stack.pop(), self.frame.stack.pop()

        assert ref.type is jvm.Int(), f'Array ref type mismatch {ref!r}'
        assert index.type is jvm.Int(), f'Index type mismatch {index.type}'

        array = list(state.heap[ref.value].value)
        if index.value >= len(array):
            return 'out of bounds'

        value = array[index.value]

        match array_type:
            case jvm.Int():
                self.frame.stack.push(jvm.Value.int(value))
            case jvm.Char():
                self.frame.stack.push(jvm.Value.int(ord(value)))
            case _:
                raise NotImplementedError(f"Unknown array type: {array_type}")

        self.frame.pc += 1
        return self.state

    def _goto(self, target: int):
        self.frame.pc.offset = target
        return self.state

    def _load(self, index: int):
        value = self.frame.locals[index]
        self.frame.stack.push(value)

        self.frame.pc += 1
        return self.state

    def _array_length(self, ):
        ref = self.frame.stack.pop()

        if ref.value is None:
            return 'null pointer'

        array = state.heap[ref.value]
        length = len(array.value)

        self.frame.stack.push(jvm.Value.int(length))

        self.frame.pc += 1
        return self.state

    def _incr(self, index: int, amount: int):
        assert self.frame.locals[index].type is jvm.Int(), 'Incr type mismatch'

        old_value = self.frame.locals[index].value
        new_value = old_value + amount

        self.frame.locals[index] = jvm.Value.int(new_value)

        self.frame.pc += 1
        return self.state

    def _cast(self, from_: jvm.Type, to_: jvm.Type):
        match from_, to_:
            case jvm.Int(), jvm.Short():
                value = self.frame.stack.pop()
                casted = jvm.Value(jvm.Short(), value.value)
                self.frame.stack.push(casted)
            case _:
                raise NotImplementedError(f'From {from_} To {to_} not handled')

        self.frame.pc += 1
        return self.state

    def _put_field(self, field: jvm.AbsFieldID):
            """Store value into an instance field"""
            value = self.frame.stack.pop() 
            obj_ref = self.frame.stack.pop()  

            if obj_ref.value is None:
                return 'null pointer'
                
            heap_obj = state.heap[obj_ref.value]
            
            if isinstance(heap_obj.value, dict):
                heap_obj.value[field.fieldid.name] = value
            
            self.frame.pc += 1
            return self.state

    def step(self, state: State, bytecode: Bytecode) -> State | str:
        """
        Stepping function:
        bc ⊢ ⟨η,μ⟩ → ⟨η‾,μ‾⟩
        """

        self.frame = state.frames.peek()
        self.bytecode = bytecode
    
        logger.info(f"-- Bytecode[{self.frame.pc}]: {self.bytecode[self.frame.pc]}")
        logger.info(f"Op Stack[{self.frame.stack}]")
        logger.info(f"State heap[{state.heap}]")
        match self.bytecode[self.frame.pc]:
            case jvm.Push(value=v): return self._push(value=v)
            case jvm.Load(type=jvm.Int(), index=n): return self._load(index=n)
            case jvm.Binary(type=jvm.Int(), operant=jvm.BinaryOpr.Add): return self._binary_add()
            case jvm.Binary(type=jvm.Int(), operant=jvm.BinaryOpr.Sub): return self._binary_sub()
            case jvm.Binary(type=jvm.Int(), operant=jvm.BinaryOpr.Div): return self._binary_div()
            case jvm.Binary(type=jvm.Int(), operant=jvm.BinaryOpr.Rem): return self._binary_rem()
            case jvm.Binary(type=jvm.Int(), operant=jvm.BinaryOpr.Mul): return self._binary_mul()
            case jvm.Incr(index=i, amount=a): return self._incr(index=i, amount=a)
            case jvm.Dup(words=1): return self._dup()
            case jvm.Get(static=True, field=f): return self._get_static(field=f)
            case jvm.Get(static=False, field=f): return self._get_field(field=f)
            case jvm.Return(type=t): return self._return(return_type=t)
            case jvm.If(condition=c, target=t): return self._if(condition=c, target=t)
            case jvm.Ifz(condition=c, target=t): return self._if(condition=c, target=t, ifz=True)
            case jvm.New(classname=cn): return self._new(classname=cn)
            case jvm.Store(type=_, index=i): return self._store(index=i)
            case jvm.NewArray(type=t, dim=1): return self._new_array(array_type=t)
            case jvm.ArrayStore(type=t): return self._array_store(array_type=t)
            case jvm.ArrayLoad(type=t): return self._array_load(array_type=t)
            case jvm.ArrayLength(): return self._array_length()
            case jvm.InvokeStatic(method=m): return self._invoke_static(method=m)
            case jvm.InvokeSpecial(method=m, is_interface=is_interface): return self._invoke_special(method=m, is_interface=is_interface)
            case jvm.InvokeVirtual(method=m): return self._invoke_virtual(method=m)
            case jvm.Goto(target=t): return self._goto(target=t)
            case jvm.Load(type=jvm.Reference(), index=i): return self._load(index=i)
            case jvm.Cast(from_=f, to_=t): return self._cast(from_=f, to_=t)
            case jvm.Put(static=False, field=f): return self._put_field(field=f)
            case jvm.Put(static=True, field=f): 
                raise NotImplementedError("putstatic not implemented")

            case unknown:
                raise NotImplementedError(f"Don't know how to handle: {unknown!r}")


def step(state: State, bytecode: Bytecode) -> State | str:
    """
    Stepping function:
    bc ⊢ ⟨η,μ⟩ → ⟨η‾,μ‾⟩
    """

    frame = state.frames.peek()

    def _push(value):
        """bc ⊢ ⟨λ, σ, ι⟩ → ⟨λ, σ‾, ι‾⟩"""
        frame.stack.push(value)
        frame.pc += 1
        return state

    def _load(index):
        """
        bc ⊢ ⟨λ, σ, ι⟩ → ⟨λ, σ‾, ι‾⟩
        """
        value = frame.locals[index]
        assert value.type is jvm.Int() or jvm.Boolean()
        frame.stack.push(value)
        frame.pc += 1
        return state

    def _binary_add():
        """bc ⊢ ⟨λ, σ, ι⟩ → ⟨λ, σ‾, ι‾⟩"""
        v2, v1 = frame.stack.pop(), frame.stack.pop()
        assert v1.type is jvm.Int(), f"expected int, but got {v1}"
        assert v2.type is jvm.Int(), f"expected int, but got {v2}"
        frame.stack.push(jvm.Value.int(v1.value + v2.value))
        frame.pc += 1
        return state

    def _binary_sub():
        """bc ⊢ ⟨λ, σ, ι⟩ → ⟨λ, σ‾, ι‾⟩"""
        v2, v1 = frame.stack.pop(), frame.stack.pop()
        assert v1.type is jvm.Int(), f"expected int, but got {v1}"
        assert v2.type is jvm.Int(), f"expected int, but got {v2}"
        frame.stack.push(jvm.Value.int(v1.value - v2.value))
        frame.pc += 1
        return state

    def _binary_div():
        """bc ⊢ ⟨λ, σ, ι⟩ → ⟨λ, σ‾, ι‾⟩"""
        v2, v1 = frame.stack.pop(), frame.stack.pop()
        assert v1.type is jvm.Int(), f"expected int, but got {v1}"
        assert v2.type is jvm.Int(), f"expected int, but got {v2}"
        if v2.value == 0:
            return "divide by zero"
        frame.stack.push(jvm.Value.int(v1.value // v2.value))
        frame.pc += 1
        return state

    def _binary_rem():
        """
        bc ⊢ ⟨λ, σ, ι⟩ → ⟨λ, σ‾, ι‾⟩
        rem = value1 - (value1 / value2) * value2
        """
        v2, v1 = frame.stack.pop(), frame.stack.pop()
        assert v1.type is jvm.Int(), f"expected int, but got {v1}"
        assert v2.type is jvm.Int(), f"expected int, but got {v2}"
        if v2.value == 0:
            return "divide by zero"
        vv1, vv2 = v1.value, v2.value
        frame.stack.push(jvm.Value.int(vv1 - (vv1 // vv2) * vv2))
        frame.pc += 1
        return state

    def _binary_mul():
        """bc ⊢ ⟨λ, σ, ι⟩ → ⟨λ, σ‾, ι‾⟩"""
        v2, v1 = frame.stack.pop(), frame.stack.pop()
        assert v1.type is jvm.Int(), f"expected int, but got {v1}"
        assert v2.type is jvm.Int(), f"expected int, but got {v2}"

        frame.stack.push(jvm.Value.int(v1.value * v2.value))
        frame.pc += 1
        return state

    def _dup():
        """bc ⊢ ⟨λ, σ, ι⟩ → ⟨λ, σ‾, ι‾⟩"""
        value = frame.stack.peek()
        frame.stack.push(value)
        frame.pc += 1
        return state

    def _get_static(field):
        """
        Pushes the value of the specified static field onto the operand stack.
        bc ⊢ ⟨λ, σ, ι⟩ → ⟨λ, σ‾, ι‾⟩
        """
        value = bytecode.get_static_field(frame.pc, field)
        frame.stack.push(value)
        frame.pc += 1
        return state
    
    def _get_field(field):
        """
        Pops an object reference from the stack.
        Pushes the value of the specified field onto the stack
        Throws NullPointerException if object reference is null

        bc ⊢ ⟨λ, σ, ι⟩ → ⟨λ, σ‾, ι‾⟩
        """

        objref = frame.stack.pop()

        if objref.value is None:
            return "NullPointerException"
        obj = state.heap.get(objref.value)
        if obj is None:
            raise RuntimeError(f"Invalid object reference {objref}")
        v = obj.value[field.fieldid.name]
        if v is None:
            raise RuntimeError(f"Field {field} not found in object {objref}")
        frame.stack.push(v)

        frame.pc += 1
        return state

    def _if(condition: str, target: int, ifz: bool = False):
        """
        1. Pops two values from the operand stack (one in case of [ifz == True]).
        2. Compares them according to the condition (with 0 in case of [ifz == True]).
        3. Jumps to target instruction if condition is true.
        4. Continues to next instruction if condition is false.
        """
        if ifz:
            value = frame.stack.pop()
            if value.type is jvm.Boolean():
                v1 = 1 if value.value else 0
            else:
                v1 = value.value
            v2 = 0
        else:
            v2, v1 = frame.stack.pop().value, frame.stack.pop().value
        match condition:
            case 'ne':
                jump = v1 != v2
            case 'eq':
                jump = v1 == v2
            case 'ne':
                jump = v1 != v2
            case 'ge':
                jump = v1 >= v2
            case 'gt':
                jump = v1 > v2
            case 'lt':
                jump = v1 < v2
            case 'le':
                jump = v1 <= v2
            case unknown:
                raise NotImplementedError(f"Unknown condition: {unknown!r}")

        frame.pc.offset = target if jump else frame.pc.offset + 1
        return state

    def _invoke_static(method: jvm.AbsMethodID):
        """The invoke static opcode for calling static methods
        bc ⊢ ⟨λ, σ, ι⟩ → ⟨λ', σ', ι'⟩
        """
        new_frame = Frame.from_method(method)
        new_frame.pc = PC(method, 0)

        #Note: this loop should technically be reversed, argumennts on the stack itself are put as arg1, arg2, arg3...
        #But it doesn't matter for our "simple" calls
        for index, param in enumerate(method.extension.params):
            local = frame.stack.pop()

            # assert isinstance(local.type, type(param)), f'''
            # Inappropriate argument type: {local.type!r}
            # (expected {param!r})
            # '''

            new_frame.locals[index] = local

        state.frames.push(new_frame)
        return state

    def _invoke_special(method: jvm.AbsMethodID, is_interface: bool):
        """
        The invoke special opcode for calling constructors, private methods, and superclass methods.
        bc ⊢ ⟨λ, σ, ι⟩ → ⟨λ', σ', ι'⟩
        """

        if m.classname.name == "java/lang/Object" and m.methodid.name == "<init>":
            frame.pc += 1
            return state
        
        new_frame = Frame.from_method(method)
        new_frame.pc = PC(method, 0)

        #technically, we shoudl also determine whether our method is static or not - if it is, we should get our variables from the stack
        #if it is not, we should get it from the heap
        #but let's not overcomplicate it for now

        #params + reference - important especially for new classes
        param_count = len(method.methodid.params) + 1
        
        args = []
        for _ in range(param_count):
            args.insert(0, frame.stack.pop())
        
        for i, arg in enumerate(args):
            new_frame.locals[i] = arg
        

        state.frames.push(new_frame)
        #important: we don't have frame.pc += 1, because return instruction later would do it for us
        return state
    
    def _invoke_virtual(method: jvm.AbsMethodID):
        """
        The invoke virtual opcode for calling instance methods
        bc ⊢ ⟨λ, σ, ι⟩ → ⟨λ', σ', ι'⟩
        """
        
        new_frame = Frame.from_method(method)
        new_frame.pc = PC(method, 0)

        param_count = len(method.methodid.params) + 1
        
        args = []
        for _ in range(param_count):
            args.insert(0, frame.stack.pop())
        
        for i, arg in enumerate(args):
            new_frame.locals[i] = arg        

        state.frames.push(new_frame)
        
        return state

    def _return(return_type: jvm.Type | None):
        """
        bc ⊢ ⟨λ, σ, ι⟩ → ⟨λ', σ', ι'⟩

        1. Returns control to the invoker of the current method, if present.
        2. If type is present, returns a value of that type to invoker.
        3. If type is None (void return), returns no value.
        """
        state.frames.pop()
        if state.frames:
            new_frame = state.frames.peek()

            if return_type is not None:
                value = frame.stack.pop()

                # assert value.type is return_type, f'Return type mismatch {return_type} {value.type}'

                new_frame.stack.push(value)

            new_frame.pc += 1
            return state
        return "ok"

    def _new(classname: jvm.ClassName):
        """
        The new opcode that creates a new instance of a class.
        bc ⊢ ⟨λ, σ, ι⟩ → ⟨λ, σ', ι'⟩
        """

        match classname.name:
            case 'java/lang/AssertionError':
                return 'assertion error'
            case _:
                suite = jpamb.Suite()
                class_info = suite.findclass(classname)
                #we need to push an reference of this class onto the stack
                #dict -> jvm.AbsMethodID?
                #I don't know exactly how methodID is read later from the stack ....

                instance_fields: dict[str, jvm.Value] = {}
                for f in class_info.get("fields", []):
                    if f.get("static", False):
                        continue
                    
                    field_name = f["name"]
                    field_type = f["type"]["base"]
                    
                    match field_type:
                        case "int":
                            instance_fields[field_name] = jvm.Value.int(0)
                        case "boolean":
                            instance_fields[field_name] = jvm.Value.boolean(False)
                        case _:
                            instance_fields[field_name] = jvm.Value(jvm.Reference(), None)

                ref = max(state.heap.keys()) + 1 if state.heap else 0
                
                obj_value = jvm.Value(jvm.Object(classname), instance_fields)
                state.heap[ref] = obj_value

                frame.stack.push(jvm.Value.int(ref))
                frame.pc += 1

                return state

    def _new_array(array_type: jvm.Type):
        assert array_type is jvm.Int(), f'NewArray {array_type} not handled'

        size = frame.stack.pop()
        assert size.type is jvm.Int(), 'Size must be of type Int'

        array = [0 for _ in range(size.value)]

        # TODO extract
        ref = max(state.heap.keys()) + 1 if len(state.heap.keys()) > 0 else 0
        state.heap[ref] = jvm.Value.array(array_type, array)

        frame.stack.push(jvm.Value.int(ref))
        frame.pc += 1
        return state

    def _store(index: int):
        value = frame.stack.pop()
        frame.locals[index] = value

        frame.pc += 1
        return state

    def _array_store(array_type: jvm.Type):
        value, index, ref = frame.stack.pop(), frame.stack.pop(), frame.stack.pop()

        if ref.value is None:
            return 'null pointer'

        assert ref.type is jvm.Int(), f'Array ref type mismatch {ref!r}'
        assert index.type is jvm.Int(), f'Index type mismatch {index.type}'
        assert value.type is array_type, f'Value type mismatch {value.type}'

        old_array = state.heap[ref.value]

        if index.value >= len(old_array.value):
            return 'out of bounds'

        new_array = list(old_array.value)
        new_array[index.value] = value.value

        state.heap[ref.value] = jvm.Value.array(array_type, new_array)

        frame.pc += 1
        return state

    def _array_load(array_type: jvm.Type):
        index, ref = frame.stack.pop(), frame.stack.pop()

        assert ref.type is jvm.Int(), f'Array ref type mismatch {ref!r}'
        assert index.type is jvm.Int(), f'Index type mismatch {index.type}'

        array = list(state.heap[ref.value].value)
        if index.value >= len(array):
            return 'out of bounds'

        value = array[index.value]

        match array_type:
            case jvm.Int():
                frame.stack.push(jvm.Value.int(value))
            case jvm.Char():
                frame.stack.push(jvm.Value.int(ord(value)))
            case _:
                raise NotImplementedError(f"Unknown array type: {array_type}")

        frame.pc += 1
        return state

    def _goto(target: int):
        frame.pc.offset = target
        return state

    def _load(index: int):
        value = frame.locals[index]
        frame.stack.push(value)

        frame.pc += 1
        return state

    def _array_length():
        ref = frame.stack.pop()

        if ref.value is None:
            return 'null pointer'

        array = state.heap[ref.value]
        length = len(array.value)

        frame.stack.push(jvm.Value.int(length))

        frame.pc += 1
        return state

    def _incr(index: int, amount: int):
        assert frame.locals[index].type is jvm.Int(), 'Incr type mismatch'

        old_value = frame.locals[index].value
        new_value = old_value + amount

        frame.locals[index] = jvm.Value.int(new_value)

        frame.pc += 1
        return state

    def _cast(from_: jvm.Type, to_: jvm.Type):
        match from_, to_:
            case jvm.Int(), jvm.Short():
                value = frame.stack.pop()
                casted = jvm.Value(jvm.Short(), value.value)
                frame.stack.push(casted)
            case _:
                raise NotImplementedError(f'From {from_} To {to_} not handled')

        frame.pc += 1
        return state

    def _put_field(field: jvm.AbsFieldID):
        """Store value into an instance field"""
        value = frame.stack.pop() 
        obj_ref = frame.stack.pop()  

        if obj_ref.value is None:
            return 'null pointer'
            
        heap_obj = state.heap[obj_ref.value]
        
        if isinstance(heap_obj.value, dict):
            heap_obj.value[field.fieldid.name] = value
        
        frame.pc += 1
        return state

    logger.info(f"-- Bytecode[{frame.pc}]: {bytecode[frame.pc]}")
    logger.info(f"Op Stack[{frame.stack}]")
    logger.info(f"State heap[{state.heap}]")
    logger.info(f"Locals: {frame.locals}")
    match bytecode[frame.pc]:
        case jvm.Push(value=v): return _push(value=v)
        case jvm.Load(type=jvm.Int(), index=n): return _load(index=n)
        case jvm.Binary(type=jvm.Int(), operant=jvm.BinaryOpr.Add): return _binary_add()
        case jvm.Binary(type=jvm.Int(), operant=jvm.BinaryOpr.Sub): return _binary_sub()
        case jvm.Binary(type=jvm.Int(), operant=jvm.BinaryOpr.Div): return _binary_div()
        case jvm.Binary(type=jvm.Int(), operant=jvm.BinaryOpr.Rem): return _binary_rem()
        case jvm.Binary(type=jvm.Int(), operant=jvm.BinaryOpr.Mul): return _binary_mul()
        case jvm.Incr(index=i, amount=a): return _incr(index=i, amount=a)
        case jvm.Dup(words=1): return _dup()
        case jvm.Get(static=True, field=f): return _get_static(field=f)
        case jvm.Get(static=False, field=f): return _get_field(field=f)
        case jvm.Return(type=t): return _return(return_type=t)
        case jvm.If(condition=c, target=t): return _if(condition=c, target=t)
        case jvm.Ifz(condition=c, target=t): return _if(condition=c, target=t, ifz=True)
        case jvm.New(classname=cn): return _new(classname=cn)
        case jvm.Store(type=_, index=i): return _store(index=i)
        case jvm.NewArray(type=t, dim=1): return _new_array(array_type=t)
        case jvm.ArrayStore(type=t): return _array_store(array_type=t)
        case jvm.ArrayLoad(type=t): return _array_load(array_type=t)
        case jvm.ArrayLength(): return _array_length()
        case jvm.InvokeStatic(method=m): return _invoke_static(method=m)
        case jvm.InvokeSpecial(method=m, is_interface=is_interface): return _invoke_special(method=m, is_interface=is_interface)
        case jvm.InvokeVirtual(method=m): return _invoke_virtual(method=m)
        case jvm.Goto(target=t): return _goto(target=t)
        case jvm.Load(type=jvm.Reference(), index=i): return _load(index=i)
        case jvm.Cast(from_=f, to_=t): return _cast(from_=f, to_=t)
        case jvm.Put(static=False, field=f): return _put_field(field=f)
        case jvm.Put(static=True, field=f): 
            raise NotImplementedError("putstatic not implemented")

        case unknown:
            raise NotImplementedError(f"Don't know how to handle: {unknown!r}")


def configure_logger():
    """Configures the logger with a custom format."""
    logger.remove()
    logger.add(sys.stderr, format="[{level}] {message}")


def generate_initial_frame(method_id: jvm.AbsMethodID, method_input: Input) -> tuple[Frame, dict[int, jvm.Value]]:
    """Generates the initial frame from the given method id and method input"""
    initial_frame = Frame.from_method(method_id)
    heap = {}

    #logger.debug(method_input.values)
    #logger.debug(method_input.values[0].type)
    #uv run solutions/interpreter.py "jpamb.cases.CustomClasses.Withdraw:(Ljpamb/cases/PositiveInteger;)V" "(new jpamb/cases/PositiveInteger(5))"

    for index, value in enumerate(method_input.values):
        # match value:
        #     case jvm.Value(type=jvm.Boolean(), value=value):
        #         local = jvm.Value.int(1 if value else 0)
        #     case jvm.Value(type=jvm.Int(), value=value):
        #         local = value
        #     case _:
        #         assert False, f"Do not know how to handle {value}"

        #check if it is of type of custom class
        logger.debug(value.type)
        m = re.match(r"^L([A-Za-z0-9_/\$]+);$",str(value.type))
        if m is not None:
            #custom class found
            class_name_str = m.group(1)
            class_name = jvm.ClassName(class_name_str)

            ref = max(heap.keys()) + 1 if heap else 0
            obj_value = jvm.Value(jvm.Object(class_name), value.value)
            heap[ref] = obj_value
            initial_frame.locals[index] = jvm.Value.int(ref)
        else:
            local = wrap_value(value.value)
            if isinstance(local.type, jvm.Array):
                ref = len(heap.values())
                heap[ref] = local
                initial_frame.locals[index] = jvm.Value.int(ref)
            else:
                initial_frame.locals[index] = local

    logger.debug(f"Initial frame local variable {initial_frame.locals}")
    logger.debug(f"Heap {heap}")
    return initial_frame, heap

def input_is_an_object() -> bool:
    input = sys.argv[2]
    class_input = re.search(r"\(new\s+([A-Za-z_]\w*)\(([^)]*)\)\)", input)

    if class_input is not None:
        return True
    return False

#Solution 2)
def do_first_step_with_object_input(bc: Bytecode):
    """This function manually goes through first step, given object as an input"""
    mid, not_relevant_minput = jpamb.getcase()
    minput = re.search(r"\(new\s+([A-Za-z_]\w*)\(([^)]*)\)\)", sys.argv[2])

    initial_frame = Frame.from_method(mid)
    heap = {}
    state = State(heap, Stack.empty().push(initial_frame))

    #logger.debug(bc.methods) we can also add things to the bytecode, but idk how to do it

    #or manually execute the instructions
        # 000 | new jpamb/cases/CustomClasses$PositiveInteger
        # 001 | dup 1
        # 002 | load:I 0 or 002 | push:I 1000
        # 003 | invoke special jpamb/cases/CustomClasses$PositiveInteger.<init>:(I)V
        # 004 | store:A 1
    step_class = Step_class()
    step_class.update_state(state)

    calling_class = sys.argv[1]
    input_class = minput.group(1)
    class_constructor_input_str = minput.group(2)

    def get_class_path(input_string: str, class_name: str) -> str:
        class_path = input_string.split(':')[0]
        path_parts = class_path.rsplit('.', 1)[0]
        return f"{path_parts.replace('.', '/')}${class_name}"

    classname_str = get_class_path(calling_class, input_class)
    classname = jvm.ClassName.decode(classname_str)

    step_class._new(classname)
    step_class.update_frame()
    step_class._dup()
    step_class.update_frame()


    assert re.search(r"-?\d+", class_constructor_input_str), "Class constructor input is not an integer!!!"
    class_constructor_input = jvm.Value.decode(class_constructor_input_str)
    step_class._push(class_constructor_input)
    step_class.update_frame()

    full_classname_str = classname_str + "<init>:(I)V"
    #full_classname = jvm.AbsMethodID.decode(full_classname_str)        #issues here
    #step_class._invoke_special(full_classname, False)
    #an now it stop working since we cannot really predict what is gonna be in the class constructor....

    logger.debug(f"Op Stack[{step_class.frame.stack}]")
    logger.debug(f"Op heap[{step_class.state.heap}]")
    

    return state


if __name__ == "__main__":
    configure_logger()

    bc = Bytecode(jpamb.Suite(), {})
    
    #Solution 2)
    # if input_is_an_object():
    #     state = do_first_step_with_object_input(bc)
    # else:

    #Solution 1) - parsing inside getcase()
    mid, minput = jpamb.getcase()
    initial_frame, heap = generate_initial_frame(mid, minput)
    state = State(heap, Stack.empty().push(initial_frame))

    for x in range(100000):
        state = step(state, bc)
        if isinstance(state, str):
            print(state)
            break
    else:
        print("*")

    # state = step(state, bc)
    # while isinstance(state, str):
    #     print(state)
    #     state = step(state, bc)
