import dataclasses
import io
import re
import types
import typing
from collections import OrderedDict
from collections.abc import Callable, Iterable, Iterator, Sequence
from dataclasses import dataclass
from functools import partial
from typing import (
    TYPE_CHECKING,
    Any,
    GenericAlias,
    NamedTuple,
    Protocol,
    Self,
    TypeIs,
    runtime_checkable,
)

if TYPE_CHECKING:
    from _typeshed import DataclassInstance
else:
    DataclassInstance = None


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
    ToSExpr | str | int | bool | float | Iterable[LikeSExpr | Option[SExpr]] | None
)


class ParseError(Exception):
    msg: str


def sexpr(obj: LikeSExpr) -> SExpr:
    if isinstance(obj, ToSExpr):
        v = obj.__sexpr__()
        assert issexpr(v, deep=False), f"expected s-expr from {obj!r} but got {v!r}"
        return v
    if isinstance(obj, str):
        return obj
    if isinstance(obj, bool):
        return str(obj).lower()
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
        assert hasattr(cls, "__sexprtag__")
        return str(cls.__sexprtag__)
    name = cls.__name__
    result = re.sub(r"(?=[A-Z])", "-", name[1:])
    return (name[0] + result).lower()


def from_dataclass(obj: DataclassInstance) -> list[Option[SExpr]]:
    return data(
        sexprtag(obj.__class__),
        **{f.name: getattr(obj, f.name) for f in dataclasses.fields(obj)},
    )


def from_dataclass_values(obj: DataclassInstance) -> list[Option[SExpr]]:
    kwargs = {}
    args = []
    for f in dataclasses.fields(obj):
        if f.kw_only:
            kwargs[f.name] = getattr(obj, f.name)
        else:
            args.append(getattr(obj, f.name))

    return data(sexprtag(obj.__class__), *args, **kwargs)


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


def from_sexpr(expr: SExpr, *, target: type[Any]):
    if isinstance(target, typing.TypeAliasType):
        if target is SExpr:
            return expr
        return from_sexpr(expr, target=target.__value__)

    if hasattr(target, "from_sexpr"):
        return target.from_sexpr(expr)

    if target is int:
        return to_int(expr)

    if target is float:
        return to_float(expr)

    if target is str:
        return to_str(expr)

    if target is bool:
        return to_bool(expr)

    origin = typing.get_origin(target)

    if origin is dict or origin is OrderedDict:
        tkey, tvalue = typing.get_args(target)
        if tkey is str:
            val = to_dict(expr, keyfn=str, valuefn=partial(from_sexpr, target=tvalue))
        elif isinstance(tkey, type) and issubclass(tkey, Decodable):
            val = to_dict(
                expr, keyfn=tkey.decode, valuefn=partial(from_sexpr, target=tvalue)
            )
        else:
            raise NotImplementedError(
                f"No implementation of type {typing.get_origin(target)} to {target}"
            )

        if origin is OrderedDict:
            return OrderedDict(val)
        return val

    if typing.get_origin(target) is tuple:
        args = typing.get_args(target)

        if len(args) == 2 and args[1] == Ellipsis:
            return tuple(
                to_list(
                    expr,
                    valuefn=partial(from_sexpr, target=args[0]),
                )
            )

        return to_tuple(expr, handlers=[partial(from_sexpr, target=t) for t in args])

    if typing.get_origin(target) is set:
        (arg,) = typing.get_args(target)

        return set(
            to_list(
                expr,
                valuefn=partial(from_sexpr, target=arg),
            )
        )

    if typing.get_origin(target) is list:
        (arg,) = typing.get_args(target)
        if typing.get_origin(arg) is Option:
            (arg,) = typing.get_args(arg)
        return to_list(
            expr,
            valuefn=partial(from_sexpr, target=arg),
        )

    if isinstance(target, types.UnionType):
        return to_union(expr, targets=target.__args__)

    if target is type(None):
        return None

    raise NotImplementedError(
        f"No implementation of type {typing.get_origin(target)} to {target}"
    )


def to_union[T](expr: SExpr, *, targets: Iterable[type[T]]) -> T:
    for t in targets:
        try:
            return from_sexpr(expr, target=t)
        except FromSExprError:
            continue

    raise FromSExprError(f"Could not match {expr} with any of {targets}")


def to_tagged_union[T](expr: SExpr, *, targets: dict[str, type[T]]) -> T:
    options = to_options(expr)
    if len(options) == 0:
        raise FromSExprError("Expected tag, but got empty list ")

    tag = options[0].unitem()

    if tag not in targets:
        raise FromSExprError(f"Could not find {tag!r} tag in {list(targets)}")
    return from_sexpr(expr, target=targets[tag])


