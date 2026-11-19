import argparse
import random
import sys
from itertools import product

import jpamb
import jvm
import jvm.state as jvmc

I32_MIN = -(1 << 31)
I32_MAX = (1 << 31) - 1
INTERESTING_INTS = (0, 1, -1, I32_MIN, I32_MAX)
TEXT_ALPHABET = "abcdefghijklmnopqrstuvwxyz"
MAX_SEQUENCE_LENGTH = 8


class UnsupportedInputType(NotImplementedError):
    """Raised when the random generator cannot represent a JVM parameter."""


def int32(value: int) -> int:
    """JVM integer arithmetic wraps to signed 32 bits."""
    return (value + (1 << 31)) % (1 << 32) - (1 << 31)


def binary(op, v1: int, v2: int) -> int | str:
    match op:
        case jvm.BinaryOpr.Add:
            return int32(v1 + v2)
        case jvm.BinaryOpr.Sub:
            return int32(v1 - v2)
        case jvm.BinaryOpr.Mul:
            return int32(v1 * v2)
        case jvm.BinaryOpr.Div | jvm.BinaryOpr.Rem:
            if v2 == 0:
                return "divide by zero"
            # Java truncates towards zero; Python // rounds down.
            quotient = abs(v1) // abs(v2)
            if (v1 < 0) != (v2 < 0):
                quotient = -quotient
            return int32(quotient if op == jvm.BinaryOpr.Div else v1 - quotient * v2)
        case _:
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
            raise NotImplementedError(f"Unhandled comparison {op!r}")


