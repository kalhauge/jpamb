import itertools
import random
import sys

import jpamb
import jvm
import jvm.state as jvmc


def to_u16(v: int) -> int: # chars
    return v & 0xFFFF

def to_i16(v: int) -> int:
    v = v & 0xFFFF
    if v >= 2**15:
        v = v - 2**16
    return v

def to_i32(v: int) -> int:
    """
    Java and python have different integer arithmetic.
    Ints in java are 32-bit signed integers, so what would happen if we
    add 1 to 2**31 - 1 = 2.147.483.647? 
    
    Hint: recall computer systems
    
    a) I (Bastian) will show up for every single lecture... FOREVER
    b) 2.147.483.648
    c) -2.147.483.648
    
    Python does not have this behaviour, so we need to simulate it :)
    """
    v = v & 0xFFFFFFFF
    if v >= 2**31:
        v = v - 2**32
    return v

def xor(b1: bool, b2: bool) -> bool:
    return b1 != b2
    
def java_div(v1: int, v2: int) -> int:
    q = abs(v1) // abs(v2)
    if xor((v1 < 0), (v2 < 0)):
        q = -q
    return q

def java_rem(v1: int, v2: int) -> int:
    return v1 - java_div(v1, v2) * v2

def binary(op, v1: int, v2: int) -> int | str:
    match op:
        case jvm.BinaryOpr.Add:
            return to_i32(v1 + v2)
        case jvm.BinaryOpr.Sub:
            return to_i32(v1 - v2)
        case jvm.BinaryOpr.Mul:
            return to_i32(v1 * v2)
        case jvm.BinaryOpr.Div:
            if v2 == 0:
                return "divide by zero"
            return to_i32(java_div(v1, v2))
        case jvm.BinaryOpr.Rem:
            if v2 == 0:
                return "divide by zero"
            return to_i32(java_rem(v1, v2))
        case _:
            raise AssertionError(f"Unknown comparison operator {op!r}, CmpOpr only has 5 members")

def compare(op, v1: int, v2: int) -> bool:
    match op:
        case jvm.CmpOpr.Eq:
            return v1 == v2
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
        case _:
            raise AssertionError(f"Unknown comparison operator {op!r}, CmpOpr only has 6 members")

