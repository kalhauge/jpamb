import jpamb
from jpamb import jvm
from dataclasses import dataclass, field
import logging
import sys

from typing import Iterable

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PC:
    method: jvm.AbsMethodID
    offset: int

    def __iadd__(self, delta):
        return self + delta

    def __add__(self, delta):
        return PC(self.method, self.offset + delta)

    def with_offset(self, target):
        return PC(self.method, target)

    def __str__(self):
        return f"{self.method}:{self.offset}"


@dataclass
class Bytecode:
    suite: jpamb.Suite
    methods: dict[jvm.AbsMethodID, jvm.Method] = field(default_factory=dict)

    def getmethod(self, methodid: jvm.AbsMethodID) -> jvm.Method:
        try:
            method = self.methods[methodid]
        except KeyError:
            opcodes = list(self.suite.method_opcodes(methodid))
            max_locals = self.suite.method_max_locals(methodid)
            method = jvm.Method(methodid, opcodes, max_locals)
            self.methods[methodid] = method
        return method

    def __getitem__(self, pc: PC) -> jvm.Opcode:
        return self.getmethod(pc.method).opcodes[pc.offset]

    def __contains__(self, pc: PC) -> bool:
        return pc.offset < len(self.getmethod(pc.method).opcodes)


class Stack:
    pass


type Sign = Literal[-1] | Literal[0] | Literal[1]


@dataclass(frozen=True)
class SignSet:
    sign: frozenset[Sign]

    @classmethod
    def bot(cls):
        if not hasattr(cls, "_bot"):
            cls._bot = SignSet(frozenset())
        return cls._bot

    @classmethod
    def top(cls):
        if not hasattr(cls, "_top"):
            cls._top = SignSet(frozenset({-1, 0, 1}))
        return cls._top

    def __or__(self, other):
        assert isinstance(other, SignSet), f"Expected SignSet but got {other!r}"
        return SignSet(self.sign | other.sign)

    def __str__(self):
        return (
            "{"
            + "".join(
                [
                    "-" if -1 in self.sign else "",
                    "0" if 0 in self.sign else "",
                    "+" if +1 in self.sign else "",
                ]
            )
            + "}"
        )

    @classmethod
    def from_singleton(cls, value):
        match value.type:
            case jvm.Int():
                return SignSet(frozenset({(value.value > 0) - (value.value < 0)}))
            case jvm.Boolean():
                return SignSet(frozenset({int(value.value)}))
            case a:
                assert False, f"Unsupported value {value!r}"

    @classmethod
    def abstract(cls, values):
        abstraction = cls.bot()
        for value in values:
            abstraction |= cls.from_singleton(value)
        return abstraction


