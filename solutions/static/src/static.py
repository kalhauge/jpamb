import sys
from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass, field, replace

from abstractions import BooleanSet, IntegerAbstraction, StringSet
from configuration import DEFAULT_CONFIG, AnalysisConfig, parse_options
from string_methods import AbstractReference
from string_methods import equals as string_equals

import jpamb
import sexpr
from jpamb import jvm
from jvm.state import PC, StackInt


@dataclass(frozen=True)
class State(sexpr.AsSExpr):
    locals: tuple[IntegerAbstraction | BooleanSet | AbstractReference | None, ...]
    stack: tuple[IntegerAbstraction | BooleanSet | AbstractReference, ...]

    # Copy on update: successor states never mutate a predecessor's heap.
    heap: dict[str, StringSet] = field(default_factory=dict)

    def __post_init__(self):
        assert isinstance(self.locals, tuple)
        assert isinstance(self.stack, tuple)

    def __str__(self):
        return f"{', '.join(map(str, self.locals))}/{':'.join(map(str, self.stack))}"

    def __or__(self, other):
        assert isinstance(other, State), f"Expected State but got {other!r}"
        assert len(self.stack) == len(other.stack), "Stacks should be equal lenght"
        assert len(self.locals) == len(other.locals), "Locals should be equal lenght"

        heap = dict(self.heap)
        for target, value in other.heap.items():
            heap[target] = heap.get(target, StringSet.bot()) | value
        return State(
            tuple(join_value(s1, s2) for s1, s2 in zip(self.locals, other.locals)),
            tuple(join_value(s1, s2) for s1, s2 in zip(self.stack, other.stack)),
            heap,
        )

    def push(self, value):
        if not isinstance(value, (IntegerAbstraction, BooleanSet, AbstractReference)):
            raise NotImplementedError(f"Unsupported stack value: {value}")
        return replace(self, stack=self.stack + (value,))

    def pop(self, number=1):
        return self.stack[-number:], replace(self, stack=self.stack[:-number])

    def load(self, index):
        value = self.locals[index]
        if value is None:
            raise NotImplementedError("Read of an uninitialized local")
        return value

    def store(self, index, value):
        return State(
            tuple(self.locals[:index]) + (value,) + tuple(self.locals[index + 1 :]),
            self.stack,
            self.heap,
        )

    def string_reference(self, target, value, nullable=False):
        """Return a reference and a state containing its abstract contents."""
        heap = dict(self.heap)
        heap[target] = heap.get(target, StringSet.bot()) | value
        return AbstractReference(frozenset({target}), nullable), replace(
            self, heap=heap
        )


def join_value(left, right):
    # None denotes an uninitialized local, not a Java null reference. If either
    # path leaves a slot uninitialized it cannot safely be loaded after the join.
    if left is None or right is None:
        return None
    if type(left) is not type(right):
        raise NotImplementedError("Joining incompatible local/stack types")
    return left | right