def step(bc: jpamb.Bytecode, state: jvmc.State) -> tuple[jvmc.PC, jvmc.State | str]:
    assert isinstance(state, jvmc.State), f"expected state but got {state}"
    frame = state.frames.peek()
    pc = frame.pc
    opr = bc[pc]
    output = state
    print(f"Stepping {pc}:\n > {opr}", file=sys.stderr)
    match opr:
        case jvm.Push(type=t, value=v):
            match t:
                case jvm.Int():
                    frame.stack.push(jvmc.StackInt(v))
                case jvm.Reference():
                    frame.stack.push(jvmc.StackReference(0))
                case jvm.Object():
                    ref = state.heap.new(jvmc.HeapString(v))
                    frame.stack.push(ref)
                case _:
                    raise NotImplementedError(f"Don't know how to push {t}")
            frame.pc += 1

        case jvm.Binary(type=jvm.Int(), operant=op):
            v2, v1 = frame.stack.pop(), frame.stack.pop()
            assert isinstance(v1, jvmc.StackInt), f"expected int, but got {v1}"
            assert isinstance(v2, jvmc.StackInt), f"expected int, but got {v2}"

            value = binary(op, v1.value, v2.value)

            if isinstance(value, str):
                output = value
            else:
                frame.stack.push(jvmc.StackInt(value))
                frame.pc += 1

        case jvm.Return(type=t):
            if t is None:
                value = None
            else:
                value = frame.stack.pop()

            state.frames.pop()

            if state.frames:
                caller = state.frames.peek()
                if value is not None:
                    caller.stack.push(value)
                caller.pc += 1
            else:
                output = "ok"

        case jvm.Get(static=True, field=field):
            # Hack - Only handle the assertion case
            assert field.extension.name == "$assertionsDisabled"

            # Hack - Assuming assertions are never disabled
            frame.stack.push(jvmc.StackInt(0))
            frame.pc += 1

        case jvm.New(classname=jvm.ClassName("java.lang.AssertionError")):
            # Hack -- if we create an assertion error, we probably also throw it.
            output = "assertion error"

        case jvm.Load(type=t, index=n):
            v = frame.locals[n]
            frame.stack.push(v)
            frame.pc += 1

        case jvm.Store(type=t, index=n):
            v = frame.stack.pop()
            frame.locals[n] = v
            frame.pc += 1

        case jvm.Dup(words=1):
            v = frame.stack.pop()
            frame.stack.push(v)
            frame.stack.push(v)
            frame.pc += 1

        case jvm.Incr(index=n, amount=amount):
            v = frame.locals[n]
            assert isinstance(v, jvmc.StackInt), f"expected int, but got {v}"
            frame.locals[n] = jvmc.StackInt(to_i32(v.value + amount))
            frame.pc += 1

        case jvm.Negate(type=jvm.Int()):
            v = frame.stack.pop()
            assert isinstance(v, jvmc.StackInt), f"expected int, but got {v}"
            frame.stack.push(jvmc.StackInt(to_i32(-v.value)))
            frame.pc += 1

        case jvm.Goto(target=target):
            frame.pc %= target

        case jvm.Ifz(condition=op, target=target):
            v = frame.stack.pop()
            assert isinstance(v, (jvmc.StackInt, jvmc.StackReference)), f"expected int or ref, but got {v}"
            if compare(op, v.value, 0):
                frame.pc %= target
            else:
                frame.pc += 1

        case jvm.If(condition=op, target=target):
            v2 = frame.stack.pop()
            v1 = frame.stack.pop()
            assert isinstance(v1, (jvmc.StackInt, jvmc.StackReference)), f"expected int or ref, but got {v1}"
            assert isinstance(v2, (jvmc.StackInt, jvmc.StackReference)), f"expected int or ref, but got {v2}"
            if compare(op, v1.value, v2.value):
                frame.pc %= target
            else:
                frame.pc += 1
                
        case jvm.NewArray(type=t, dim=1):
            size = frame.stack.pop()
            assert isinstance(size, jvmc.StackInt), f"expected int, but got {size}"
            values = []
            i = 0
            while i < size.value:
                values.append(0)
                i = i + 1
            ref = state.heap.new(jvmc.HeapArray(t, values))
            frame.stack.push(ref)
            frame.pc += 1

        case jvm.ArrayLength():
            ref = frame.stack.pop()
            assert isinstance(ref, jvmc.StackReference), f"expected ref, but got {ref}"
            if ref.value == 0:
                output = "null pointer"
            else:
                array = state.heap[ref]
                frame.stack.push(jvmc.StackInt(len(array.values)))
                frame.pc += 1

        case jvm.ArrayLoad(type=t):
            index = frame.stack.pop()
            ref = frame.stack.pop()
            assert isinstance(index, jvmc.StackInt), f"expected int, but got {index}"
            assert isinstance(ref, jvmc.StackReference), f"expected ref, but got {ref}"
            if ref.value == 0:
                output = "null pointer"
            else:
                array = state.heap[ref]
                if index.value < 0 or index.value >= len(array.values):
                    output = "out of bounds"
                else:
                    frame.stack.push(jvmc.StackInt(array.values[index.value]))
                    frame.pc += 1

        case jvm.ArrayStore(type=t):
            value = frame.stack.pop()
            index = frame.stack.pop()
            ref = frame.stack.pop()
            assert isinstance(value, jvmc.StackInt), f"expected int, but got {value}"
            assert isinstance(index, jvmc.StackInt), f"expected int, but got {index}"
            assert isinstance(ref, jvmc.StackReference), f"expected ref, but got {ref}"
            if ref.value == 0:
                output = "null pointer"
            else:
                array = state.heap[ref]
                if index.value < 0 or index.value >= len(array.values):
                    output = "out of bounds"
                else:
                    array.values[index.value] = value.value
                    frame.pc += 1
                    
        case jvm.InvokeStatic(method=m):
            callee = jvmc.Frame.from_method(bc.getmethod(m))
            n_args = len(m.extension.params)
            i = n_args - 1
            while i >= 0:
                callee.locals[i] = frame.stack.pop()
                i = i - 1
            state.frames.push(callee)
            
        case jvm.Cast(from_=jvm.Int(), to_=t):
            v = frame.stack.pop()
            assert isinstance(v, jvmc.StackInt), f"expected int, but got {v}"
            match t:
                case jvm.Short():
                    result = to_i16(v.value)
                case jvm.Char():
                    result = to_u16(v.value)
                case _:
                    raise NotImplementedError(f"Don't know how to cast int to {t}")
            frame.stack.push(jvmc.StackInt(result))
            frame.pc += 1
            
        case jvm.InvokeVirtual(method=m):
            is_string_equals = (
                m.classname == jvm.ClassName("java.lang.String")
                and m.extension.name == "equals"
            )
            if not is_string_equals:
                raise NotImplementedError(f"Don't know how to invoke virtual {m}")

            arg = frame.stack.pop()
            receiver = frame.stack.pop()
            assert isinstance(arg, jvmc.StackReference), f"expected ref, but got {arg}"
            assert isinstance(receiver, jvmc.StackReference), f"expected ref, but got {receiver}"

            if receiver.value == 0:
                output = "null pointer"
            else:
                receiver_obj = state.heap[receiver]
                assert isinstance(receiver_obj, jvmc.HeapString), f"expected string, but got {receiver_obj}"

                result = 0
                if arg.value != 0:
                    arg_obj = state.heap[arg]
                    if isinstance(arg_obj, jvmc.HeapString) and receiver_obj.content == arg_obj.content:
                        result = 1

                frame.stack.push(jvmc.StackInt(result))
                frame.pc += 1

        case a:
            raise NotImplementedError(a.help())

    assert isinstance(output, (jvmc.State, str))

    return pc, output