@dataclass(frozen=True)
class SignAnalysis:
    bc: Bytecode

    @dataclass(frozen=True)
    class State:
        locals: tuple[SignSet]
        stack: tuple[SignSet] | None

        def __str__(self):
            return (
                f"{', '.join(map(str, self.locals))}/{':'.join(map(str, self.stack))}"
            )

        def __or__(self, other):
            assert isinstance(other, SignAnalysis.State), (
                f"Expected SignAnalysis but got {other!r}"
            )

            if self.stack is None:
                return other

            if other.stack is None:
                return self

            assert len(self.stack) == len(other.stack), "Stacks should be equal lenght"
            assert len(self.locals) == len(other.locals), (
                "Locals should be equal lenght"
            )

            return SignAnalysis.State(
                tuple(s1 | s2 for s1, s2 in zip(self.locals, other.locals)),
                tuple(s1 | s2 for s1, s2 in zip(self.stack, other.stack)),
            )

        def push(self, value: SignSet):
            assert isinstance(value, SignSet), f"Expected sign set but got {value}"
            return SignAnalysis.State(self.locals, self.stack + (value,))

        def pop(self, number=1):
            return self.stack[-number:], SignAnalysis.State(
                self.locals, self.stack[:-number]
            )

        def load(self, index):
            return self.locals[index]

        def binary(
            self, opr: jvm.BinaryOpr, v1: SignSet, v2: SignSet
        ) -> Iterable[tuple[bool, "SignAnalysis"]]:
            assert isinstance(v1, SignSet), f"Expected sign set but got {v1}"
            assert isinstance(v2, SignSet), f"Expected sign set but got {v2}"
            match opr:
                case jvm.BinaryOpr.Div:
                    divides_by_zero = False
                    signs = set()
                    for x in v1.sign:
                        for y in v2.sign:
                            if y == 0:
                                divides_by_zero = True
                                continue
                            signs.add(x / y)
                    yield (SignSet(frozenset(signs)), self)
                    if divides_by_zero:
                        yield "divide by zero"
                case jvm.BinaryOpr.Sub:
                    signs = set()
                    for x in v1.sign:
                        for y in v2.sign:
                            if y == 0:
                                divides_by_zero = True
                                continue
                            signs.add(x - y)
                    yield (SignSet(frozenset(signs)), self)
                case jvm.BinaryOpr.Add:
                    signs = set()
                    for x in v1.sign:
                        for y in v2.sign:
                            if y == 0:
                                divides_by_zero = True
                                continue
                            signs.add(x + y)
                    yield (SignSet(frozenset(signs)), self)
                case jvm.BinaryOpr.Mul:
                    signs = set()
                    for x in v1.sign:
                        for y in v2.sign:
                            if y == 0:
                                divides_by_zero = True
                                continue
                            signs.add(x * y)
                    yield (SignSet(frozenset(signs)), self)
                case a:
                    raise NotImplementedError(f"The binary operator {a!r}")

        def compare(
            self, opr: jvm.CmpOpr, v1: SignSet, v2: SignSet
        ) -> Iterable[tuple[bool, "SignAnalysis"]]:
            assert isinstance(v1, SignSet), f"Expected sign set but got {v1}"
            assert isinstance(v2, SignSet), f"Expected sign set but got {v2}"
            match opr:
                case jvm.CmpOpr.Ne:
                    equal = False
                    notequal = False
                    for x in v1.sign:
                        for y in v2.sign:
                            if x == y:
                                equal = True
                            if x != y:
                                notequal = True
                    if equal:
                        yield (False, self)
                    if notequal:
                        yield (True, self)
                case jvm.CmpOpr.Eq:
                    equal = False
                    notequal = False
                    for x in v1.sign:
                        for y in v2.sign:
                            if x == y:
                                equal = True
                            if x != y:
                                notequal = True
                    if equal:
                        yield (True, self)
                    if notequal:
                        yield (False, self)
                case jvm.CmpOpr.Gt:
                    greater = False
                    smallerequal = False
                    for x in v1.sign:
                        for y in v2.sign:
                            if x > y:
                                greater = True
                            if x <= y:
                                smallerequal = True
                    if greater:
                        yield (True, self)
                    if smallerequal:
                        yield (False, self)
                case a:
                    raise NotImplementedError(f"The compare operator {a!r}")

    def initialstate_from_method(
        self, methodid: jvm.AbsMethodID, inputs: list[jvm.Value] | None
    ):
        # assert len(methodid.extension.params) == 0, "Expected no parameters
        state = self.bot_from_method(methodid, stack=tuple())

        if inputs is None:
            for i, p in enumerate(methodid.extension.params):
                state.locals[i] = SignSet.top()
        else:
            for i, x in enumerate(inputs):
                state.locals[i] = SignSet.from_singleton(x)

        return StateSet({PC(methodid, 0): state}, abstraction=self)

    def bot_from_method(self, methodid: jvm.AbsMethodID, stack=None):
        method = self.bc.getmethod(methodid)
        # assert len(methodid.extension.params) == 0, "Expected no parameters
        return self.State([SignSet.bot()] * method.max_locals, stack)

    def abstract(self, values):
        return SignSet.abstract(values)


