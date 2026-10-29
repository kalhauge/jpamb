import random
import re
import sys

import jpamb
import jvm
import jvm.state as jvmc


def to_int32(value: int) -> int:
    """
    Convert a Python integer to a signed Java 32-bit integer.
    """
    return (value + (1 << 31)) % (1 << 32) - (1 << 31)


def java_division(v1: int, v2: int) -> int:
    """
    Java integer division truncates toward zero.
    """
    quotient = abs(v1) // abs(v2)

    if (v1 < 0) != (v2 < 0):
        quotient = -quotient

    return to_int32(quotient)


def binary(op, v1: int, v2: int) -> int | str:
    match op:
        case jvm.BinaryOpr.Div:
            if v2 == 0:
                return "divide by zero"
            return java_division(v1, v2)

        case jvm.BinaryOpr.Rem:
            if v2 == 0:
                return "divide by zero"
            quotient = java_division(v1, v2)
            return to_int32(v1 - quotient * v2)

        case jvm.BinaryOpr.Add:
            return to_int32(v1 + v2)

        case jvm.BinaryOpr.Sub:
            return to_int32(v1 - v2)

        case jvm.BinaryOpr.Mul:
            return to_int32(v1 * v2)

        case _:
            raise NotImplementedError(f"Unhandled binary operation {op!r}")


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

        case jvm.CmpOpr.Is:
            return v1 is v2

        case _:
            raise NotImplementedError(f"Unhandled comparison {op!r}")

def bootstrap_args(bc: jpamb.Bytecode, cn: jvm.ClassName, index: int) -> list[dict]:
    """Get the static arguments of a bootstrap method of a class.

    An invokedynamic opcode only stores the index of its bootstrap method;
    the arguments (e.g. the recipe of makeConcatWithConstants) are stored
    in the class, so the caller must know which class the opcode is in.
    """
    for bsm in bc.suite.findclass(cn, eff=bc.eff).get("bootstrapmethods", []):
        if bsm["index"] == index:
            return bsm["method"]["args"]
    raise IndexError(f"Could not find bootstrap method {index} in {cn}")

def java_to_string(heap: jvmc.Heap, type_: jvm.Type, value: jvmc.StackValue) -> str:
    """Convert a stack value to text, as Java's String.valueOf does."""
    match type_:
        case jvm.Boolean():
            return "true" if value.value else "false"
        case jvm.Char():
            return chr(value.value)
        case jvm.Int() | jvm.Short() | jvm.Byte():
            return str(value.value)
        case jvm.Object(name=jvm.ClassName("java.lang.String")):
            if value.value == 0:
                return "null"
            string = heap[value]
            assert isinstance(string, jvmc.HeapString), f"expected string, but got {string}"
            return string.content
        case _:
            raise NotImplementedError(f"Cannot convert {type_} to a string")

def string_split(string: str, regex: str, limit: int = 0) -> list[str]:
    """Split like Java's String.split: the separator is a regex, and the
    limit decides how many parts to make and whether to keep trailing "".

    Simple regexes behave the same in Python and Java; capturing groups do not.
    """
    if limit == 1:
        return [string]
    # Python's maxsplit=0 means "no limit", like Java's limit <= 0
    parts = re.split(regex, string, maxsplit=max(limit - 1, 0))
    if limit == 0 and len(parts) > 1:
        while parts and parts[-1] == "":
            parts.pop()
    return parts


def string_char_at(string: str, index: int) -> int:
    # Python accepts negative indexes, Java does not
    if not 0 <= index < len(string):
        raise IndexError(index)
    return ord(string[index])


# The String methods we can execute, with the Python code that computes them
STRING_METHODS = {
    "equals": lambda s, other: s == other,
    "equalsIgnoreCase": lambda s, other: other is not None and s.lower() == other.lower(),
    "startsWith": lambda s, prefix: s.startswith(prefix),
    "endsWith": lambda s, suffix: s.endswith(suffix),
    "contains": lambda s, part: part in s,
    "isEmpty": lambda s: s == "",
    "length": lambda s: len(s),
    "charAt": string_char_at,
    "split": string_split,
}

# Methods that accept a null argument instead of throwing NullPointerException
NULL_SAFE_STRING_METHODS = {"equals", "equalsIgnoreCase"}

