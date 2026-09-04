import io
import re
from collections.abc import Iterable, Iterator
import dataclasses
from dataclasses import dataclass
from typing import (
    NamedTuple,
    Protocol,
    runtime_checkable,
    Callable,
    TypeIs,
    Self,
    Sequence,
)

from functools import partial
import typing


@runtime_checkable
class Encodable(Protocol):
    def encode(self) -> str: ...


def encode(obj: str | Encodable) -> str:
    if isinstance(obj, str):
        return obj

    return obj.encode()


@dataclass(frozen=True, slots=True)
class Option[T]:
    key: str
    value: T

    def __post_init__(self):
        assert isinstance(self.key, str)

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
    if isinstance(obj, dict):
        return [Option(encode(k), sexpr(v)) for k, v in obj.items()]
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
    assert isinstance(name, str), f"expected string but got {name!r}"

    exp: list[Option[SExpr]] = [Option.unkeyed(name)]
    exp += values(args, deep=deep)
    exp += items(kwargs.items(), deep=deep)
    return exp


def sexprtag(cls: type) -> str:
    if getattr(cls, "__sexprtag__", None):
        return cls.__sexprtag__
    name = cls.__name__
    result = re.sub(r"(?=[A-Z])", "-", name[1:])
    return (name[0] + result).lower()


def from_dataclass(obj: object) -> list[Option[SExpr]]:
    return data(
        sexprtag(obj.__class__),
        **{f.name: getattr(obj, f.name) for f in dataclasses.fields(obj)},
    )


def from_dataclass_values(obj: object) -> list[Option[SExpr]]:
    return data(
        sexprtag(obj.__class__),
        *[getattr(obj, f.name) for f in dataclasses.fields(obj)],
    )


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


class FromSExprError(ValueError):
    pass


@runtime_checkable
class Decodable(Protocol):
    @classmethod
    def decode(cls, code: str) -> Self: ...


def from_sexpr(expr: SExpr, *, target: type):
    if hasattr(target, "from_sexpr"):
        return target.from_sexpr(expr)

    if target is int:
        return int_from_sexpr(expr)

    if target is float:
        return float_from_sexpr(expr)

    if target is str:
        return str_from_sexpr(expr)

    if typing.get_origin(target) is dict:
        tkey, tvalue = typing.get_args(target)
        if tkey is str:
            return dict_from_sexpr(expr, valuefn=partial(from_sexpr, target=tvalue))

        if issubclass(tkey, Decodable):
            return dict_from_sexpr(
                expr, keyfn=tkey.decode, valuefn=partial(from_sexpr, target=tvalue)
            )

    if typing.get_origin(target) is tuple:
        args = typing.get_args(target)

        if len(args) == 2 and args[1] == Ellipsis:
            return tuple(
                list_from_sexpr(
                    expr,
                    handler=partial(from_sexpr, target=args[0]),
                )
            )

        return tuple_from_sexpr(
            expr, handlers=[partial(from_sexpr, target=t) for t in args]
        )

    if typing.get_origin(target) is set:
        (arg,) = typing.get_args(target)

        return set(
            list_from_sexpr(
                expr,
                handler=partial(from_sexpr, target=arg),
            )
        )

    if typing.get_origin(target) is list:
        (arg,) = typing.get_args(target)
        return list_from_sexpr(
            expr,
            handler=partial(from_sexpr, target=arg),
        )

    raise NotImplementedError(
        f"No implementation of type {typing.get_origin(target)} to {target}"
    )


def union_from_sexpr[T](expr: SExpr, *, targets: Iterable[type[T]]) -> T:
    for t in targets:
        try:
            return from_sexpr(expr, target=t)
        except FromSExprError:
            continue

    raise FromSExprError(f"Could not match {expr} with any of {targets}")


def dataclass_from_sexpr[T](expr: SExpr, *, target: type[T]) -> T:
    kname, args, kwargs = data_from_sexpr(expr)

    if kname != sexprtag(target):
        raise FromSExprError(f"Expected {sexprtag(target)}, but got {kname}")

    annotations = list(dataclasses.fields(target))

    if len(args) > len(annotations):
        raise FromSExprError(
            f"Expected {len(annotations)} arguments, but got {len(args)}: {args}"
        )

    _args = []
    for arg, field in zip(args, annotations):
        _args.append(from_sexpr(arg, target=field.type))

    _kwargs = {}
    for field in annotations[len(args) :]:
        if not field.name in kwargs:
            raise FromSExprError(
                f"Expected {key!r} option, but only got {kwargs.keys()}"
            )

        _kwargs[field.name] = from_sexpr(kwargs[field.name], target=field.type)
        del kwargs[field.name]

    if kwargs:
        raise FromSExprError(f"Found {kwargs.keys()} options, not in dataclass")

    return target(*_args, **_kwargs)


def str_from_sexpr(sexpr: SExpr) -> str:
    if not isinstance(sexpr, str):
        raise FromSExprError("expected symbol but fund list or keyword")

    return sexpr


def float_from_sexpr(sexpr: SExpr) -> float:
    string = str_from_sexpr(sexpr)

    try:
        return float(string)
    except ValueError as e:
        raise FromSExprError(e)


def int_from_sexpr(expr: SExpr) -> float:
    string = str_from_sexpr(expr)

    try:
        return int(string)
    except ValueError as e:
        raise FromSExprError(e)


def list_from_sexpr[T](expr: SExpr, *, handler: Callable[[SExpr], T]) -> list[T]:
    if not isinstance(expr, list):
        raise FromSExprError("expected list but fund symbol")

    items: list[T] = []
    for v in expr:
        assert not v.key
        items.append(handler(v.value))

    return items


def tuple_from_sexpr(
    expr: SExpr, *, handlers: Sequence[Callable[[SExpr], object]]
) -> tuple:
    if not isinstance(expr, list):
        raise FromSExprError("expected list but fund symbol")

    if len(expr) != len(handlers):
        raise FromSExprError(f"expected {len(handlers)} element but fund {len(expr)}")

    items = []
    for e, h in zip(expr, handlers):
        assert not e.key
        items.append(h(e.value))

    return tuple(items)


def dict_from_sexpr[K, V](
    sexpr: SExpr,
    *,
    keyfn: Callable[[str], K] = str,
    valuefn: Callable[[SExpr], V],
) -> str:
    if not isinstance(sexpr, list):
        raise FromSExprError("expected list but fund symbol")

    items: dict[K, V] = {}
    for opt in sexpr:
        key = keyfn(opt.key)
        assert key not in items
        items[keyfn(opt.key)] = valuefn(opt.value)

    return items


def data_from_sexpr(
    sexpr: list[Option[SExpr]],
) -> tuple[str, list[SExpr], dict[str, SExpr]]:
    if not isinstance(sexpr, list) or len(sexpr) == 0:
        raise FromSExprError(f"Unexpected expression: {sexpr}")

    key = sexpr[0]

    if key.key:
        raise FromSExprError(f"Unexpected key {key.key} in {sexpr}")

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
