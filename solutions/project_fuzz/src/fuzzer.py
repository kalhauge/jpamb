import syntaxAnalyser
import random
import sys

import jpamb
import jvm
import jvm.state as jvmc


def binary(op, v1: int, v2: int) -> int | str:
    match op:
        case jvm.BinaryOpr.Div:
            try:
                return v1 // v2
            except ZeroDivisionError:
                return "divide by zero"
        case jvm.BinaryOpr.Mul:
            return v1*v2
        case jvm.BinaryOpr.Add:
            return v1+v2
        case jvm.BinaryOpr.Sub:
            return v1-v2
        case jvm.BinaryOpr.Rem:
            if (v2!=0):
                return v1 % v2
            else:
                raise ValueError("Division by zero")
        
        case a:
            raise NotImplementedError(f"Unhandled binary {op!r}")


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
            raise NotImplementedError(f"Unhandled comparation {op!r}")


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
                    frame.pc += 1
                case jvm.Char():
                    frame.stack.push(jvmc.StackInt(ord(v)))
                    frame.pc += 1
                case jvm.Boolean():
                    frame.stack.push(jvmc.StackInt(1 if v else 0))
                    frame.pc += 1
                case jvm.Reference():
                    frame.stack.push(jvmc.StackReference(v))
                    frame.pc += 1
                #hardcoded for strings
                case jvm.Object(name=jvm.ClassName("java.lang.String")):
                    assert isinstance(v, str), f"expected string, but got {v!r}"
                    reference = state.heap.new(jvmc.HeapString(v))
                    frame.stack.push(reference)
                    frame.pc += 1
                case jvm.Object():
                    frame.stack.push(jvmc.StackReference(v))
                    frame.pc += 1
                case a:
                    raise NotImplementedError(f"Unhandled push type {t!r}")

            

        case jvm.Load(type=jvm.Int(), index=i):
            v = frame.locals[i]
            frame.stack.push(v)
            frame.pc += 1

        case jvm.Ifz(condition=op, target=target):
            value = frame.stack.pop()
            assert isinstance(value, jvmc.StackInt), f"expected int, but got {value}"

            if compare(op, value.value, 0):
                frame.pc %= target
            else:
                frame.pc += 1

        case jvm.If(condition=op, target=target):
            v2, v1 = frame.stack.pop(), frame.stack.pop()
            assert isinstance(v1, jvmc.StackInt), f"expected int, but got {value}"
            assert isinstance(v2, jvmc.StackInt), f"expected int, but got {value}"

            if compare(op, v1.value, v2.value):
                frame.pc %= target
            else:
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
            match t:
                case jvm.Int():
                    v1 = frame.stack.pop()
                    state.frames.pop()
                    if state.frames:
                        frame = state.frames.peek()
                        frame.stack.push(v1)
                        frame.pc += 1
                    else:
                        output = "ok"
                case None:
                    state.frames.pop()
                    if state.frames:
                        frame = state.frames.peek()
                        frame.pc += 1
                    else:
                        output = "ok"
                case a:
                    raise NotImplementedError(f"Unhandled return type {t!r}")

        case jvm.Get(static=True, field=field):
            # Hack - Only handle the assertion case
            assert field.extension.name == "$assertionsDisabled"

            # Hack - Assuming assertions are never disabled
            frame.stack.push(jvmc.StackInt(0))
            frame.pc += 1

        case jvm.New(classname=jvm.ClassName("java.lang.AssertionError")):
            # Hack -- if we create an assertion error, we probably also throw it.
            output = "assertion error"

        case jvm.NewArray( type=t, dim=d):
            #count is popped off the operand stack. it represents the number of elements in the array to be created
            count = frame.stack.pop()
            assert isinstance(count, jvmc.StackInt), f"expected int, but got {count!r}"
            match t:
                case jvm.Int():
                    ref = state.heap.new(jvmc.HeapArray(t, [0] * count.value))
                    frame.stack.push(ref)
                    frame.pc += 1
                case jvm.Boolean():
                    ref = state.heap.new(jvmc.HeapArray(t, [0] * count.value))
                    frame.stack.push(ref)
                    frame.pc += 1
                case jvm.Char():
                    ref = state.heap.new(jvmc.HeapArray(t, [0] * count.value))
                    frame.stack.push(ref)
                    frame.pc += 1
                case a:
                    raise NotImplementedError(f"Unhandled array type {t!r}")

        case jvm.Dup():
            value = frame.stack.pop()
            frame.stack.push(value)
            frame.stack.push(value)
            frame.pc += 1

        case jvm.ArrayStore(type=t):
            match t:
                case jvm.Int():
                    value, index, ref = frame.stack.pop(), frame.stack.pop(), frame.stack.pop()
                    assert isinstance(value, jvmc.StackInt), f"expected int, but got {value!r}"
                    assert isinstance(index, jvmc.StackInt), f"expected int, but got {index!r}"

                    try:
                        array = state.heap[ref]
                    except IndexError:
                        output = "null pointer"
                    else:
                        assert isinstance(array, jvmc.HeapArray), f"expected array, but got {array!r}"
                        assert isinstance(array.contains, jvm.Int), f"expected int array, but got {array!r}"

                        try:
                            array.values[index.value] = value.value
                        except IndexError:
                            output = "out of bounds"
                        else:
                            frame.pc += 1

                case a:
                    raise NotImplementedError(f"Unhandled array type {t!r}")

        case jvm.Store(type=t, index=i):
            assert isinstance(i, int), f"expected int, but got {i!r}"
            match t:
                case jvm.Reference():
                    objectref = frame.stack.pop()
                    # must be of type returnAddress or of type reference
                    # assert isinstance(objectref, (jvmc.StackReference)), f"expected return address, but got {objectref!r}"

                    try:
                        frame.locals[i] = objectref
                    except IndexError:
                        output = "null pointer"
                    else:
                        frame.pc += 1
                case jvm.Int():
                    objectref = frame.stack.pop()
                    # must be of type returnAddress or of type reference
                    #assert isinstance(objectref, (jvmc.StackReference)), f"expected return address, but got {objectref!r}"

                    try:
                        frame.locals[i] = objectref
                    except IndexError:
                        output = "null pointer"
                    else:
                        frame.pc += 1
                case a:
                    raise NotImplementedError(f"Unhandled store type {t!r}")

        case jvm.ArrayLoad(type=t):
            match t:
                case jvm.Int():
                    index, ref = frame.stack.pop(), frame.stack.pop()
                    assert isinstance(index, jvmc.StackInt), f"expected int, but got {index!r}"
                    try:
                        array = state.heap[ref]
                    except IndexError:
                        output = "null pointer"
                    else:
                        assert isinstance(array, jvmc.HeapArray), f"expected array, but got {array!r}"

                        try:
                            value = array.values[index.value]
                        except IndexError:
                            output = "out of bounds"
                        else:
                            frame.stack.push(jvmc.StackInt(value))
                            frame.pc += 1
                case jvm.Char():
                    index, ref = frame.stack.pop(), frame.stack.pop()
                    assert isinstance(index, jvmc.StackInt), f"expected int, but got {index!r}"
                    try:
                        array = state.heap[ref]
                    except IndexError:
                        output = "null pointer"
                    else:
                        assert isinstance(array, jvmc.HeapArray), f"expected array, but got {array!r}"

                        try:
                            value = array.values[index.value]
                        except IndexError:
                            output = "out of bounds"
                        else:
                            frame.stack.push(jvmc.StackInt(value))
                            frame.pc += 1

                case a:
                    raise NotImplementedError(f"Unhandled array type {t!r}")

        case jvm.Load(type=t, index=i):
            assert isinstance(i, int), f"expected int, but got {i!r}"
            match t:
                case jvm.Reference():

                    try:
                        objectref = frame.locals[i]
                    except IndexError:
                        output = "null pointer"
                    else:
                        frame.stack.push(objectref)
                        frame.pc += 1
                case jvm.Int():
                    try:
                        objectref = frame.locals[i]
                    except IndexError:
                        output = "null pointer"
                    else:
                        frame.stack.push(objectref)
                        frame.pc += 1
                case a:
                    raise NotImplementedError(f"Unhandled store type {t!r}")

        case jvm.ArrayLength():
            ref = frame.stack.pop()
            assert isinstance(ref, jvmc.StackReference), f"expected reference, but got {ref!r}"

            try:
                array = state.heap[ref]
            except IndexError:
                output = "null pointer"
            else:
                assert isinstance(array, jvmc.HeapArray), f"expected array, but got {array!r}"

                frame.stack.push(jvmc.StackInt(len(array.values)))
                frame.pc += 1

        case jvm.Incr(index=i, amount=a):
            # The value const is first sign-extended to an int, and then the local variable at index is incremented by that amount.
            assert isinstance(i, int), f"expected int, but got {i!r}"
            assert isinstance(a, int), f"expected int, but got {a!r}"
            try:
                frame.locals[i] = jvmc.StackInt(frame.locals[i].value + a)
            except IndexError:
                output = "out of bounds"
            else:
                frame.pc += 1

        case jvm.Goto(target=target):
            frame.pc = frame.pc % target

        case jvm.InvokeStatic(method=methodid):
            method = bc.getmethod(methodid)
            callee = jvmc.Frame.from_method(method)
            for index in reversed(range(len(methodid.extension.params))):
                callee.locals[index] = frame.stack.pop()
            state.frames.push(callee)

        # hardcoded for strings
        case jvm.InvokeVirtual(method=methodid):
            if (
                methodid.classname == jvm.ClassName("java.lang.String")
                and methodid.extension.name == "equals"
            ):
                argument = frame.stack.pop()
                receiver = frame.stack.pop()
                assert isinstance(argument, jvmc.StackReference), (
                    f"expected reference argument, but got {argument!r}"
                )
                assert isinstance(receiver, jvmc.StackReference), (
                    f"expected string receiver, but got {receiver!r}"
                )

                try:
                    receiver_string = state.heap[receiver]
                except IndexError:
                    output = "null pointer"
                else:
                    assert isinstance(receiver_string, jvmc.HeapString)
                    if argument.value == 0:
                        equal = False
                    else:
                        argument_string = state.heap[argument]
                        equal = (
                            isinstance(argument_string, jvmc.HeapString)
                            and receiver_string.content == argument_string.content
                        )
                    frame.stack.push(jvmc.StackInt(int(equal)))
                    frame.pc += 1
            else:
                method = bc.getmethod(methodid)
                callee = jvmc.Frame.from_method(method)
                for index in reversed(range(len(methodid.extension.params))):
                    callee.locals[index + 1] = frame.stack.pop()
                callee.locals[0] = frame.stack.pop()
                state.frames.push(callee)

        case jvm.InvokeSpecial(method=methodid):
            method = bc.getmethod(methodid)
            callee = jvmc.Frame.from_method(method)
            for index in reversed(range(len(methodid.extension.params))):
                callee.locals[index] = frame.stack.pop()
            state.frames.push(callee)

        # It is popped from the operand stack, truncated to a short, then sign-extended to an int result.
        case jvm.Cast(from_= jvm.Int(), to_= jvm.Short()):
            value = frame.stack.pop()
            assert isinstance(value, jvmc.StackInt), f"expected jvm.Int but got {value!r}"
            truncated = value.value & 0xFFFF
            frame.stack.push(jvmc.StackInt(truncated))
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
        "Stephen Walking",
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


