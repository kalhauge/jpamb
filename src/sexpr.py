import io
import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import NamedTuple, Protocol, runtime_checkable

type SExpr = list[SExpr] | str


@runtime_checkable
class ToSExpr(Protocol):
    def __sexpr__(self) -> SExpr: ...


type LikeSExpr = ToSExpr | str | int | Iterable[LikeSExpr] | None


def sexpr(obj: LikeSExpr) -> SExpr:
    if isinstance(obj, ToSExpr):
        v = obj.__sexpr__()
        assert isinstance(v, list | str), f"expected s-expr from {obj!r} but got {v!r}"
        return v
    if isinstance(obj, str):
        return obj
    if isinstance(obj, int):
        return str(obj)
    if obj is None:
        return "-"
    if isinstance(obj, Iterable):
        return list(map(sexpr, obj))

    raise TypeError(f"Do not know how to convert {obj!r} to an s-expression")


BAD_SYMBOL = re.compile("[)(\n \t|]")


def data(name: str, *args: object, **kwargs: object) -> list[SExpr]:
    exp = [name]

    for a in args:
        assert isinstance(a, list | str), f"expected s-expr but got {a!r}"
        assert not (isinstance(a, str) and a.startswith(":"))
        exp += [a]

    for k, v in kwargs.items():
        assert isinstance(k, str)
        assert isinstance(v, list | str), f"expected s-expr at :{k} but got {v!r}"
        exp += [":" + k, v]
    return exp


def sequence(values: Iterable[object]) -> list[SExpr]:
    exp = []
    for k, v in enumerate(values):
        assert isinstance(v, list | str), f"expected s-expr but got {v!r}"
        exp += [f":{k}", v]
    return exp


def undata(sexpr: list[SExpr]) -> tuple[str, list[SExpr], dict[str, SExpr]]:
    if not isinstance(sexpr, list) or len(sexpr) == 0:
        raise RuntimeError(f"Unexpected expression: {sexpr}")

    key = sexpr[0]

    if not isinstance(key, str):
        raise TypeError(f"Unexpected expression: {key} in {sexpr}")

    items = list(sexpr[1:])
    args = []
    kwargs = {}

    while len(items):
        a = items.pop(0)
        if isinstance(a, str) and a.startswith(":"):
            k = a[1:]
            assert not k in kwargs
            v = items.pop(0)
            kwargs[k] = v
            continue

        args.append(a)

    return key, args, kwargs


def escape(symbol: str) -> str:
    if symbol == "":
        return "||"

    if BAD_SYMBOL.search(symbol) is not None:
        return f"|{symbol.replace('|', '||')}|"
    else:
        return symbol


def pretty(expr: SExpr, indent=0) -> str:
    if indent != 0:
        output = io.StringIO()
        pretty_indent(expr, output, 0, indent)
        return output.getvalue()

    if isinstance(expr, list):
        return f"({' '.join([pretty(s) for s in expr])})"
    if isinstance(expr, str):
        return escape(expr)
    return pretty(sexpr(expr))


def pretty_indent(expr: SExpr, output, current, indent) -> None:
    if isinstance(expr, list):
        output.write("(")
        if len(expr) == 0:
            output.write(")")
            return

        indented = False

        e = expr[0]
        left = list(expr[1:])

        if isinstance(e, str) and e.startswith(":") and len(left) > 0:
            e2 = left.pop(0)
            output.write("\n" + " " * (current + indent))
            output.write(escape(e))
            output.write(" ")
            indented = True
            pretty_indent(e2, output, current + indent, indent)
        else:
            pretty_indent(expr[0], output, current, indent)

        while left:
            e = left.pop(0)
            if isinstance(e, str) and e.startswith(":") and len(left) > 0:
                e2 = left.pop(0)
                output.write("\n" + " " * (current + indent))
                output.write(escape(e))
                output.write(" ")
                indented = True
                pretty_indent(e2, output, current + indent, indent)
            elif indented:
                output.write("\n" + " " * (current + indent))
                pretty_indent(e, output, current + indent, indent)
            else:
                output.write(" ")
                pretty_indent(e, output, current, indent)
        if indented:
            output.write("\n" + (" " * current))
        output.write(")")
    elif isinstance(expr, str):
        output.write(escape(expr))
    else:
        return pretty_indent(sexpr(expr), output, current, indent)


class Token(NamedTuple):
    type: str
    value: str
    line: int
    column: int


def tokenize(code):
    token_specification = [
        ("OPEN", r"\("),  # Open Paren
        ("CLOSE", r"\)"),  # Close Paren
        ("SYMBOL", r"[^)(\n \t|]+"),  # Symbol
        ("STEP", r"STEP"),  # Symbol
        ("ESCAPED_SYMBOL", r"\|([^|]|\|\|)*\|"),  # Symbol
        ("NEWLINE", r"\n"),  # Line endings
        ("SKIP", r"[ \t]+"),  # Skip over spaces and tabs
        ("MISMATCH", r"."),  # Any other character
    ]
    tok_regex = "|".join(f"(?P<{n}>{r})" for n, r in token_specification)
    line_num = 1
    line_start = 0
    for mo in re.finditer(tok_regex, code):
        kind = mo.lastgroup

        assert kind is not None

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


def from_string(code: str) -> list[SExpr]:
    parser = Parser.from_string(code)
    expressions = []
    while (val := parser.sexpr()) is not None:
        expressions.append(val)

    return expressions


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
            value = str(self.head.value)[1:-1].replace("||", "|")
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
