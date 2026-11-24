import syntaxAnalyser
import os
import random
import sys
import time
from dataclasses import dataclass

import jpamb
import jvm
import jvm.state as jvmc

# Print every interpreted instruction to stderr. Only useful for debugging the
# interpreter; the fuzzer runs thousands of executions, so it is off by default.
TRACE = os.environ.get("FUZZ_TRACE") == "1"


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
    if TRACE:
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


def run_with_coverage(
    bc: jpamb.Bytecode, state: jvmc.State, max_steps: int
) -> tuple[jvmc.State | str, frozenset[jvmc.PC]]:
    """Run an input and return its outcome and the bytecode locations it executed."""
    coverage: set[jvmc.PC] = set()
    for _ in range(max_steps):
        pc, state = step(bc, state)
        coverage.add(pc)
        if isinstance(state, str):
            break

    return state, frozenset(coverage)


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
    global TRACE
    TRACE = True

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


# Coverage guided fuzzing (similar to AFL)
# - coverage = edges (prev pc -> pc) + bucketed hit count per edge
# - inputs that hit new coverage go into the corpus, the rest is dropped
# - new inputs = mutated corpus entries, ints can also come from the
#   constant dictionary (syntaxAnalyser)
#
# FUZZ_MODE:
#   random   - no feedback, fresh random input every time
#   coverage - coverage guided, no dictionary
#   full     - coverage guided + dictionary (default)

INT_MIN, INT_MAX = -(1 << 31), (1 << 31) - 1
MAX_STEPS = 3000

Coverage = frozenset  # frozenset of coverage features


def to_int32(v: int) -> int:
    """Wrap an arbitrary python int into a signed 32 bit integer."""
    return (v - INT_MIN) % (1 << 32) + INT_MIN


def hit_bucket(count: int) -> int:
    """AFL style hit count buckets: 1, 2, 3, 4-7, 8-15, 16-31, 32-127, 128+."""
    if count <= 3:
        return count
    for bucket, limit in enumerate((8, 16, 32, 128), start=4):
        if count < limit:
            return bucket
    return 8


def execute(
    bc: jpamb.Bytecode, state: jvmc.State, max_steps: int
) -> tuple[str | None, Coverage]:
    """Runs one input and returns (outcome, coverage).
    outcome is "*" if max_steps ran out, None if the interpreter crashed."""
    hits: dict[tuple, int] = {}
    prev = None
    outcome: str | None = "*"
    try:
        for _ in range(max_steps):
            pc, state = step(bc, state)
            edge = (prev, pc)
            hits[edge] = hits.get(edge, 0) + 1
            prev = pc
            if isinstance(state, str):
                outcome = state
                break
    except Exception as e:  # interpreter does not support everything yet
        if TRACE:
            print(f"interpreter failed: {e!r}", file=sys.stderr)
        outcome = None

    features = {(edge, hit_bucket(n)) for edge, n in hits.items()}
    # new outcome also counts as new coverage
    features.add(("outcome", outcome))
    return outcome, frozenset(features)


@dataclass
class Seed:
    values: tuple
    coverage: Coverage
    picks: int = 0