def fuzz_input(rand: random.Random, methodid: jvm.AbsMethodID, specialValues: list[int]) -> jpamb.case.Input:
    input = []
    # 1. come up with possible inputs
    for p in methodid.extension.params:
        match p:
            case jvm.Int():
                if rand.randint(0,1):
                    input.append(jpamb.case.Int(rand.randint(-(1 << 31), 1 << 31)))
                else:
                    input.append(jpamb.case.Int(specialValues[rand.randint(0, len(specialValues)-1)]))
            case jvm.Boolean():
                input.append(jpamb.case.Boolean(1 == rand.randint(0, 1)))
            case jvm.Array():
                match p.contains:
                    case jvm.Int():
                        input.append(
                            jpamb.case.Array(
                                contains=jvm.Int(),
                                values=[
                                    rand.randint(-(1 << 31), 1 << 31)
                                    for _ in range(rand.randint(0, 10))
                                ],
                            )
                        )
                    case jvm.Char():
                        input.append(
                            jpamb.case.Array(
                                contains=jvm.Char(),
                                values=[
                                    chr(rand.randint(0, 255))
                                    for _ in range(rand.randint(0, 10))
                                ],
                            )
                        )
            case jvm.Object(name=jvm.ClassName("java.lang.String")):
                input.append(
                    jpamb.case.String(
                        value="".join(
                            chr(rand.randint(0, 255)) for _ in range(rand.randint(0, 10))
                        )
                    )
                )
                
            case a:
                raise NotImplementedError(
                    "Don't know how to create random values for {input}"
                )

    return jpamb.case.Input(input)