def to_dataclass[T: DataclassInstance](expr: SExpr, *, target: type[T]) -> T:
    kname, args, kwargs = to_data(expr)

    if kname != sexprtag(target):
        raise FromSExprError(f"Expected {sexprtag(target)}, but got {kname}")

    annotations = list(dataclasses.fields(target))

    if len(args) > len(annotations):
        raise FromSExprError(
            f"Expected {len(annotations)} arguments, but got {len(args)}: {args}"
        )

    def is_resolvable_type(t):
        return isinstance(
            t,
            type
            | GenericAlias
            | types.UnionType
            | typing._GenericAlias
            | typing.TypeAliasType,
        )

    keyed = []
    positionals = []

    for ann in annotations:
        if ann.kw_only:
            keyed.append(ann)
        else:
            positionals.append(ann)

    _args = []
    for arg, field in zip(args, positionals):
        if not is_resolvable_type(field.type):
            raise TypeError(
                f"Expected type of field {field.name!r} to be type, not {field.type!r}"
            )

        _args.append(from_sexpr(arg, target=field.type))

    _kwargs = {}
    for field in positionals[len(args) :] + keyed:
        if not field.name in kwargs:
            raise FromSExprError(
                f"Expected {field.name!r} option, but only got {kwargs.keys()}"
            )

        if not is_resolvable_type(field.type):
            raise TypeError(
                f"Expected type of field {field.name!r} to be type, not {field.type!r}"
            )

        _kwargs[field.name] = from_sexpr(kwargs[field.name], target=field.type)
        del kwargs[field.name]

    if kwargs:
        raise FromSExprError(f"Found {kwargs.keys()} options, not in dataclass")

    return target(*_args, **_kwargs)


def to_str(expr: SExpr) -> str:
    if not isinstance(expr, str):
        raise FromSExprError(f"expected symbol but found: {expr}")

    return expr


def to_float(sexpr: SExpr) -> float:
    string = to_str(sexpr)

    try:
        return float(string)
    except ValueError as e:
        raise FromSExprError(e)


def to_int(expr: SExpr) -> int:
    string = to_str(expr)

    try:
        return int(string)
    except ValueError as e:
        raise FromSExprError(e)


def to_bool(expr: SExpr) -> bool:
    string = to_str(expr)

    if string == "true":
        return True

    if string == "false":
        return False

    raise FromSExprError(f"Not a bool {expr!r}")


def to_list[T](expr: SExpr, *, valuefn: Callable[[SExpr], T]) -> list[T]:
    if not isinstance(expr, list):
        raise FromSExprError("expected list but found symbol")

    items: list[T] = []
    for v in expr:
        assert not v.key
        items.append(valuefn(v.value))

    return items


def to_options(expr: SExpr) -> list[Option[SExpr]]:
    if not isinstance(expr, list):
        raise FromSExprError(f"expected list but found {expr!r}")
    return expr


def to_values(expr: SExpr) -> list[SExpr]:
    if not isinstance(expr, list):
        raise FromSExprError(f"expected list but found {expr!r}")
    return [s.value for s in expr]


def to_tuple(expr: SExpr, *, handlers: Sequence[Callable[[SExpr], object]]) -> tuple:
    if not isinstance(expr, list):
        raise FromSExprError("expected list but found symbol")

    if len(expr) != len(handlers):
        raise FromSExprError(f"expected {len(handlers)} element but found {len(expr)}")

    items = []
    for e, h in zip(expr, handlers):
        assert not e.key
        items.append(h(e.value))

    return tuple(items)


def to_dict[K, V](
    sexpr: SExpr,
    *,
    keyfn: Callable[[str], K],
    valuefn: Callable[[SExpr], V],
) -> dict[K, V]:
    if not isinstance(sexpr, list):
        raise FromSExprError("expected list but found symbol")

    result: dict[K, V] = {}
    for opt in sexpr:
        key = keyfn(opt.key)
        assert key not in result
        result[key] = valuefn(opt.value)

    return result


def to_data(
    sexpr: SExpr,
) -> tuple[str, list[SExpr], dict[str, SExpr]]:
    if not isinstance(sexpr, list) or len(sexpr) == 0:
        raise FromSExprError(f"Expected list but got: {sexpr!r}")

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


BAD_SYMBOL = re.compile(r'[)(\n \t"]')


def escape(symbol: str) -> str:
    if symbol == "":
        return '""'

    if BAD_SYMBOL.search(symbol) is not None or symbol.startswith(":"):
        return f'"{symbol.replace('"', '""')}"'
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

        for e in expr:
            if e.key:
                if indent > 0:
                    spacing = "\n" + " " * (current + indent)
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


def tokenize(code):
    token_specification = [
        ("OPEN", r"\("),  # Open Paren
        ("CLOSE", r"\)"),  # Close Paren
        ("KEYWORD", r':[^)(\n \t"]+(?![^)(\n \t])'),
        ("ESCAPED_KEYWORD", r':"([^"]|"")*"'),
        ("SYMBOL", r'[^)(\n \t":][^)(\n \t"]*(?![^)(\n \t])'),
        ("ESCAPED_SYMBOL", r'"([^"]|"")*"'),
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
        before = self.head
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
            value = str(self.head.value)[1:-1].replace('""', '"')
            self.next()
            return value

        return None

    def keyword(self) -> str | None:
        if self.head.type == "KEYWORD":
            value = self.head.value
            self.next()
            return value[1:]

        if self.head.type == "ESCAPED_KEYWORD":
            value = str(self.head.value)[2:-1].replace('""', '"')
            self.next()
            return value

    def list(self) -> list[Option[SExpr]] | None:
        if self.head.type != "OPEN":
            return None

        self.next()

        output = []

        for i in range(2000):
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