def step(bc: jpamb.Bytecode, state: jvmc.State) -> tuple[jvmc.PC, jvmc.State | str]:
    """Execute one supported JVM instruction; never guess unsupported semantics."""
    frame = state.frames.peek()
    pc = frame.pc
    opr = bc[pc]
    # Branch and call instructions override this default next instruction.
    frame.pc += 1
    match opr:
        case jvm.Push(type=jvm.Int(), value=value):
            frame.stack.push(jvmc.StackInt(int32(value)))
        case jvm.Push(type=jvm.Reference(), value=0):
            frame.stack.push(jvmc.StackReference(0))
        case jvm.Push(
            type=jvm.Object(name=jvm.ClassName("java.lang.String")), value=value
        ):
            frame.stack.push(state.heap.new(jvmc.HeapString(value)))
        case jvm.Load(index=index):
            frame.stack.push(frame.locals[index])
        case jvm.Store(index=index):
            frame.locals[index] = frame.stack.pop()
        case jvm.Incr(index=index, amount=amount):
            frame.locals[index] = jvmc.StackInt(
                int32(frame.locals[index].value + amount)
            )
        case jvm.Cast(from_=jvm.Int(), to_=target):
            value = frame.stack.pop().value
            if isinstance(target, jvm.Char):
                value &= 0xFFFF
            elif isinstance(target, jvm.Short):
                value = (value + (1 << 15)) % (1 << 16) - (1 << 15)
            elif isinstance(target, jvm.Byte):
                value = (value + (1 << 7)) % (1 << 8) - (1 << 7)
            else:
                raise NotImplementedError(f"Unsupported integer cast: {target}")
            frame.stack.push(jvmc.StackInt(value))
        case jvm.Negate(type=jvm.Int()):
            frame.stack.push(jvmc.StackInt(int32(-frame.stack.pop().value)))
        case jvm.Binary(type=jvm.Int(), operant=op):
            right, left = frame.stack.pop(), frame.stack.pop()
            value = binary(op, left.value, right.value)
            if isinstance(value, str):
                return pc, value
            frame.stack.push(jvmc.StackInt(value))
        case jvm.Ifz(condition=condition, target=target):
            if compare(condition, frame.stack.pop().value, 0):
                frame.pc = pc % target
        case jvm.If(condition=condition, target=target):
            right, left = frame.stack.pop(), frame.stack.pop()
            if compare(condition, left.value, right.value):
                frame.pc = pc % target
        case jvm.Goto(target=target):
            frame.pc = pc % target
        case jvm.Return(type=return_type):
            value = frame.stack.pop() if return_type is not None else None
            state.frames.pop()
            if not state.frames:
                return pc, "ok"
            if value is not None:
                state.frames.peek().stack.push(value)
        case jvm.Get(static=True, field=field) if (
            field.extension.name == "$assertionsDisabled"
        ):
            frame.stack.push(jvmc.StackInt(0))  # JPAMB runs with assertions enabled.
        case jvm.New(classname=jvm.ClassName("java.lang.AssertionError")):
            frame.stack.push(state.heap.new(jvmc.HeapObject(opr.classname, {})))
        case jvm.Dup(words=1):
            value = frame.stack.pop()
            frame.stack.push(value).push(value)
        case jvm.Throw():
            ref = frame.stack.pop()
            if ref.value == 0:
                return pc, "null pointer"
            obj = state.heap[ref]
            if isinstance(obj, jvmc.HeapObject) and obj.classname == jvm.ClassName(
                "java.lang.AssertionError"
            ):
                return pc, "assertion error"
            raise NotImplementedError(f"Unsupported thrown object: {obj!r}")
        case jvm.NewArray(type=element, dim=1) if isinstance(
            element, (jvm.Int, jvm.Char)
        ):
            length = frame.stack.pop().value
            # Allocation failures are outside JPAMB's six outcomes. Do not
            # mislabel them as array bounds failures or attempt unbounded allocation.
            if length < 0 or length > 100_000:
                raise NotImplementedError(
                    f"Unsupported array allocation length: {length}"
                )
            frame.stack.push(state.heap.new(jvmc.HeapArray(element, [0] * length)))
        case jvm.ArrayLength():
            ref = frame.stack.pop()
            if ref.value == 0:
                return pc, "null pointer"
            frame.stack.push(jvmc.StackInt(len(state.heap[ref].values)))
        case jvm.ArrayLoad(type=element) | jvm.ArrayStore(type=element):
            if not isinstance(element, (jvm.Int, jvm.Char)):
                raise NotImplementedError(f"Unsupported array element type: {element}")
            stored = frame.stack.pop() if isinstance(opr, jvm.ArrayStore) else None
            index, ref = frame.stack.pop().value, frame.stack.pop()
            if ref.value == 0:
                return pc, "null pointer"
            array = state.heap[ref]
            if not 0 <= index < len(array.values):
                return pc, "out of bounds"
            if stored is None:
                frame.stack.push(jvmc.StackInt(array.values[index]))
            else:
                array.values[index] = (
                    stored.value & 0xFFFF
                    if isinstance(element, jvm.Char)
                    else int32(stored.value)
                )
        case jvm.InvokeStatic(method=method):
            arguments = [frame.stack.pop() for _ in method.extension.params][::-1]
            # Calls within the suite use the same heap and instruction budget.
            callee = jvmc.Frame.from_method(bc.getmethod(method))
            for index, value in enumerate(arguments):
                callee.locals[index] = value
            state.frames.push(callee)
        case jvm.InvokeSpecial(method=method) if (
            method.classname == jvm.ClassName("java.lang.AssertionError")
            and method.extension.name == "<init>"
        ):
            for _ in method.extension.params:
                frame.stack.pop()
            frame.stack.pop()  # Receiver; constructor has no relevant side effects.
        case jvm.InvokeVirtual(method=method) if (
            method.encode() == "java.lang.String.equals:(Ljava/lang/Object;)Z"
        ):
            other, receiver = frame.stack.pop(), frame.stack.pop()
            if receiver.value == 0:
                return pc, "null pointer"
            content = state.heap[receiver].content
            obj = state.heap[other] if other.value else None
            frame.stack.push(
                jvmc.StackInt(
                    int(isinstance(obj, jvmc.HeapString) and obj.content == content)
                )
            )
        case _:
            raise NotImplementedError(f"Unsupported instruction: {opr!r}")
    return pc, state


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
        "The Rice Theorem Cookers",
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


def fuzz_int(rand: random.Random) -> int:
    """Generate a JVM int, with useful boundary values sampled frequently."""
    if rand.random() < 0.5:
        return rand.choice(INTERESTING_INTS)
    return rand.randint(I32_MIN, I32_MAX)


