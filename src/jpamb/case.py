import collections
import re
from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import NoReturn, Optional

import jvm
import jvm.state
import sexpr


@dataclass(frozen=True)
class Value(ABC):
    """A jvm value of a known type."""

    @property
    @abstractmethod
    def type(self) -> jvm.Type: ...

    @abstractmethod
    def encode(self) -> str: ...

    @abstractmethod
    def __sexpr__(self) -> sexpr.SExpr: ...

    def math(self) -> str:
        return sexpr.pretty(sexpr.sexpr(self))

    @classmethod
    def from_sexpr_with_type(cls, expr: sexpr.SExpr, *, type: jvm.Type) -> "Value":
        match type:
            case jvm.Boolean():
                return Boolean(sexpr.to_str(expr).lower() == "true")
            case jvm.Int():
                return Int(sexpr.to_int(expr))
            case jvm.Float():
                return Float(sexpr.to_float(expr))
            case jvm.Char():
                return Char(sexpr.to_str(expr))
            # case jvm.Reference():
            #     value = int(sexpr.to_str(expr), base=0)
            #     return Reference(None if value == 0 else value - 1)
            case jvm.Object(cn) if cn.slashed() == "java/lang/String":
                return String(sexpr.to_str(expr))
            case jvm.Array(contains=jvm.Int()):
                values = sexpr.to_list(expr, valuefn=sexpr.to_int)
                return Array(jvm.Int(), tuple(values))
            case jvm.Array(contains=jvm.Char()):
                values = sexpr.to_list(expr, valuefn=sexpr.to_str)
                return Array(jvm.Char(), tuple(values))
            case _:
                raise sexpr.FromSExprError(f"{expr} is not a known value")

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> "Value":
        values = sexpr.to_values(expr)
        if len(values) < 1:
            raise sexpr.FromSExprError("Expected one or more elements")

        type = jvm.Type.from_sexpr(values[0])

        return cls.from_sexpr_with_type(values[1], type=type)


@dataclass(frozen=True)
class Int(Value):
    value: int

    @property
    def type(self) -> jvm.Type:
        return jvm.Int()

    def encode(self) -> str:
        return str(self.value)

    def __sexpr__(self) -> sexpr.SExpr:
        return sexpr.sexpr(["int", self.value])


@dataclass(frozen=True)
class Boolean(Value):
    value: bool

    @property
    def type(self) -> jvm.Type:
        return jvm.Boolean()

    def encode(self) -> str:
        return "true" if self.value else "false"

    def __sexpr__(self) -> sexpr.SExpr:
        return sexpr.sexpr(["bool", self.value])


@dataclass(frozen=True)
class Float(Value):
    value: float

    @property
    def type(self) -> jvm.Type:
        return jvm.Float()

    def encode(self) -> str:
        return str(self.value)

    def __sexpr__(self) -> sexpr.SExpr:
        return sexpr.sexpr(["float", self.value])


@dataclass(frozen=True)
class Char(Value):
    value: str

    def __post_init__(self):
        assert len(self.value) == 1, (
            f"string should be exactly one char, was {self.value!r}"
        )

    @property
    def type(self) -> jvm.Type:
        return jvm.Char()

    def encode(self) -> str:
        return f"'{self.value}'"

    def __sexpr__(self) -> sexpr.SExpr:
        return sexpr.sexpr(["char", self.value])


@dataclass(frozen=True)
class String(Value):
    value: str

    @property
    def type(self) -> jvm.Type:
        return jvm.Object(jvm.ClassName("java.lang.String"))

    def encode(self) -> str:
        return f"s'{self.value}'"

    def __sexpr__(self) -> sexpr.SExpr:
        return sexpr.sexpr([sexpr.sexpr(self.type), self.value])


@dataclass(frozen=True)
class Array(Value):
    contains: jvm.Type
    values: tuple[int | str | float | bool, ...]

    @property
    def type(self) -> jvm.Type:
        return jvm.Array(self.contains)

    def encode(self) -> str:
        match self.contains:
            case jvm.Int():
                ints = ", ".join(map(str, self.values))
                return f"[I:{ints}]"
            case jvm.Char():
                chars = ", ".join(f"'{a}'" for a in self.values)
                return f"[C:{chars}]"
            case _:
                raise NotImplementedError()

    def __sexpr__(self) -> sexpr.SExpr:
        return sexpr.sexpr([sexpr.sexpr(self.type), sexpr.sexpr(tuple(self.values))])


