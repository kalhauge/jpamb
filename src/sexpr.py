import io
import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import NamedTuple, Protocol, runtime_checkable, Callable

type SExpr = list[SExpr] | str


@runtime_checkable
class ToSExpr(Protocol):
    def __sexpr__(self) -> SExpr: ...


type LikeSExpr = ToSExpr | str | int | float | Iterable[LikeSExpr] | None


class ParseError(BaseException):
    msg: str

    pass


def sexpr(obj: LikeSExpr) -> SExpr:
    if isinstance(obj, ToSExpr):
        v = obj.__sexpr__()
        assert isinstance(v, list | str), f"expected s-expr from {obj!r} but got {v!r}"
        return v
    if isinstance(obj, str):
        return obj
    if isinstance(obj, int):
        return str(obj)
    if isinstance(obj, float):
        return str(obj)
    if obj is None:
        return "-"
    if isinstance(obj, Iterable):
        return list(map(sexpr, obj))

    raise TypeError(f"Do not know how to convert {obj!r} to an s-expression")


def data(name: str, /, *args: SExpr, **kwargs: SExpr) -> list[SExpr]:
    exp: list[SExpr] = [name]
    exp += values(args)
    exp += items(kwargs.items())
    return exp


def sequence(
    values: Iterable[LikeSExpr],
    *,
    keyfmt: Callable[..., str] = str,
    deep=True,
) -> list[SExpr]:
    return items(((keyfmt(k), v) for k, v in enumerate(values)), deep=deep)


def values(values: Iterable[LikeSExpr], *, deep=True) -> list[SExpr]:
    exp = []
    for a in values:
        if deep:
            a = sexpr(a)
        assert isinstance(a, list | str), f"expected s-expr but got {a!r}"
        assert not (isinstance(a, str) and a.startswith(":"))
        exp += [a]
    return exp


def items[K](
    items: Iterable[tuple[K, LikeSExpr]],
    *,
    keyfmt: Callable[[K], str] = str,
    deep=True,
) -> list[SExpr]:
    exp = []
    for k, v in items:
        if deep:
            v = sexpr(v)
        assert isinstance(k, str), f"expected str but got {k!r}"
        assert isinstance(v, list | str), f"expected s-expr but got {v!r}"
        exp += [f":{keyfmt(k)}", v]
    return exp


def undata(sexpr: SExpr) -> tuple[str, list[SExpr], dict[str, SExpr]]:
    pass


def unsymbol(sexpr: SExpr) -> str:
    if not isinstance(sexpr, str):
        raise UnsexprError("expected symbol but fund list")

    if sexpr.startswith(":"):
        raise UnsexprError("expected symbol but found keyword")

    return sexpr


def unfloat(sexpr: SExpr) -> float:
    string = unsymbol(sexpr)

    try:
        return float(string)
    except ValueError as e:
        raise UnsexprError(e)


def unint(sexpr: SExpr) -> float:
    string = unsymbol(sexpr)

    try:
        return int(string)
    except ValueError as e:
        raise UnsexprError(e)


def unlist[T](sexpr: SExpr, *, handler: Callable[[SExpr], T]) -> list[T]:
    if not isinstance(sexpr, list):
        raise UnsexprError("expected list but fund symbol")

    return [handler(v) for v in sexpr]


def undata(sexpr: list[SExpr]) -> tuple[str, list[SExpr], dict[str, SExpr]]:
    if not isinstance(sexpr, list) or len(sexpr) == 0:
        raise ValueError(f"Unexpected expression: {sexpr}")

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
            assert k not in kwargs
            v = items.pop(0)
            kwargs[k] = v
            continue

        args.append(a)

    return key, args, kwargs


def unlist(sexpr: SExpr) -> dict[str, SExpr]:
    if not isinstance(sexpr, list) or len(sexpr) == 0:
        raise RuntimeError(f"Unexpected expression: {sexpr}")

    items = list(sexpr)
    kwargs = {}

    while len(items):
        a = items.pop(0)
        if isinstance(a, str) and a.startswith(":"):
            k = a[1:]
            assert k not in kwargs
            v = items.pop(0)
            kwargs[k] = v
            continue

    return kwargs


BAD_SYMBOL = re.compile("[)(\n \t|]")


def escape(symbol: str) -> str:
    if symbol == "":
        return "||"

    if BAD_SYMBOL.search(symbol) is not None:
        if symbol.startswith(":"):
            return f":|{symbol[1:].replace('|', '||')}|"

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


class ParseError(Exception):
    pass


def tokenize(code):
    token_specification = [
        ("OPEN", r"\("),  # Open Paren
        ("CLOSE", r"\)"),  # Close Paren
        ("SYMBOL", r"[^)(\n \t|]+(?![^)(\n \t])"),  # Symbol
        ("STEP", r"STEP"),  # Symbol
        ("ESCAPED_SYMBOL", r":?\|([^|]|\|\|)*\|"),  # Symbol
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
            raise ParseError(f"{value!r} unexpected on line {line_num}")
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
            if self.head.value[0] == ":":
                value = ":" + str(self.head.value)[2:-1].replace("||", "|")
            else:
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