class CoverageFuzzer:
    """Coverage-guided mutational fuzzer for a single JVM method."""

    def __init__(
        self,
        bc: jpamb.Bytecode,
        methodid: jvm.AbsMethodID,
        rand: random.Random,
        int_dict: list[int] | None = None,
        str_dict: list[str] | None = None,
        use_coverage: bool = True,
        max_steps: int = MAX_STEPS,
    ):
        self.bc = bc
        self.methodid = methodid
        self.params = list(methodid.extension.params)
        self.rand = rand
        self.int_dict = sorted(int_dict or [])
        self.str_dict = sorted(str_dict or [])
        self.use_coverage = use_coverage
        self.max_steps = max_steps

        self.corpus: list[Seed] = []
        self.global_coverage: set = set()
        # outcome -> first input that caused it (for test synthesis)
        self.witnesses: dict[str, tuple] = {}
        self.execs = 0
        self.crashes = 0

    # input generation

    def random_int(self) -> int:
        r = self.rand.random()
        if self.int_dict and r < 0.3:
            return self.rand.choice(self.int_dict)
        if r < 0.65:
            return self.rand.randint(-128, 128)
        return self.rand.randint(INT_MIN, INT_MAX)

    def random_char(self) -> str:
        if self.rand.random() < 0.8:
            return chr(self.rand.randint(32, 126))  # printable ascii
        return chr(self.rand.randint(0, 255))

    def random_string(self) -> str:
        if self.str_dict and self.rand.random() < 0.3:
            return self.rand.choice(self.str_dict)
        return "".join(self.random_char() for _ in range(self.rand.randint(0, 10)))

    def random_value(self, p: jvm.Type):
        match p:
            case jvm.Int():
                return self.random_int()
            case jvm.Boolean():
                return self.rand.random() < 0.5
            case jvm.Array(contains=jvm.Int()):
                return tuple(self.random_int() for _ in range(self.rand.randint(0, 10)))
            case jvm.Array(contains=jvm.Char()):
                if self.str_dict and self.rand.random() < 0.3:
                    return tuple(self.rand.choice(self.str_dict))
                return tuple(self.random_char() for _ in range(self.rand.randint(0, 10)))
            case jvm.Object(name=jvm.ClassName("java.lang.String")):
                return self.random_string()
            case _:
                raise NotImplementedError(f"Don't know how to fuzz values of {p!r}")

    def random_input(self) -> tuple:
        return tuple(self.random_value(p) for p in self.params)

    # mutation

    def mutate_int(self, v: int) -> int:
        choice = self.rand.randrange(6 if self.int_dict else 5)
        match choice:
            case 0:  # small arithmetic step
                return to_int32(v + self.rand.choice((-1, 1)) * self.rand.randint(1, 35))
            case 1:  # flip one bit
                return to_int32(v ^ (1 << self.rand.randrange(32)))
            case 2:  # negate
                return to_int32(-v)
            case 3:  # scale
                return to_int32(v * 2 if self.rand.random() < 0.5 else v // 2)
            case 4:  # fresh value
                return self.random_int()
            case _:  # value from the constant dictionary
                return self.rand.choice(self.int_dict)

    def mutate_seq(self, seq: tuple, new_elem, mutate_elem) -> tuple:
        seq = list(seq)
        choice = self.rand.randrange(5)
        if choice == 0 or not seq:  # insert
            seq.insert(self.rand.randint(0, len(seq)), new_elem())
        elif choice == 1:  # delete
            del seq[self.rand.randrange(len(seq))]
        elif choice == 2:  # mutate one element
            i = self.rand.randrange(len(seq))
            seq[i] = mutate_elem(seq[i])
        elif choice == 3:  # truncate
            seq = seq[: self.rand.randint(0, len(seq))]
        else:  # duplicate a slice
            i = self.rand.randrange(len(seq))
            seq[i:i] = seq[i : self.rand.randint(i, len(seq))]
        return tuple(seq[:64])

    def mutate_char(self, c: str) -> str:
        if self.rand.random() < 0.5:
            return chr(max(0, min(0xFFFF, ord(c) + self.rand.choice((-1, 1)))))
        return self.random_char()

    def mutate_value(self, p: jvm.Type, v):
        match p:
            case jvm.Int():
                return self.mutate_int(v)
            case jvm.Boolean():
                return not v
            case jvm.Array(contains=jvm.Int()):
                return self.mutate_seq(v, self.random_int, self.mutate_int)
            case jvm.Array(contains=jvm.Char()):
                if self.str_dict and self.rand.random() < 0.2:
                    return tuple(self.rand.choice(self.str_dict))
                return self.mutate_seq(v, self.random_char, self.mutate_char)
            case jvm.Object(name=jvm.ClassName("java.lang.String")):
                if self.str_dict and self.rand.random() < 0.2:
                    return self.rand.choice(self.str_dict)
                return "".join(self.mutate_seq(tuple(v), self.random_char, self.mutate_char))
            case _:
                return self.random_value(p)

    def mutate(self, values: tuple) -> tuple:
        values = list(values)
        # apply 1, 2 or 4 mutations to random parameters
        for _ in range(1 << self.rand.randrange(3)):
            i = self.rand.randrange(len(values))
            values[i] = self.mutate_value(self.params[i], values[i])
        return tuple(values)

    # execution

    def to_input(self, values: tuple) -> jpamb.case.Input:
        out = []
        for p, v in zip(self.params, values):
            match p:
                case jvm.Int():
                    out.append(jpamb.case.Int(v))
                case jvm.Boolean():
                    out.append(jpamb.case.Boolean(v))
                case jvm.Array(contains=t):
                    out.append(jpamb.case.Array(contains=t, values=tuple(v)))
                case jvm.Object(name=jvm.ClassName("java.lang.String")):
                    out.append(jpamb.case.String(v))
        return jpamb.case.Input(tuple(out))

    def run_one(self, values: tuple) -> tuple[str | None, Coverage]:
        self.execs += 1
        try:
            state = initial(self.bc, self.methodid, self.to_input(values))
        except Exception:
            self.crashes += 1
            return None, frozenset()
        outcome, cov = execute(self.bc, state, self.max_steps)
        if outcome is None:
            self.crashes += 1
        elif outcome not in self.witnesses:
            self.witnesses[outcome] = values
        return outcome, cov

    def consider(self, values: tuple) -> bool:
        """Execute values and keep them in the corpus if they add coverage."""
        outcome, cov = self.run_one(values)
        if not self.use_coverage or outcome is None:
            return False
        if cov - self.global_coverage:
            self.global_coverage |= cov
            self.corpus.append(Seed(values, cov))
            return True
        return False

    def choose_seed(self) -> Seed:
        # prefer seeds that were picked less often
        weights = [1.0 / (1 + s.picks) for s in self.corpus]
        seed = self.rand.choices(self.corpus, weights=weights)[0]
        seed.picks += 1
        return seed

    def run(self, time_budget: float, max_execs: int) -> set[str]:
        """Fuzz until the time or execution budget is used up."""
        deadline = time.monotonic() + time_budget

        if not self.params:
            # no parameters, so one run is enough
            self.run_one(())
            return set(self.witnesses)

        for _ in range(8):  # initial random seeds
            self.consider(self.random_input())

        while self.execs < max_execs and time.monotonic() < deadline:
            if not self.use_coverage or not self.corpus or self.rand.random() < 0.05:
                self.consider(self.random_input())
                continue
            seed = self.choose_seed()
            for _ in range(16):
                self.consider(self.mutate(seed.values))

        return set(self.witnesses)


def analyse():
    """Coverage-guided fuzzer used as a JPAMB analysis."""

    methodid = jpamb.getmethodid(
        "project_fuzz",
        "1.0",
        "Group 16",
        ["dynamic", "fuzzing", "coverage", "python"],
        for_science=True,
    )

    suite, eff = jpamb.setup()
    bc = jpamb.Bytecode(suite, eff, {})

    mode = os.environ.get("FUZZ_MODE", "full")
    seed = int(os.environ.get("FUZZ_SEED", "0"))
    budget = float(os.environ.get("FUZZ_BUDGET", "2.0"))
    max_execs = int(os.environ.get("FUZZ_MAX_EXECS", "100000"))

    int_dict: list[int] = []
    if mode == "full":
        try:
            constants = syntaxAnalyser.getDictFromMethodIdTS(methodid)
            int_dict = sorted(syntaxAnalyser.augmentWithBoundryValues(constants))
        except BaseException as e:  # syntaxAnalyser calls sys.exit on failure
            print(f"constant extraction failed: {e!r}", file=sys.stderr)

    fuzzer = CoverageFuzzer(
        bc,
        methodid,
        random.Random(seed),
        int_dict=int_dict,
        use_coverage=mode != "random",
    )

    try:
        behaviors = fuzzer.run(budget, max_execs)
    except NotImplementedError as e:
        print(f"cannot fuzz {methodid}: {e}", file=sys.stderr)
        behaviors = set()

    print(
        f"mode={mode} execs={fuzzer.execs} corpus={len(fuzzer.corpus)} "
        f"coverage={len(fuzzer.global_coverage)} crashes={fuzzer.crashes} "
        f"found={sorted(behaviors)}",
        file=sys.stderr,
    )
    for outcome, values in fuzzer.witnesses.items():
        print(f"witness {outcome!r}: {fuzzer.to_input(values)}", file=sys.stderr)

    deterministic = not fuzzer.params and fuzzer.crashes == 0
    for query in jpamb.QUERIES:
        if query == "*" and query in behaviors:
            # hitting MAX_STEPS does not prove an infinite loop
            # (e.g. fib(21) or collatz also hit it), so own category
            print(f"{query};timeout")
        elif query in behaviors:
            print(f"{query};found")
        elif deterministic:
            # no parameters -> the single run is the only behaviour
            print(f"{query};no")
        else:
            print(f"{query};not-found")