@dataclass
class InputParser:
    Token = collections.namedtuple("Token", "kind value")

    input: str
    head: Optional["InputParser.Token"]
    _tokens: Iterator["InputParser.Token"]

    def __init__(self, input) -> None:
        self.input = input
        self._tokens = InputParser.tokenize(input)
        self.next()

    @staticmethod
    def tokenize(string):
        token_specification = [
            ("OPEN_ARRAY", r"\[[IC]:"),
            ("CLOSE_ARRAY", r"\]"),
            ("INT", r"-?\d+"),
            ("BOOL", r"true|false"),
            ("CHAR", r"'[^']'"),
            ("STRING", r"s'[^']*'"),
            ("COMMA", r","),
            ("SKIP", r"[ \t]+"),
        ]
        tok_regex = "|".join(f"(?P<{n}>{m})" for n, m in token_specification)

        for m in re.finditer(tok_regex, string):
            kind, value = m.lastgroup, m.group()
            if kind == "SKIP":
                continue
            yield InputParser.Token(kind, value)

    @staticmethod
    def parse(string) -> list[Value]:
        return InputParser(string).parse_comma_seperated_values()

    def next(self):
        try:
            self.head = next(self._tokens)
        except StopIteration:
            self.head = None

    def expected(self, expected) -> NoReturn:
        raise ValueError(f"Expected {expected} but got {self.head} in {self.input}")

    def expect(self, expect) -> Token:
        head = self.head
        if head is None or expect != head.kind:
            self.expected(repr(expect))
        self.next()
        return head

    def eof(self):
        if self.head is None:
            return
        self.expected("end of file")

    def parse_value(self):
        next = self.head or self.expected("token")
        match next.kind:
            case "INT":
                return Int(self.parse_int())
            case "CHAR":
                return Char(self.parse_char())
            case "BOOL":
                return Boolean(self.parse_bool())
            case "STRING":
                return String(self.parse_string())
            case "OPEN_ARRAY":
                return self.parse_array()
        self.expected("char")

    def parse_int(self):
        tok = self.expect("INT")
        return int(tok.value)

    def parse_bool(self):
        tok = self.expect("BOOL")
        return tok.value == "true"

    def parse_char(self):
        tok = self.expect("CHAR")
        return tok.value[1]

    def parse_string(self):
        tok = self.expect("STRING")
        return tok.value[2:-1]

    def parse_array(self):
        key = self.expect("OPEN_ARRAY")
        if key.value == "[I:":  # ]
            type = jvm.Array(jvm.Int())
            parser = self.parse_int
        elif key.value == "[C:":  # ]
            type = jvm.Array(jvm.Char())
            parser = self.parse_char
        else:
            self.expected("int or char array")

        inputs = self.parse_comma_seperated_values(parser, "CLOSE_ARRAY")

        self.expect("CLOSE_ARRAY")

        return Array(type.contains, tuple(inputs))

    def parse_comma_seperated_values(self, parser=None, end_by=None):
        if self.head is None:
            return []

        if end_by is not None and self.head.kind == end_by:
            return []

        parser = parser or self.parse_value
        inputs = [parser()]

        while self.head is not None and self.head.kind == "COMMA":
            self.next()
            inputs.append(parser())

        return inputs


@dataclass(frozen=True, slots=True)
class Input:
    """
    An 'Input' to a 'Case' is a comma seperated list of JVM values
    """

    values: tuple[Value, ...]

    @staticmethod
    def decode(code: str) -> "Input":
        if code[0] != "(" and code[-1] != ")":
            raise ValueError(f"Expected input to be in parenthesis, but got {code}")
        vp = InputParser(code)
        values = vp.parse_comma_seperated_values()
        vp.eof()
        return Input(tuple(values))

    def encode(self) -> str:
        return "(" + ", ".join(v.encode() for v in self.values) + ")"

    def __sexpr__(self) -> sexpr.SExpr:
        return self.encode()

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> "Input":
        return cls.decode(sexpr.to_str(expr))

    def parameter_types(self) -> jvm.Parameters:
        return jvm.Parameters(tuple(v.type for v in self.values))


EXPERIMENT_RE = re.compile(
    r"(?P<classname>[^(]+)\.(?P<methodname>[^(]+)(?P<input>[:!]\(.*\))(?P<retype>[^)]+)",
    re.MULTILINE,
)


