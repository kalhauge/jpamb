import io
import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import NamedTuple, Protocol, runtime_checkable, Callable, TypeIs, Self


class Option[T](NamedTuple):
    key: str
    value: T

    @classmethod
    def unkeyed(cls, value: T) -> Self:
        return cls("", value)

    def unitem(self) -> T:
        if self.key:
            raise ValueError("Can't unitem a keyed option")
        return self.value

    def __repr__(self):
        if self.key:
            return f"option({self.key!r}, {self.value!r})"
        else:
            return f"item({self.value!r})"


type SExpr = list[Option[SExpr]] | str


def item(value: SExpr) -> Option[SExpr]:
    return Option.unkeyed(value)


def option(key: str, value: SExpr) -> Option[SExpr]:
    return Option(key, value)


def issexpr(expr: object, *, deep=True) -> TypeIs[SExpr]:
    if isinstance(expr, list):
        return all(
            isinstance(e, Option) and (not deep or issexpr(e.value, deep=True))
            for e in expr
        )
    return isinstance(expr, str)


@runtime_checkable
class ToSExpr(Protocol):
    def __sexpr__(self) -> SExpr: ...


type LikeSExpr = (
    ToSExpr | str | int | float | Iterable[LikeSExpr | Option[SExpr]] | None
)


class ParseError(BaseException):
    msg: str


def sexpr(obj: LikeSExpr) -> SExpr:
    if isinstance(obj, ToSExpr):
        v = obj.__sexpr__()
        assert issexpr(v, deep=False), f"expected s-expr from {obj!r} but got {v!r}"
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
        items = []
        for e in obj:
            if isinstance(e, Option):
                items.append(e)
            else:
                items.append(Option.unkeyed(sexpr(e)))
        return items

    raise TypeError(f"Do not know how to convert {obj!r} to an s-expression")


def data(
    name: str, /, *args: LikeSExpr, deep=True, **kwargs: LikeSExpr
) -> list[Option[SExpr]]:
    assert isinstance(name, str)
    exp: list[Option[SExpr]] = [Option.unkeyed(name)]
    exp += values(args, deep=deep)
    exp += items(kwargs.items(), deep=deep)
    return exp


def sequence(
    values: Iterable[LikeSExpr],
    *,
    keyfmt: Callable[[int], str] = str,
    deep=True,
) -> list[Option[SExpr]]:
    return items(enumerate(values), keyfmt=keyfmt, deep=deep)


def values(values: Iterable[LikeSExpr], *, deep=True) -> list[Option[SExpr]]:
    exp = []
    for a in values:
        if deep:
            a = sexpr(a)
        assert issexpr(a), f"expected s-expr but got {a!r}"
        exp += [Option.unkeyed(a)]
    return exp


def items[K](
    items: Iterable[tuple[K, LikeSExpr]],
    *,
    keyfmt: Callable[[K], str] = str,
    deep=True,
) -> list[Option[SExpr]]:
    exp = []
    for k, v in items:
        if deep:
            v = sexpr(v)
        assert issexpr(v), f"expected s-expr but got {v!r}"
        exp += [Option(keyfmt(k), v)]
    return exp


def undata(sexpr: SExpr) -> tuple[str, list[SExpr], dict[str, SExpr]]:
    pass


def unsymbol(sexpr: SExpr) -> str:
    if not isinstance(sexpr, str):
        raise UnsexprError("expected symbol but fund list or keyword")

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

    items: list[T] = []
    for v in sexpr:
        assert not v.key
        items.append(handler(v.value))

    return items


def undata(sexpr: list[Option[SExpr]]) -> tuple[str, list[SExpr], dict[str, SExpr]]:
    if not isinstance(sexpr, list) or len(sexpr) == 0:
        raise ValueError(f"Unexpected expression: {sexpr}")

    key = sexpr[0]

    if key.key:
        raise TypeError(f"Unexpected key {key.key} in {sexpr}")

    assert isinstance(key.value, str), "expected first argument to be string"

    args = []
    kwargs = {}

    for option in sexpr[1:]:
        if k := option.key:
            assert k != ""
            assert not k in kwargs
            kwargs[k] = option.value
        else:
            args.append(option.value)

    return key.value, args, kwargs


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

    if BAD_SYMBOL.search(symbol) is not None or symbol.startswith(":"):
        return f"|{symbol.replace('|', '||')}|"
    else:
        return symbol


def pretty(expr: SExpr, indent=0) -> str:
    if indent != 0:
        output = io.StringIO()
        pretty_indent(expr, output, 0, indent)
        return output.getvalue()

    if isinstance(expr, list):
        return f"({' '.join(f':{escape(s.key)} {pretty(s.value)}' if s.key else pretty(s.value) for s in expr)})"

    if isinstance(expr, str):
        return escape(expr)

    raise TypeError(f"{expr!r} is not a s-expression")


def pretty_indent(expr: SExpr, output, current, indent) -> None:
    if isinstance(expr, list):
        output.write("(")
        if len(expr) == 0:
            output.write(")")
            return

        spacing = ""

        if indent > 0:
            spacing = "\n" + " " * (current + indent)

        for e in expr:
            if e.key:
                output.write(spacing)
                output.write(":")
                output.write(escape(e.key))
                output.write(" ")
                pretty_indent(e.value, output, current + indent, indent)
            else:
                output.write(spacing)
                pretty_indent(e.value, output, current + indent, indent)

            if not spacing:
                spacing = " "

        if spacing != " ":
            output.write("\n" + " " * current)

        output.write(")")

    elif isinstance(expr, str):
        output.write(escape(expr))

    else:
        raise TypeError(f"{expr!r} is not a s-expression")


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
        ("KEYWORD", r":[^)(\n \t|]+(?![^)(\n \t])"),
        ("ESCAPED_KEYWORD", r":\|([^|]|\|\|)*\|"),
        ("SYMBOL", r"[^)(\n \t|:][^)(\n \t|]*(?![^)(\n \t])"),
        ("ESCAPED_SYMBOL", r"\|([^|]|\|\|)*\|"),
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
            value = str(self.head.value)[1:-1].replace("||", "|")
            self.next()
            return value

        return None

    def keyword(self) -> str | None:
        if self.head.type == "KEYWORD":
            value = self.head.value
            self.next()
            return value[1:]

        if self.head.type == "ESCAPED_KEYWORD":
            value = str(self.head.value)[2:-1].replace("||", "|")
            self.next()
            return value

    def list(self) -> list[Option[SExpr]] | None:
        if self.head.type != "OPEN":
            return None

        self.next()

        output = []

        for i in range(1000):
            key = self.keyword()
            value = self.sexpr()

            if value is None:
                if key is None:
                    break
                raise ParseError(
                    f"Expected s-expression after keyword {key} but got {self.head.type}"
                )

            output.append(Option(key or "", value))
        else:
            raise ParseError(f"Expected CLOSE, but ran for more than {i} iterations")

        if self.head.type != "CLOSE":
            raise ParseError(f"Expected CLOSE, but got {self.head.type}")

        self.next()

        return output