def fuzz_text(rand: random.Random) -> str:
    """Generate a small string that is safe for JPAMB's input encoding."""
    length = rand.randint(0, MAX_SEQUENCE_LENGTH)
    return "".join(rand.choice(TEXT_ALPHABET) for _ in range(length))


def fuzz_value(rand: random.Random, parameter: jvm.Type) -> jpamb.case.Value:
    """Generate one JPAMB value matching a JVM parameter type."""
    match parameter:
        case jvm.Int():
            return jpamb.case.Int(fuzz_int(rand))
        case jvm.Boolean():
            return jpamb.case.Boolean(rand.choice((False, True)))
        case jvm.Array(contains=jvm.Int()):
            length = rand.randint(0, MAX_SEQUENCE_LENGTH)
            values = tuple(fuzz_int(rand) for _ in range(length))
            return jpamb.case.Array(jvm.Int(), values)
        case jvm.Array(contains=jvm.Char()):
            return jpamb.case.Array(jvm.Char(), tuple(fuzz_text(rand)))
        case jvm.Object(name=jvm.ClassName("java.lang.String")):
            return jpamb.case.String(fuzz_text(rand))
        case unsupported:
            raise UnsupportedInputType(
                f"Don't know how to create a random value for {unsupported!r}"
            )


def fuzz_input(rand: random.Random, methodid: jvm.AbsMethodID) -> jpamb.case.Input:
    """Generate one well-typed random input for a method."""
    values = tuple(fuzz_value(rand, p) for p in methodid.extension.params)
    return jpamb.case.Input(values)


def random_inputs(rand, methodid, trials=10):
    """Supply the requested number of trials used by the random fuzzer."""
    if trials < 0:
        raise ValueError("trials must be zero or greater")

    for _ in range(trials):
        yield fuzz_input(rand, methodid)


def execute_input(bc, methodid, input, max_steps):
    """Execute one input and return its behavior or a bounded timeout."""
    state = initial(bc, methodid, input)

    for _ in range(max_steps):
        _, state = step(bc, state)
        if isinstance(state, str):
            return state

    return "*"


def fuzz_small(rand, methodid, max_depth=3):
    """Try small arguments in order of their largest integer magnitude."""
    if max_depth < 0:
        raise ValueError("max_depth must be zero or greater")

    parameters = methodid.extension.params
    for parameter in parameters:
        if not isinstance(parameter, (jvm.Int, jvm.Boolean)):
            print(
                f"SmallCheck cannot generate parameter type {parameter}",
                file=sys.stderr,
            )
            return

    # Initialize with 0, or with True and False
    integers = [jpamb.case.Int(0)]
    booleans = [jpamb.case.Boolean(False), jpamb.case.Boolean(True)]

    for depth in range(max_depth + 1):
        if depth > 0:
            integers.append(jpamb.case.Int(depth))
            integers.append(jpamb.case.Int(-depth))

        choices_by_parameter = []
        for parameter in parameters:
            if isinstance(parameter, jvm.Int):
                choices_by_parameter.append(integers)  # In the first run, 0 is appended
            else:
                choices_by_parameter.append(
                    booleans
                )  # In the first run, True and False is appended

        # Pick one value per parameter, in method-signature order.
        for arguments in product(*choices_by_parameter):  # Can be (0, False), (0, True)
            # Boolean-only and empty argument lists have depth zero.
            argument_depth = 0
            for argument in arguments:
                if isinstance(argument, jpamb.case.Int):
                    magnitude = abs(argument.value)
                    argument_depth = max(argument_depth, magnitude)

            if argument_depth == depth:
                input_case = jpamb.case.Input(list(arguments))
                yield input_case