@dataclass(frozen=True, eq=True, slots=True)
class Experiment:
    entry: jvm.AbsMethodID
    input: Input | None

    def __post_init__(self):
        if self.input is not None:
            assert self.entry.extension.params == self.input.parameter_types(), (
                f"Input did not match method: {self.entry.extension} {self.input}"
            )

    def encode(self) -> str:
        if self.input is not None:
            method = self.entry.extension
            rt = method.return_type.encode() if method.return_type is not None else "V"
            return f"{self.entry.classname}.{self.entry.extension.name}!{self.input.encode()}{rt}"
        else:
            return self.entry.encode()

    def __str__(self) -> str:
        return self.encode()

    def __lt__(self, other):
        return self.encode() < other.encode()

    @classmethod
    def decode(cls, code: str) -> "Experiment":
        result = EXPERIMENT_RE.fullmatch(code)
        assert result, code
        cn = jvm.ClassName.decode(result.group("classname"))
        mn = result.group("methodname")
        inp = result.group("input")
        if inp.startswith(":"):
            i = None
            params = jvm.Parameters.decode(inp[2:-1])
        else:
            i = Input.decode(inp[1:])
            params = i.parameter_types()
        rt = (
            jvm.Type.decode(result.group("retype"))
            if result.group("retype") != "V"
            else None
        )
        assert not isinstance(rt, tuple), rt
        entry = jvm.AbsMethodID(
            cn,
            jvm.MethodID(name=mn, params=params, return_type=rt),
        )
        return Experiment(entry, i)

    def as_test(self, interpreter: tuple[str, ...], max_steps: int) -> tuple[str, ...]:
        return interpreter + (
            self.entry.encode(),
            "ALL" if self.input is None else self.input.encode(),
            str(max_steps),
        )

    def short(self) -> str:
        if self.input is not None:
            return f"{self.entry.extension.name}:{self.input.encode()}"
        return f"{self.entry.extension.name}:ALL"

    def __sexpr__(self) -> sexpr.SExpr:
        return self.encode()

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> "Experiment":
        return cls.decode(sexpr.to_str(expr))


CASE_RE = re.compile(r"([^ ]*) +(\([^)]*\)) -> (.*)")


@dataclass(frozen=True, order=True)
class Case(sexpr.AsSExpr):
    """
    A 'Case' is an absolute method id, an input, and the expected result.
    """

    experiment: Experiment
    result: str

    @property
    def methodid(self) -> jvm.AbsMethodID:
        return self.experiment.entry

    @property
    def input(self) -> Input:
        assert self.experiment.input is not None
        return self.experiment.input

    @property
    def results(self) -> set[str]:
        return {self.result}

    @staticmethod
    def match(line) -> re.Match:
        if not (m := CASE_RE.match(line)):
            raise ValueError(f"Unexpected line: {line!r}")
        return m

    @staticmethod
    def decode(line):
        m = Case.match(line)
        return Case(
            Experiment(
                jvm.AbsMethodID.decode(m.group(1)),
                Input.decode(m.group(2)),
            ),
            m.group(3),
        )

    def encode(self) -> str:
        return f"{self.methodid.classname}.{self.methodid.extension.encode()} {self.input.encode()} -> {self.result}"

    @staticmethod
    def by_entry(
        iterable: Iterable["Case"],
    ) -> list[tuple[jvm.AbsMethodID, list["Case"]]]:
        """Given an interable of cases, group the cases by the entry"""
        cases_by_id = collections.defaultdict(list)

        for c in iterable:
            cases_by_id[c.methodid].append(c)

        return sorted(cases_by_id.items())


@dataclass(slots=True)
class Coverage(sexpr.AsSExpr):
    reachable: set[int] | None = None
    # unreachable: set[int] | None = None


@dataclass(frozen=True, slots=True)
class Control(sexpr.AsSExpr):
    coverage: dict[jvm.AbsMethodID, Coverage]
    results: set[str]

    def is_reachable(self, pc: jvm.state.PC) -> bool:
        coverage = self.coverage.get(pc.method)
        return (
            coverage is not None
            and coverage.reachable is not None
            and pc.offset in coverage.reachable
        )

    def reachable(self) -> set[jvm.state.PC]:
        reachable = set()
        for m, c in self.coverage.items():
            if c.reachable is not None:
                reachable.update(jvm.state.PC(m, o) for o in c.reachable)
        return reachable


type Entry = jvm.AbsMethodID


@dataclass(frozen=True, slots=True)
class Benchmark:
    experiments: collections.OrderedDict[Experiment, Control]

    def __sexpr__(self) -> sexpr.SExpr:
        experiments = sexpr.sexpr(self.experiments)
        assert isinstance(experiments, list)
        return [sexpr.item("benchmark")] + experiments

    @classmethod
    def from_sexpr(cls, expr) -> "Benchmark":
        options = sexpr.to_options(expr)
        return Benchmark(
            sexpr.from_sexpr(
                options[1:], target=collections.OrderedDict[Experiment, Control]
            )
        )

    def entries(self) -> Iterable[Entry]:
        entries = set()
        for e in self.experiments:
            if e.entry not in entries:
                yield e.entry
                entries.add(e)