def analyse():
    """The dynamic analysis, e.g. in this case a (dumb) fuzzer."""

    methodid = jpamb.getmethodid(
        "dynamic",
        "1.0",
        "Stephen Walking",
        ["dynamic", "python"],
        for_science=True,
    )

    suite, eff = jpamb.setup()
    bc = jpamb.Bytecode(suite, eff, {})

    intConstants = syntaxAnalyser.getDictFromMethodIdTS(methodid)
    intConstantsAndBoundaryValues = syntaxAnalyser.augmentWithBoundryValues(intConstants)

    MAX_STEPS = 200

    import random

    # Make the randomness deterministic
    rand = random.Random(0)

    behaviors = set()
    # Try 10 random inputs
    for i in range(10):
        input = fuzz_input(rand, methodid, list(intConstantsAndBoundaryValues))
        state = initial(bc, methodid, input)

        for x in range(MAX_STEPS):
            _, state = step(bc, state)
            if isinstance(state, str):
                behaviors.add(state)
                break

    for query in jpamb.QUERIES:
        if not input.values:
            print(f"{query};no")
        else:
            print(f"{query};not-found")
        if query in behaviors:
            if query == "*":
                print(f"{query};timeout")
            else:
                print(f"{query};found")
        else:
            print(f"{query};not-found")