# Handle one instruction and produce possible next states or final outcomes.
# Division such as 10 / n can report division by zero and also
# continue with the possible result signs {-, 0, +} kept together in one state.
# A later condition can create two paths. Currently their variable signs stay
# the same, but their next instruction positions differ. The worklist follows
# these paths through later calls to this function.
def manystep(
    bc: jpamb.Bytecode,
    pc: PC,
    state: State,
    config: AnalysisConfig = DEFAULT_CONFIG,
) -> Iterable[tuple[PC, object] | str]:
    integer_domain = config.integer_domain
    opr = bc[pc]
    match opr:
        case jvm.Push(type=jvm.Int(), value=value):
            abstract_value = config.scalar([StackInt(value)])
            yield (pc + 1, state.push(abstract_value))

        case jvm.Push(type=jvm.Object(cn), value=text) if cn == jvm.ClassName(
            "java.lang.String"
        ):
            if not config.strings:
                raise NotImplementedError("Enable --abstractions string or sign,string")
            reference, after = state.string_reference(
                "literal:" + text, StringSet.abstract([text])
            )
            yield (pc + 1, after.push(reference))

        case jvm.Push(type=jvm.Reference(), value=0):
            if not config.strings:
                raise NotImplementedError("Reference support requires string mode")
            yield (pc + 1, state.push(AbstractReference(frozenset(), True)))

        case jvm.InvokeVirtual(method=method):
            if not config.strings or method != jpamb.parse_methodid(
                "java.lang.String.equals:(Ljava/lang/Object;)Z"
            ):
                raise NotImplementedError(f"Unsupported call: {method}")
            [receiver, argument], after = state.pop(2)
            answers, errors = string_equals(receiver, argument, state.heap)
            yield from errors
            if answers:
                result = config.scalar(StackInt(int(a)) for a in answers)
                yield (pc + 1, after.push(result))

        case jvm.Get(static=True, field=field):
            # Hack - Only handle the assertion case
            if field.extension.name != "$assertionsDisabled":
                raise NotImplementedError(f"Unsupported field: {field}")

            # Hack - Assuming assertions are never disabled
            va = config.scalar([StackInt(0)])

            yield (pc + 1, state.push(va))

        case jvm.Ifz(condition=op, target=target):
            [val], after = state.pop(1)

            zero = (
                AbstractReference(frozenset(), True)
                if isinstance(val, AbstractReference)
                else config.scalar([StackInt(0)])
            )
            for res in val.compare(zero, op):
                match res:
                    case True:
                        yield (pc % target, after)
                    case False:
                        yield (pc + 1, after)
                    case err:
                        yield err

        case jvm.Load(index=i):
            va = state.load(i)
            yield (pc + 1, state.push(va))

        case jvm.Store(type=jvm.Int() | jvm.Reference(), index=index):
            [value], after = state.pop(1)
            yield (pc + 1, after.store(index, value))

        case jvm.If(condition=operation, target=target):
            [left, right], after = state.pop(2)
            for answer in left.compare(right, operation):
                if answer:
                    yield (pc % target, after)
                else:
                    yield (pc + 1, after)

        case jvm.Incr(index=index, amount=amount):
            config.require_integers()
            increment = config.scalar([StackInt(amount)])
            result, _errors = state.load(index).arithmetic(increment, jvm.BinaryOpr.Add)
            yield (pc + 1, state.store(index, result))

        case jvm.Negate(type=jvm.Int()):
            config.require_integers()
            [value], after = state.pop(1)
            zero = config.scalar([StackInt(0)])
            result, _errors = zero.arithmetic(value, jvm.BinaryOpr.Sub)
            yield (pc + 1, after.push(result))

        case jvm.Goto(target=t):
            yield (pc % t, state)

        case jvm.Binary(type=jvm.Int(), operant=operation):
            config.require_integers()
            operands, after = state.pop(2)
            left, right = operands
            result, errors = left.arithmetic(right, operation)

            yield from errors

            if result != integer_domain.bot():
                yield (pc + 1, after.push(result))

        case jvm.Return(type=None):
            yield "ok"

        case jvm.Return(type=t):
            # Hack -- we assume that we always return.
            yield "ok"

        case jvm.New(classname=jvm.ClassName("java.lang.AssertionError")):
            # Hack -- if we create an assertion error, we probably also throw it.
            yield "assertion error"

        case unsupported:
            raise NotImplementedError(f"Unsupported instruction: {unsupported}")