def initial(bc: jpamb.Bytecode, methodid: jvm.AbsMethodID, input: jpamb.Input):
    frame = jvmc.Frame.from_method(bc.getmethod(methodid))
    state = jvmc.State(jvmc.Heap(), jvmc.CallStack.from_frames([frame]))
    for i, v in enumerate(input.values):
        # Convert arbitrary values into local values
        match v:
            case jpamb.case.Boolean(value):
                frame.locals[i] = jvmc.StackInt(1 if value else 0)
            case jpamb.case.Int(value):
                frame.locals[i] = jvmc.StackInt(value)
            case jpamb.case.Array(contains=type, values=values):
                match type:
                    case jvm.Char():
                        ref = state.heap.new(
                            jvmc.HeapArray(type, [ord(a) for a in values])
                        )
                    case jvm.Int():
                        ref = state.heap.new(jvmc.HeapArray(type, [a for a in values]))
                frame.locals[i] = ref
            case jpamb.case.String(value=value):
                ref = state.heap.new(jvmc.HeapString(value))
                frame.locals[i] = ref
            case a:
                raise NotImplementedError(
                    f"Do not know how to convert values of type {a!r} to a local value"
                )

    return state


def interpret():
    """The entry point for the interpreter"""

    methodid, input, max_steps = jpamb.getcase(
        "dynamic",
        "1.0",
        "MeatballMice",
        ["dynamic", "python"],
        for_science=True,
    )

    suite, eff = jpamb.setup()
    bc = jpamb.Bytecode(suite, eff, {})

    state = initial(bc, methodid, input)

    last = jpamb.emit_init(state)

    for x in range(max_steps):
        pc, state = step(bc, state)
        last = jpamb.emit_step(last, pc, state)

        if isinstance(state, str):
            break


NUMBER_OF_RUNS = 100
MAX_ARRAY_LENGTH = 10
MAX_STRING_LENGTH = 10

def random_int(rand: random.Random, ints: list[int]) -> int:
    if ints and rand.choice([True, False]):
        return rand.choice(ints)
    return rand.randint(-(1 << 31), (1 << 31) - 1)

def random_char(rand: random.Random, chars: list[str]) -> str:
    if chars and rand.choice([True, False]):
        return rand.choice(chars)
    return chr(rand.randint(32, 126))

def random_string(rand: random.Random, chars: list[str], strings: list[str]) -> str:
    if strings and rand.choice([True, False]):
        return rand.choice(strings)
    length = rand.randint(0, MAX_STRING_LENGTH)
    return "".join(random_char(rand, chars) for _ in range(length))