def mutate_input(rand, input):
    """Change every argument of an input slightly (one mutation operator each)."""
    wrap = lambda v: (v + (1 << 31)) % (1 << 32) - (1 << 31)  # stay in JVM int range
    mutated = []
    for v in input.values:
        match v:
            case jpamb.case.Int(value):
                new = rand.choice([value + 1, value - 1, -value, 0, value * 2])
                mutated.append(jpamb.case.Int(wrap(new)))
            case jpamb.case.Boolean(value):
                mutated.append(jpamb.case.Boolean(not value))
            case a:
                raise NotImplementedError(f"Don't know how to mutate {a!r}")
    return jpamb.case.Input(mutated)


def fuzz_mutation(rand, methodid, behaviors, budget=30):
    """Mutation-based input selection.

    Start from seed inputs, then repeatedly mutate an input from the corpus.
    An input joins the corpus when running it added a new behaviour to the
    shared `behaviors` set (the caller fills that set after each run).
    """
    parameters = methodid.extension.params
    for parameter in parameters:
        if not isinstance(parameter, (jvm.Int, jvm.Boolean)):
            print(
                f"Mutation cannot generate parameter type {parameter}", file=sys.stderr
            )
            return

    # Seeds: all zeros/False, plus one random input.
    zero = jpamb.case.Input(
        [
            jpamb.case.Int(0) if isinstance(p, jvm.Int) else jpamb.case.Boolean(False)
            for p in parameters
        ]
    )
    corpus = [zero, fuzz_input(rand, methodid)]

    # Phase 1: run the seeds.
    yield from corpus

    if not parameters:  # nothing to mutate
        return

    # Phase 2: mutate inputs picked from the corpus.
    seen = set()
    for _ in range(budget):
        parent = rand.choice(corpus)
        child = mutate_input(rand, parent)
        key = tuple(v.value for v in child.values)
        if key in seen:
            continue  # skip duplicate inputs
        seen.add(key)

        known = len(behaviors)
        yield child  # caller runs it and updates `behaviors`
        if len(behaviors) > known:  # new behaviour -> keep this input
            corpus.append(child)


def parse_options(arguments):
    """Consume fuzzer flags while retaining JPAMB's method/info protocol."""
    parser = argparse.ArgumentParser(
        description="Run selected dynamic fuzzers (default: --random).",
        allow_abbrev=False,
    )
    for name in ("random", "small", "mutation"):
        parser.add_argument(
            f"--{name}", action="store_true", help=f"enable the {name} fuzzer"
        )
    parser.add_argument("method", help="JPAMB method identifier, or info")
    options = parser.parse_args(arguments)
    strategies = tuple(
        name for name in ("random", "small", "mutation") if getattr(options, name)
    ) or ("random",)
    return strategies, [options.method]


def analyse():
    """Run one or more fuzzers selected through command-line flags."""
    strategies, arguments = parse_options(sys.argv[1:])
    sys.argv = [sys.argv[0], *arguments]

    methodid = jpamb.getmethodid(
        "dynamic",
        "1.0",
        "Los Pollos Hermanos",
        ["dynamic", *strategies, "python"],
        for_science=True,
    )

    suite, eff = jpamb.setup()
    bc = jpamb.Bytecode(suite, eff, {})

    MAX_STEPS = 200

    behaviors = set()
    unsupported = set()
    # Fixed order and independent seeds make each generator reproducible even
    # when other strategies are selected. Mutation uses shared outcome feedback.
    for strategy in strategies:
        rand = random.Random(0)
        match strategy:
            case "random":
                inputs = random_inputs(rand, methodid)
            case "small":
                inputs = fuzz_small(rand, methodid)
            case "mutation":
                inputs = fuzz_mutation(rand, methodid, behaviors)
        try:
            for input in inputs:
                try:
                    behaviors.add(execute_input(bc, methodid, input, MAX_STEPS))
                except NotImplementedError as error:
                    message = str(error)
                    if message not in unsupported:
                        print(f"Unsupported execution: {message}", file=sys.stderr)
                        unsupported.add(message)
        except UnsupportedInputType as error:
            # An unsupported strategy must not prevent the others from running.
            print(error, file=sys.stderr)

    for query in jpamb.QUERIES:
        if query in behaviors:
            if query == "*":
                print(f"{query};timeout")
            else:
                print(f"{query};found")
        else:
            print(f"{query};not-found")
