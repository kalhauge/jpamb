import re
from typing import NamedTuple, Iterable
from dataclasses import dataclass

from typing import Iterator


class Token(NamedTuple):
    type: str
    value: int | float | str
    line: int
    column: int


def tokenize(code):
    token_specification = [
        ("OPEN", r"\("),  # Open Paren
        ("CLOSE", r"\)"),  # Close Paren
        ("SYMBOL", r"[^)(\n \t|]+"),  # Symbol
        ("STEP", r"STEP"),  # Symbol
        ("ESCAPED_SYMBOL", r"\|[^|]*\|"),  # Symbol
        ("NEWLINE", r"\n"),  # Line endings
        ("SKIP", r"[ \t]+"),  # Skip over spaces and tabs
        ("MISMATCH", r"."),  # Any other character
    ]
    tok_regex = "|".join("(?P<%s>%s)" % pair for pair in token_specification)
    line_num = 1
    line_start = 0
    for mo in re.finditer(tok_regex, code):
        kind = mo.lastgroup
        value = mo.group()
        column = mo.start() - line_start
        if kind == "NEWLINE":
            line_start = mo.end()
            line_num += 1
            continue
        elif kind == "SKIP":
            continue
        elif kind == "MISMATCH":
            raise RuntimeError(f"{value!r} unexpected on line {line_num}")
        yield Token(kind, value, line_num, column)


type SExpr = list[SExpr] | str


@dataclass
class Parser:
    head: Token
    stream: Iterator[Token]

    @classmethod
    def from_string(cls, code):
        stream = tokenize(code)
        return cls(next(stream), stream)

    def next(self):
        try:
            self.head = next(self.stream)
        except StopIteration:
            self.head = Token(type="EOF", value="", line=0, column=0)

    def sexpr(self) -> SExpr | None:
        if (a := self.list()) is not None:
            return a
        if (a := self.atom()) is not None:
            return a
        return None

    def atom(self) -> str | None:
        if self.head.type == "SYMBOL":
            value = self.head.value
            self.next()
            return str(value)

        if self.head.type == "ESCAPED_SYMBOL":
            value = str(self.head.value)[1:-1]
            self.next()
            return value

        return None

    def list(self) -> list[SExpr] | None:
        if self.head.type != "OPEN":
            return None

        self.next()

        output = []

        while (a := self.sexpr()) is not None:
            output.append(a)

        if self.head.type != "CLOSE":
            raise RuntimeError(f"Expected CLOSE, but got {self.head.type}")

        self.next()

        return output


def sexpr(obj: object):
    if hasattr(obj, "__sexpr__"):
        return obj.__sexpr__()
    if isinstance(obj, str):
        return obj
    if isinstance(obj, Iterable):
        return list(map(sexpr, obj))
        print("Failed to sexpr")


@dataclass
class Step:
    state: SExpr
    opr: SExpr
    next_state: SExpr


def check_step(step1: Step, step2: Step) -> bool:
    return step1.next_state == step2.state