def fuzz_input(
    rand: random.Random,
    methodid: jvm.AbsMethodID,
    ints: list[int],
    strings: list[str],
) -> jpamb.case.Input:
    chars = [chr(i) for i in ints if 0 <= i <= 0xFFFF]
    input = []
    # 1. come up with possible inputs
    for p in methodid.extension.params:
        match p:
            case jvm.Int():
                input.append(jpamb.case.Int(random_int(rand, ints)))
            case jvm.Boolean():
                input.append(jpamb.case.Boolean(1 == rand.randint(0, 1)))
            case jvm.Array(contains=jvm.Int()):
                length = rand.randint(0, MAX_ARRAY_LENGTH)
                values = tuple(random_int(rand, ints) for _ in range(length))
                input.append(jpamb.case.Array(jvm.Int(), values))
            case jvm.Array(contains=jvm.Char()):
                length = rand.randint(0, MAX_ARRAY_LENGTH)
                values = tuple(random_char(rand, chars) for _ in range(length))
                input.append(jpamb.case.Array(jvm.Char(), values))
            case jvm.Object(name=jvm.ClassName("java.lang.String")):
                input.append(jpamb.case.String(random_string(rand, chars, strings)))
            case a:
                raise NotImplementedError(
                    f"Don't know how to create random values for {a}"
                )

    return jpamb.case.Input(input)

MAX_DEPTH = 3
SMALL_SCOPE_BUDGET = 200

def gen_int(depth: int):
    yield 0
    for i in range(depth):
        yield (i + 1)
        yield -(i + 1)

def gen_char(depth: int):
    for i in range(depth):
        yield chr(ord("a") + i)

def gen_sequences(elements: list, depth: int):
    """All sequences of length 0..depth over elements"""
    for length in range(depth + 1):
        yield from itertools.product(elements, repeat=length)

def gen_value(p: jvm.Type, depth: int) -> list[jpamb.case.Value]:
    match p:
        case jvm.Int():
            return [jpamb.case.Int(i) for i in gen_int(depth)]
        case jvm.Boolean():
            return [jpamb.case.Boolean(False), jpamb.case.Boolean(True)]
        case jvm.Array(contains=jvm.Int()):
            ints = list(gen_int(depth))
            return [jpamb.case.Array(jvm.Int(), s) for s in gen_sequences(ints, depth)]
        case jvm.Array(contains=jvm.Char()):
            chars = list(gen_char(depth))
            return [jpamb.case.Array(jvm.Char(), s) for s in gen_sequences(chars, depth)]
        case jvm.Object(name=jvm.ClassName("java.lang.String")):
            chars = list(gen_char(depth))
            return [jpamb.case.String("".join(s)) for s in gen_sequences(chars, depth)]
        case a:
            raise NotImplementedError(
                f"Don't know how to create small values for {a}"
            )

def small_scope_inputs(methodid: jvm.AbsMethodID, max_depth: int, budget: int):
    """Iterative deepening over all small inputs, skipping ones already tried"""
    seen = set()
    for depth in range(1, max_depth + 1):
        values_per_param = [gen_value(p, depth) for p in methodid.extension.params]
        for values in itertools.product(*values_per_param):
            input = jpamb.case.Input(tuple(values))
            if input in seen:
                continue
            if len(seen) >= budget:
                return
            seen.add(input)
            yield input

def analyse():
    from dynamic_helper import (
        select_trace,
        analyse_traces,
        syntactically_all_ints_in_class,
        syntactically_all_strings_in_class,
    )
    """The dynamic analysis, e.g. in this case a (dumb) fuzzer."""

    methodid = jpamb.getmethodid(
        "dynamic",
        "1.0",
        "MeatballMice",
        ["dynamic", "python", "random", "dictionary", "syntactic", "smallcheck"],
        for_science=True,
    )

    suite, eff = jpamb.setup()
    bc = jpamb.Bytecode(suite, eff, {})

    MAX_STEPS = 200

    import random

    # Make the randomness deterministic
    rand = random.Random(0)

    number_of_params = len(methodid.extension.params)
    ints = syntactically_all_ints_in_class(suite, eff, methodid.classname)
    strings = syntactically_all_strings_in_class(suite, eff, methodid.classname)

    inputs = list(small_scope_inputs(methodid, MAX_DEPTH, SMALL_SCOPE_BUDGET))
    if number_of_params > 0:
        for i in range(NUMBER_OF_RUNS):
            inputs.append(fuzz_input(rand, methodid, ints, strings))

    traces = []
    for input in inputs:
        trace = select_trace(bc, methodid, input, MAX_STEPS)
        traces.append(trace)

    answers = analyse_traces(traces, number_of_params)
    for query in jpamb.QUERIES:
        print(f"{query};{answers[query]}")