def initialstate(
    bc: jpamb.Bytecode,
    methodid: jvm.AbsMethodID,
    inputs: jpamb.Input | None,
    config: AnalysisConfig = DEFAULT_CONFIG,
) -> dict[PC, State]:
    integer_domain = config.integer_domain
    method = bc.getmethod(methodid)
    state = State((None,) * method.max_locals, ())
    parameters = methodid.extension.params
    if inputs is not None and len(inputs.values) != len(parameters):
        raise NotImplementedError("Input count does not match method parameters")

    for i, parameter in enumerate(parameters):
        supplied = None if inputs is None else inputs.values[i]
        if isinstance(parameter, (jvm.Int, jvm.Boolean)):
            if isinstance(parameter, jvm.Int):
                config.require_integers()
            if inputs is None:
                value = (
                    config.scalar([StackInt(0), StackInt(1)])
                    if isinstance(parameter, jvm.Boolean)
                    else integer_domain.top()
                )
            elif isinstance(supplied, (jpamb.case.Int, jpamb.case.Boolean)):
                value = config.scalar([StackInt(int(supplied.value))])
            else:
                raise NotImplementedError(f"Unsupported input: {supplied}")
        elif (
            parameter == jvm.Object(jvm.ClassName("java.lang.String"))
            and config.strings
        ):
            if inputs is None:
                contents = StringSet.top()
            elif isinstance(supplied, jpamb.case.String):
                contents = StringSet.abstract([supplied.value])
            else:
                raise NotImplementedError(f"Unsupported string input: {supplied}")
            value, state = state.string_reference(
                f"parameter:{i}", contents, nullable=inputs is None
            )
        else:
            raise NotImplementedError(f"Unsupported parameter type: {parameter}")
        state = state.store(i, value)

    return {PC(methodid, 0): state}


@dataclass
class AbstractInterpreter:
    bc: jpamb.Bytecode
    worklist: deque[PC]
    states: dict[PC, State]
    config: AnalysisConfig = DEFAULT_CONFIG

    @staticmethod
    def initial(
        bc: jpamb.Bytecode, methodid: jvm.AbsMethodID, inputs, config=DEFAULT_CONFIG
    ):
        states = initialstate(bc, methodid, inputs, config)
        worklist = deque(states.keys())

        return AbstractInterpreter(bc, worklist, states, config)

    def step(self) -> tuple[PC, set[str]]:  # Processing one instruction
        pc = self.worklist.pop()

        print(f"Stepping {pc}:\n > {self.bc[pc]}", file=sys.stderr)

        finals = set()

        for res in manystep(self.bc, pc, self.states[pc], self.config):
            if isinstance(res, str):
                finals.add(res)
            else:
                pc_, st = res

                before = self.states.get(pc_, None)
                if before is None:
                    after = st
                else:
                    after = before | st
                if before is None or after != before:
                    self.states[pc_] = after
                    self.worklist.append(pc_)

        return pc, finals


def interpret():
    """Use the original JPAMB protocol after consuming our own options."""
    config, arguments = parse_options(sys.argv[1:])
    sys.argv = [sys.argv[0], *arguments]
    methodid, input, steps = jpamb.getcase(
        "static",
        "1.0",
        "Los Pollos Hermanos",
        config.tags,
        for_science=True,
    )
    suite, eff = jpamb.setup()
    bc = jpamb.Bytecode(suite, eff, {})

    ai = AbstractInterpreter.initial(bc, methodid, input, config)

    x = jpamb.emit_init(ai.states)

    while steps > 0 and ai.worklist:
        pc, final = ai.step()
        for f in final:
            jpamb.emit_step(x, pc, f, depth=1)
            steps -= 1

        x = jpamb.emit_step(x, pc, ai.states, depth=1)
        steps -= 1


def analyse():
    """Use the original JPAMB protocol after consuming our own options."""
    config, arguments = parse_options(sys.argv[1:])
    sys.argv = [sys.argv[0], *arguments]

    methodid = jpamb.getmethodid(
        "static",
        "1.0",
        "Los Pollos Hermanos",
        config.tags,
        for_science=True,
    )

    suite, eff = jpamb.setup()
    bc = jpamb.Bytecode(suite, eff, {})

    steps = 300

    final = set()
    incomplete = False

    try:
        ai = AbstractInterpreter.initial(bc, methodid, None, config)
        while steps > 0 and ai.worklist:
            _pc, finals = ai.step()
            final |= finals
            steps -= 1
        incomplete = bool(ai.worklist)
    except NotImplementedError as error:
        print(error, file=sys.stderr)
        incomplete = True

    for outcome in jpamb.QUERIES:
        if outcome in final:
            prediction = "maybe"
        elif incomplete or outcome == "*":
            # Sign analysis alone does not establish termination.
            prediction = "unknown"
        else:
            prediction = "no"
        print(f"{outcome};{prediction}")