@dataclass
class StateSet[A]:
    instructions: dict[PC, object]
    abstraction: A

    def per_instruction(self):
        return list(self.instructions.items())

    def __getitem__(self, pc: PC):
        return self.instructions.get(pc, self.abstraction.bot_from_method(pc.method))

    def __setitem__(self, pc: PC, item: A):
        assert isinstance(item, self.abstraction.State)
        assert pc in self.abstraction.bc, f"{pc} invalid program counter"
        self.instructions[pc] = item


def manystep2(
    analysis: SignAnalysis,
    pc: PC,
    state: SignAnalysis.State,
) -> Iterable[tuple[PC, object] | str]:
    opr = analysis.bc[pc]
    match opr:
        case jvm.Get(static=True, field=field):
            # Hack - Only handle the assertion case
            assert field.extension.name == "$assertionsDisabled"

            # Hack - Assuming assertions are never disabled
            va = analysis.abstract([jvm.Value.int(0)])

            yield (pc + 1, state.push(va))

        case jvm.Ifz(condition=op, target=target):
            [val], after = state.pop(1)

            for res in after.compare(op, val, analysis.abstract([jvm.Value.int(0)])):
                match res:
                    case (True, final):
                        yield (pc.with_offset(target), final)
                    case (False, final):
                        yield (pc + 1, final)
                    case err:
                        yield err

        case jvm.If(condition=op, target=target):
            [v1, v2], after = state.pop(2)

            for res in after.compare(op, v1, v2):
                match res:
                    case (True, final):
                        yield (pc.with_offset(target), final)
                    case (False, final):
                        yield (pc + 1, final)
                    case err:
                        yield err

        case jvm.Load(index=i):
            va = state.load(i)
            yield (pc + 1, state.push(va))

        case jvm.Push(value=v):
            va = analysis.abstract([v])
            yield (pc + 1, state.push(va))

        case jvm.Binary(operant=op):
            [v1, v2], after = state.pop(2)
            for res in after.binary(op, v1, v2):
                match res:
                    case (v3, final):
                        yield (pc + 1, final.push(v3))
                    case err:
                        yield err

        case jvm.Return(type=None):
            yield "ok"

        case jvm.Return(type=t):
            yield "ok"

        case jvm.New(classname=jvm.ClassName("java/lang/AssertionError")):
            # Hack -- if we create an assertion error, we probably also throw it.
            yield "assertion error"

        case a:
            a.help()
            sys.exit(-1)


def run(suite, methodid, inputs: list[jvm.Value] | None = None, MAX_STEPS=20):
    bc = Bytecode(suite)

    analysis = SignAnalysis(bc)

    final = set()
    sts = analysis.initialstate_from_method(methodid, inputs)
    for i in range(MAX_STEPS):
        for pc, state in sts.per_instruction():
            opr = analysis.bc[pc]
            step = f"STEP {pc}"
            step += f"\n{state}"
            step += f"\n--- {opr} -->"
            for res in manystep2(analysis, pc, state):
                if isinstance(res, str):
                    step += f"\n{res}"
                    final.add(res)
                else:
                    pc, st = res
                    step += f"\n{pc}:  {st}"
                    sts[pc] |= st
            logger.debug(step)

    logger.info(f"The following final states {final} is possible in {MAX_STEPS}")
    return final


def interpret():
    """The static analysis"""
    logging.basicConfig(level=logging.DEBUG, format="%(message)s")
    methodid, input = jpamb.getcase()
    suite = jpamb.Suite.from_cwd()
    final = run(suite, methodid, input.values)
    for f in final:
        print(f)


def analyse():
    """The static analysis"""
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    methodid = jpamb.getmethodid(
        "static",
        "1.0",
        "The Rice Theorem Cookers",
        ["static", "python"],
        for_science=True,
    )

    suite = jpamb.Suite.from_cwd()

    final = run(suite, methodid)

    for f in jpamb.QUERIES:
        if f not in final:
            print(f"{f};0%")