# Exactly the format Java accepts: Python's int() would also accept spaces,
# underscores ("1_0") and non-ASCII digits
INT_PATTERN = re.compile(r"[+-]?[0-9]+")


def integer_parse_int(string: str | None) -> int:
    """Parse like Java's Integer.parseInt; ValueError is NumberFormatException."""
    if string is None or not INT_PATTERN.fullmatch(string):
        raise ValueError(f"For input string: {string!r}")
    value = int(string)
    if not -(2**31) <= value < 2**31:
        raise ValueError(f"For input string: {string!r}")
    return value

STATIC_METHODS = {
    (jvm.ClassName("java.lang.Integer"), "parseInt"): integer_parse_int,
}

# Methods invoked with invoke special (like constructors of library classes)
SPECIAL_METHODS = {
    (jvm.ClassName("java.lang.Object"), "<init>"): lambda this: None,
    (jvm.ClassName("java.lang.IllegalArgumentException"), "<init>"): lambda this, msg: None,
}

def from_stack(heap: jvmc.Heap, value: jvmc.StackValue):
    """Turn a stack value into a Python value: strings become str, null None."""
    if isinstance(value, jvmc.StackReference):
        if value.value == 0:
            return None
        obj = heap[value]
        return obj.content if isinstance(obj, jvmc.HeapString) else obj
    return value.value


def to_stack(heap: jvmc.Heap, type_: jvm.Type, value) -> jvmc.StackValue:
    """Turn a Python result into a stack value of the given JVM type."""
    match type_:
        case jvm.Boolean():
            return jvmc.StackInt(1 if value else 0)
        case jvm.Int() | jvm.Char():
            return jvmc.StackInt(value)
        case jvm.Object(name=jvm.ClassName("java.lang.String")):
            return heap.new(jvmc.HeapString(value))
        case jvm.Array(contains=jvm.Object(name=jvm.ClassName("java.lang.String")) as t):
            refs = [heap.new(jvmc.HeapString(s)).value for s in value]
            return heap.new(jvmc.HeapArray(t, refs))
        case _:
            raise NotImplementedError(f"Cannot return a value of type {type_}")

