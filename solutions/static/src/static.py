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


@dataclass(frozen=True)
class Method:
    id: jvm.AbsMethodID
    opcodes: list[jvm.Opcode]
    max_locals: int


@dataclass
class Bytecode:
    suite: jpamb.Suite
    methods: dict[jvm.AbsMethodID, Method] = field(default_factory=dict)

    def getmethod(self, methodid: jvm.AbsMethodID) -> Method:
        try:
            method = self.methods[methodid]
        except KeyError:
            opcodes = list(self.suite.method_opcodes(methodid))
            max_locals = self.suite.method_max_locals(methodid)
            method = Method(methodid, opcodes, max_locals)
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
            case a:
                assert False, f"Unsupported value {a}"

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

        def logical(
            self, opr: str, v1: SignSet, v2: SignSet
        ) -> Iterable[tuple[bool, "SignAnalysis"]]:
            assert isinstance(v1, SignSet), f"Expected sign set but got {v1}"
            assert isinstance(v2, SignSet), f"Expected sign set but got {v2}"
            match opr:
                case "ne":
                    if len(v1.sign & v1.sign) > 0:
                        yield (False, self)
                    yield (True, self)
                case "gt":
                    greater = False
                    smallerequal = False
                    for x in v1.sign:
                        for y in v1.sign:
                            if x > y:
                                greater = True
                            if x <= y:
                                smallerequal = True
                    if greater:
                        yield (True, self)
                    if smallerequal:
                        yield (False, self)
                case a:
                    raise NotImplementedError(f"The logical operator {a}")

    def initialstate_from_method(self, methodid: jvm.AbsMethodID):
        # assert len(methodid.extension.params) == 0, "Expected no parameters
        state = self.bot_from_method(methodid, stack=tuple())

        for i, p in enumerate(methodid.extension.params):
            state.locals[i] = SignSet.top()

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

        case jvm.Ifz(condition=opr, target=target):
            [val], after = state.pop(1)

            for res in after.logical(opr, val, analysis.abstract([jvm.Value.int(0)])):
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

        case jvm.Return(type=None):
            yield "ok"

        case jvm.New(classname=jvm.ClassName("java/lang/AssertionError")):
            # Hack -- if we create an assertion error, we probably also throw it.
            yield "assertion error"

        case a:
            a.help()
            sys.exit(-1)


def run(suite, methodid, MAX_STEPS=10):
    bc = Bytecode(suite)

    analysis = SignAnalysis(bc)

    final = set()
    sts = analysis.initialstate_from_method(methodid)
    for i in range(MAX_STEPS):
        for pc, state in states.per_instruction():
            opr = analysis.bc[pc]
            logger.debug(f"{pc} {opr}\n{state}")
            for res in manystep2(analysis, pc, state):
                logger.debug(f"-> {res}")
                if isinstance(s, str):
                    final.add(s)
                else:
                    pc, st = s
                    sts[pc] |= st

    logger.info(f"The following final states {final} is possible in {MAX_STEPS}")
    return final


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