def step(bc: jpamb.Bytecode, state: jvmc.State) -> tuple[jvmc.PC, jvmc.State | str]:
    assert isinstance(state, jvmc.State), f"expected state but got {state}"
    frame = state.frames.peek()
    pc = frame.pc
    opr = bc[pc]
    output = state
    print(f"Stepping {pc}:\n > {opr}", file=sys.stderr)
    match opr:
        case jvm.Dup():
            v1 = frame.stack.pop()
            frame.stack.push(v1)
            frame.stack.push(v1)
            frame.pc += 1

        case jvm.Ifz(condition=c, target=t):
            assert isinstance(
                c, jvm.CmpOpr
            ), f"expected comparison op, but got {type(c)}"
            assert isinstance(t, int), f"expected int, but got {type(t)}"

            v1 = frame.stack.pop()
            assert isinstance(v1, jvmc.StackInt) or isinstance(
                v1, jvmc.StackReference
            ), f"expected int or reference, but got {v1}"
            result = compare(c, v1.value, 0)

            if isinstance(result, str):
                output = result
            else:
                frame.pc = pc % t if result else frame.pc + 1

        case jvm.Load(type=t, index=n):
            v = frame.locals[n]
            frame.stack.push(v)
            frame.pc += 1

        case jvm.ArrayLoad(type=t):
            index, arr_ref = frame.stack.pop(), frame.stack.pop()
            if arr_ref.value == 0:
                output = "null pointer"
            else:
                arr = state.heap[arr_ref]
                if index.value < 0 or index.value >= len(arr.values):
                    output = "out of bounds"
                else:
                    arr = state.heap[arr_ref]

                    val = arr.values[index.value]
                    # Arrays of objects store heap addresses, not numbers
                    if isinstance(t, jvm.Reference):
                        frame.stack.push(jvmc.StackReference(val))
                    else:
                        frame.stack.push(jvmc.StackInt(val))

                    frame.pc += 1

        case jvm.Incr(index=i, amount=a):
            current_val = frame.locals[i].value
            new_val = to_int32(current_val + a)
            frame.locals[i] = jvmc.StackInt(new_val)
            frame.pc += 1

        case jvm.Goto(target=t):
            frame.pc = frame.pc % t

        case jvm.Push(type=t, value=v):
            if isinstance(t, jvm.Int):
                frame.stack.push(jvmc.StackInt(v))

            elif isinstance(t, jvm.Float):
                frame.stack.push(jvmc.StackFloat(v))

            elif isinstance(t, jvm.Object) and t.name == jvm.ClassName(
                "java.lang.String"
            ):
                # Create the string in the JVM heap
                ref = state.heap.new(jvmc.HeapString(v))
                # Push its reference onto the operand stack
                frame.stack.push(ref)
            elif isinstance(t, jvm.Reference):
                frame.stack.push(jvmc.StackReference(v))
            else:
                raise NotImplementedError(f"Push type {t} not supported!")
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
            # Retrieve the return value, if the method has one
            val = None
            if t is not None:
                val = frame.stack.pop()
            # Remove the frame of the method that just finished
            state.frames.pop()
            # Is there a caller waiting for this method?
            if state.frames:
                caller = state.frames.peek()
                # Pass the return value back to the caller
                if val is not None:
                    caller.stack.push(val)
                # Continue after the invocation instruction
                caller.pc += 1
            else:
                # No frames remain: the entire program finished
                output = "ok"

        case jvm.Get(static=True, field=field):
            # Hack - Only handle the assertion case
            assert field.extension.name == "$assertionsDisabled"

            # Hack - Assuming assertions are never disabled
            frame.stack.push(jvmc.StackInt(0))
            frame.pc += 1

        case jvm.If(condition=c, target=t):
            val2, val1 = frame.stack.pop(), frame.stack.pop()
            result = compare(c, val1.value, val2.value)

            if isinstance(result, str):
                output = result
            else:
                frame.pc = pc % t if result else frame.pc + 1

        case jvm.NewArray(type=t, dim=d):
            size = frame.stack.pop()
            if size.value < 0:
                output = "negative array size"
            else:
                initial_values = [0] * size.value
                arr = jvmc.HeapArray(contains=t, values=initial_values)
                ref = state.heap.new(arr)
                frame.stack.push(ref)
                frame.pc += 1

        case jvm.New(classname=jvm.ClassName("java.lang.AssertionError")):
            # Hack -- if we create an assertion error, we probably also throw it.
            output = "assertion error"

        case jvm.New(classname=c):
            obj = jvmc.HeapObject(classname=c, fields={})
            ref = state.heap.new(obj)
            frame.stack.push(ref)
            frame.pc += 1

        case jvm.ArrayStore(type=t):
            val, index, ref = frame.stack.pop(), frame.stack.pop(), frame.stack.pop()

            if ref.value == 0:
                output = "null pointer"
            else:
                arr = state.heap[ref]
                if index.value < 0 or index.value >= len(arr.values):
                    output = "out of bounds"
                else:
                    arr.values[index.value] = val.value
                    frame.pc += 1

        case jvm.Store(type=t, index=i):
            val = frame.stack.pop()
            frame.locals.locals[i] = val
            frame.pc += 1

        case jvm.ArrayLength():
            arr_ref = frame.stack.pop()

            if arr_ref.value == 0:
                output = "null pointer"
            else:
                arr = state.heap[arr_ref]

                length_value = len(arr.values)
                frame.stack.push(jvmc.StackInt(length_value))

                frame.pc += 1

        case jvm.InvokeVirtual(method=m) if m.classname == jvm.ClassName("java.lang.Class") and m.extension.name == "newInstance":
            class_ref = frame.stack.pop()
            class_obj = state.heap[class_ref]
            target_class_name = class_obj.fields["target_class"]
            
            target_class = jvm.ClassName(target_class_name)  
                      
            new_instance = jvmc.HeapObject(classname=target_class, fields={})
            ref = state.heap.new(new_instance)
            
            frame.stack.push(ref)
            frame.pc += 1
            
            init_methodid = jvm.AbsMethodID(
                classname=target_class,
                extension=jvm.MethodID(
                    name="<init>",
                    params=jvm.Parameters(()),
                    return_type=None
                )
            )
            
            loc = [ref] + [None] * 14
            
            new_pc = jvmc.PC(init_methodid, 0)
            new_locals = jvmc.Locals(loc)
            new_stack = jvmc.OperandStack([])
            new_frame = jvmc.Frame(new_locals, new_stack, new_pc)
            
            state.frames = state.frames.push(new_frame)

        case jvm.InvokeVirtual(method=m) if m.classname == jvm.ClassName(
            "java.lang.String"
        ):
            name = m.extension.name
            if name not in STRING_METHODS:
                raise NotImplementedError(f"String.{name} is not supported")

            # Pop the arguments (the last one is on top), then the receiver
            args = [frame.stack.pop() for _ in m.extension.params][::-1]
            this = frame.stack.pop()
            values = [from_stack(state.heap, v) for v in args]

            if this.value == 0 or (name not in NULL_SAFE_STRING_METHODS and None in values):
                output = "null pointer"
            else:
                try:
                    result = STRING_METHODS[name](state.heap[this].content, *values)
                except IndexError:
                    output = "out of bounds"
                else:
                    frame.stack.push(to_stack(state.heap, m.extension.return_type, result))
                    frame.pc += 1

        case jvm.InvokeVirtual(method=m):
            # General InvokeVirtual handling (simplified)
            len_params = len(m.methodid.params)
            
            args = []
            for _ in range(len_params):
                args.insert(0, frame.stack.pop())
            
            this_ref = frame.stack.pop()

            loc = [this_ref] + args
            loc = loc + [None] * (15 - len(loc))

            new_pc = jvmc.PC(m, 0)
            new_locals = jvmc.Locals(loc)
            new_stack = jvmc.OperandStack([])
            new_frame = jvmc.Frame(new_locals, new_stack, new_pc)
            
            state.frames = state.frames.push(new_frame)

        case jvm.InvokeStatic(method=m) if m.classname == jvm.ClassName("java.lang.Class") and m.extension.name == "forName":
            name_ref = frame.stack.pop()
            class_name = state.heap[name_ref].content
            
            class_obj = jvmc.HeapObject(classname=jvm.ClassName("java.lang.Class"), fields={"target_class": class_name})
            ref = state.heap.new(class_obj)
            
            frame.stack.push(ref)
            frame.pc += 1

        case jvm.InvokeStatic(method=m) if (
            m.classname,
            m.extension.name,
        ) in STATIC_METHODS:
            args = [frame.stack.pop() for _ in m.extension.params][::-1]
            values = [from_stack(state.heap, v) for v in args]
            try:
                result = STATIC_METHODS[(m.classname, m.extension.name)](*values)
            except ValueError as e:
                # A Java exception that is not one of the JPAMB outcomes
                raise NotImplementedError(f"Exceptions are not supported yet: {e}") from e
            frame.stack.push(to_stack(state.heap, m.extension.return_type, result))
            frame.pc += 1

        case jvm.InvokeStatic(method=m):
            assert (isinstance(m, jvm.AbsMethodID), f"expected method id but got {m}")
            len_params = len(m.methodid.params)

            print(f"param length: {len_params}", file=sys.stderr)
            args = []
            for _ in range(len_params):
                args.insert(0, frame.stack.pop())

            loc = args + [None] * (15 - len(args))

            new_pc = jvmc.PC(m, 0)
            new_locals = jvmc.Locals(loc)
            new_stack = jvmc.OperandStack([])
            new_frame = jvmc.Frame(new_locals, new_stack, new_pc)
            state.frames = state.frames.push(new_frame)

        case jvm.InvokeSpecial(method=m) if (m.classname, m.extension.name) in SPECIAL_METHODS:
            args = [frame.stack.pop() for _ in m.extension.params][::-1]
            
            this_ref = frame.stack.pop()
            
            SPECIAL_METHODS[(m.classname, m.extension.name)](this_ref, *args)
            
            frame.pc += 1

        case jvm.InvokeSpecial(method=m):
            len_params = len(m.methodid.params)
            
            args = []
            for _ in range(len_params):
                args.insert(0, frame.stack.pop())
            
            this_ref = frame.stack.pop()

            loc = [this_ref] + args
            loc = loc + [None] * (15 - len(loc))

            new_pc = jvmc.PC(m, 0)
            new_locals = jvmc.Locals(loc)
            new_stack = jvmc.OperandStack([])
            new_frame = jvmc.Frame(new_locals, new_stack, new_pc)
            
            state.frames = state.frames.push(new_frame)

        case jvm.InvokeDynamic(index=i, method=m) if (
            m.extension.name == "makeConcatWithConstants"
        ):
            # The recipe has one \u0001 for each dynamic argument and one
            # \u0002 for each extra constant of the bootstrap method
            recipe, *constants = bootstrap_args(bc, pc.method.classname, i)
            params = list(m.extension.params)
            # The last argument is on top of the stack
            args = [frame.stack.pop() for _ in params][::-1]
            parts = iter(java_to_string(state.heap, t, v) for t, v in zip(params, args))
            extra = iter(c["value"] for c in constants)

            result = ""
            for char in recipe["value"]:
                if char == "\u0001":
                    result += next(parts)
                elif char == "\u0002":
                    result += str(next(extra))
                else:
                    result += char

            frame.stack.push(state.heap.new(jvmc.HeapString(result)))
            frame.pc += 1

        case jvm.Cast(from_=jvm.Int(), to_=jvm.Short()):
            # Pop the integer from the operand stack
            value = frame.stack.pop()
            # Convert to a signed 16-bit Java short
            short_value = (value.value + (1 << 15)) % (1 << 16) - (1 << 15)
            # JVM stores short results as integer stack values
            frame.stack.push(jvmc.StackInt(short_value))
            frame.pc += 1

        case jvm.CheckCast(type=t):
            ref = frame.stack.pop()
            frame.stack.push(ref)
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
        "bests analyzers",
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


INTERESTING_INTS = [
    0,
    1,
    -1,
    2,
    -2,
    3,
    -3,
    5,
    -5,
    10,
    -10,
    42,
    -42,
    100,
    -100,
    # Large constant and neighboring values
    10054202,
    10054203,
    10054204,
    -10054202,
    -10054203,
    -10054204,
    # Java integer boundaries
    2147483647,
    -2147483648,
]


# ============================================================
# NEW: DICTIONARY ANALYSIS
# Finds integer and string const used in the method.
# ============================================================
def collect_dictionary(bc, methodid):

    int_dictionary = []
    string_dictionary = []

    method = bc.getmethod(methodid)

    # Look through the bytecode instructions
    for opr in method.opcodes:

        match opr:

            # Integer const
            case jvm.Push(type=jvm.Int(), value=value):
                if value not in int_dictionary:
                    int_dictionary.append(value)

            # String const
            case jvm.Push(type=t, value=value) if isinstance(
                t, jvm.Object
            ) and t.name == jvm.ClassName("java.lang.String"):
                if value not in string_dictionary:
                    string_dictionary.append(value)

            case _:
                pass

    return int_dictionary, string_dictionary


def fuzz_input(
    rand: random.Random,
    methodid: jvm.AbsMethodID,
    trial: int = 0,
    int_dictionary=None,
    string_dictionary=None,
) -> jpamb.case.Input:

    if int_dictionary is None:
        int_dictionary = []

    if string_dictionary is None:
        string_dictionary = []

    int_values = INTERESTING_INTS.copy()

    for value in int_dictionary:
        if value not in int_values:
            int_values.append(value)

    values = []

    for position, param in enumerate(methodid.extension.params):

        match param:

            # -----------------------------
            # INT -
            # -----------------------------
            case jvm.Int():
                if trial < 80:
                    index = (trial // (len(int_values) ** position)) % len(int_values)

                    value = int_values[index]

                else:
                    value = rand.randint(-(1 << 31), (1 << 31) - 1)

                values.append(jpamb.case.Int(value))

            # -----------------------------
            # BOOLEAN -
            # -----------------------------
            case jvm.Boolean():

                value = bool((trial // (2**position)) % 2)

                values.append(jpamb.case.Boolean(value))

            # -----------------------------
            # STRING -
            # -----------------------------
            case jvm.Object(name=classname) if classname == jvm.ClassName(
                "java.lang.String"
            ):

                interesting_strings = [
                    "",
                    "hello",
                    "not hello",
                    "Hello",
                    "x",
                    "a",
                    "test",
                    "null",
                    "hello world",
                ]
                for string in string_dictionary:
                    if string not in interesting_strings:
                        interesting_strings.append(string)
                if trial < 80:
                    value = interesting_strings[trial % len(interesting_strings)]

                else:
                    length = rand.randint(0, 10)

                    value = "".join(
                        rand.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(length)
                    )

                values.append(jpamb.case.String(value))

            # =============================================
            # NEW: SUPPORT INT ARRAYS
            # =============================================
            case jvm.Array(contains=jvm.Int()):

                interesting_arrays = [
                    [],
                    [0],
                    [1],
                    [-1],
                    [0, 0],
                    [1, 2, 3],
                    [-1, 0, 1],
                    [42],
                    [100],
                ]

                if trial < 80:
                    array = interesting_arrays[trial % len(interesting_arrays)]

                else:
                    length = rand.randint(0, 6)

                    array = [rand.choice(int_values) for _ in range(length)]

                values.append(jpamb.case.Array(jvm.Int(), array))

            # =============================================
            # NEW: SUPPORT CHAR ARRAYS
            # =============================================
            case jvm.Array(contains=jvm.Char()):

                interesting_char_arrays = [
                    "",
                    "a",
                    "x",
                    "hello",
                    "Hello",
                    "test",
                ]

                if trial < 80:
                    value = interesting_char_arrays[
                        trial % len(interesting_char_arrays)
                    ]

                else:
                    length = rand.randint(0, 8)

                    value = "".join(
                        rand.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(length)
                    )

                values.append(jpamb.case.Array(jvm.Char(), value))

            case _:
                raise NotImplementedError(f"Unsupported input type: {param!r}")

    return jpamb.case.Input(values)


def gen_int(depth):
    yield 0

    for i in range(depth):
        yield i + 1
        yield -(i + 1)


def analyse():
    """
    Dynamic analysis using systematic and random inputs.
    """

    methodid = jpamb.getmethodid(
        "dynamic",
        "1.0",
        "bests analyzers ",
        [
            "dynamic",
            "python",
            "smallcheck",
            "fuzzing",
            "random",
            "dictionary",
            "syntatic",
        ],
        for_science=True,
    )

    suite, eff = jpamb.setup()

    bc = jpamb.Bytecode(suite, eff, {})

    int_dictionary, string_dictionary = collect_dictionary(bc, methodid)

    # Maximum instructions executed for one input
    MAX_STEPS = 200

    # More steps for SmallCheck because recursive inputs need longer
    SMALLCHECK_STEPS = 2000 
     

    # Number of different inputs to try
    MAX_TESTS = 100

    # Deterministic randomness
    rand = random.Random(0)

    # Store all observed outcomes
    behaviors = set()
    # ============================================================
    # SMALLCHECK
    # Test small integer values first
    # ============================================================

    if len(methodid.extension.params) == 1 and isinstance(
        methodid.extension.params[0], jvm.Int
    ):
        for value in gen_int(8):

            test_input = jpamb.case.Input([jpamb.case.Int(value)])

            state = initial(bc, methodid, test_input)

            for step_number in range(SMALLCHECK_STEPS):

               pc, state = step(bc, state)

               if isinstance(state, str):
                behaviors.add(state)
                break

               if isinstance(bc[pc], jvm.Goto):
                new_pc = state.frames.peek().pc

                if new_pc.offset == pc.offset:
                    behaviors.add("*")
                    break

    # Generate and test different inputs
    for trial in range(MAX_TESTS):

        test_input = fuzz_input(
            rand, methodid, trial, int_dictionary, string_dictionary
        )

        state = initial(bc, methodid, test_input)

        # Run the interpreter on this input
        for step_number in range(MAX_STEPS):
            pc, state = step(bc, state)

            # The program terminated normally or with an error.
            if isinstance(state, str):
                behaviors.add(state)
                break

            # Detect an unconditional jump to itself.
            if isinstance(bc[pc], jvm.Goto):
                new_pc = state.frames.peek().pc
                if new_pc.offset == pc.offset:
                    behaviors.add("*")
                    break
        else:

            if len(methodid.extension.params) == 0:

                behaviors.add("*")

    # Report the behaviors we actually observed
    for query in jpamb.QUERIES:
        if query in behaviors:
            print(f"{query};found")
        else:
            print(f"{query};not-found")