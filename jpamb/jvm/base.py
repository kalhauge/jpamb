"""
jpamb.jvm.base

This module provides primitives to talk about the contents of java bytefiles,
as well as names and types.

It is recommended to import this module qualified

from jpamb import jvm

"""

from collections import namedtuple
from functools import total_ordering
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Protocol, Self, Iterable, Optional, Iterator, NoReturn


@dataclass(frozen=True, order=True)
class ClassName:
    """The name of a class, inner classes must use the $ syntax"""

    _as_string: str

    @property
    def packages(self) -> list[str]:
        """Get a list of packages"""
        return self.parts[:-1]

    @property
    def name(self) -> str:
        """Get the unqualified name"""
        return self.parts[-1]

    @property
    def classname(self) -> Self:
        """return yourself"""
        return self

    @property
    def parts(self) -> list[str]:
        """Get the elements of the name"""
        return self._as_string.split(".")

    def encode(self) -> str:
        return self._as_string

    def slashed(self) -> str:
        return "/".join(self.parts)

    def dotted(self) -> str:
        return self._as_string

    def __str__(self) -> str:
        return self.dotted()

    def __repr__(self) -> str:
        return f"ClassName({self.dotted()!r})"

    @staticmethod
    def decode(input: str) -> "ClassName":
        return ClassName(input)

    @staticmethod
    def from_parts(*args: str) -> "ClassName":
        return ClassName(".".join(args))


@total_ordering
class Type(ABC):
    """A jvm type"""

    @abstractmethod
    def encode(self) -> str: ...

    @abstractmethod
    def math(self) -> str: ...

    def is_stacktype(self) -> bool:
        return False

    @staticmethod
    def decode(input) -> tuple["Type", str]:
        r, stack = None, []
        i = 0
        r = None
        while i < len(input):
            match input[i]:
                case "Z":
                    r = Boolean()
                case "I":
                    r = Int()
                case "B":
                    r = Byte()
                case "C":
                    r = Char()
                case "S":
                    r = Short()
                case "J":
                    r = Long()
                case "F":
                    r = Float()
                case "D":
                    r = Double()
                case "[":  # ]
                    stack.append(Array)
                    i += 1
                    continue
                case _:
                    raise ValueError(f"Unknown type {input[i]}")
            break
        else:
            raise ValueError(f"Could not decode {input}")

        assert r is not None

        for k in reversed(stack):
            r = k(r)

        return r, input[i + 1 :]

    def __lt__(self, other):
        return self.encode() <= other.encode()

    def __eq__(self, other):
        return self.encode() <= other.encode()

    @staticmethod
    def from_json(json: str) -> "Type":
        if isinstance(json, str):
            match json:
                case "integer":
                    return Int()
                case "int":
                    return Int()
                case "char":
                    return Char()
                case "short":
                    return Short()
                case "ref":
                    return Reference()
                case "boolean":
                    return Boolean()
        if "base" in json:
            return Type.from_json(json["base"])
        if "kind" in json:
            match json["kind"]:
                case "array":
                    return Array(Type.from_json(json["type"]))
                case kind:
                    raise NotImplementedError(
                        f"Unknown kind {kind}, in Type.from_json: {json!r}"
                    )

        raise NotImplementedError(f"Type.from_json: {json!r}")

    def __str__(self) -> str:
        return self.encode()


@dataclass(frozen=True)
class StackType(Type):

    def is_stacktype(self):
        return True


@dataclass(frozen=True)
class Boolean(Type):
    """
    A boolean
    """

    _instance = None

    def __new__(cls) -> "Boolean":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def encode(self):
        return "Z"

    def math(self):
        return "bool"


@dataclass(frozen=True)
class Int(StackType):
    """
    A 32bit signed integer
    """

    _instance = None

    def __new__(cls) -> "Int":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def encode(self):
        return "I"

    def math(self):
        return "int"


@dataclass(frozen=True)
class Byte(Type):
    """
    An 8bit signed integer
    """

    _instance = None

    def __new__(cls) -> "Byte":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def encode(self):
        return "B"

    def math(self):
        return "byte"


@dataclass(frozen=True)
class Char(Type):
    """
    An 16bit character
    """

    _instance = None

    def __new__(cls) -> "Char":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def encode(self):
        return "C"

    def math(self):
        return "char"


@dataclass(frozen=True)
class Short(Type):
    """
    An 16bit signed integer
    """

    _instance = None

    def __new__(cls) -> "Short":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def encode(self):
        return "S"

    def math(self):
        return "short"


@dataclass(frozen=True, order=True)
class Reference(StackType):
    """An unknown reference"""

    _instance = None

    def __new__(cls) -> "Reference":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def encode(self):
        return "A"

    def math(self):
        return "ref"


@dataclass(frozen=True, order=True)
class Object(Type):
    """
    A reference to an object of an known class.
    """

    _instance = dict()

    def __new__(cls, subtype) -> "Object":
        if subtype not in cls._instance:
            cls._instance[subtype] = super().__new__(cls)
        return cls._instance[subtype]

    name: ClassName

    def __post_init__(self):
        assert self.name is not None

    def encode(self):
        return "L" + self.name.slashed() + ";"  # ]

    def math(self):
        return f"object {self.name}"


@dataclass(frozen=True, order=True)
class Array(Type):
    """
    A reference to an array of known type
    """

    _instance = dict()

    def __new__(cls, subtype) -> "Array":
        if subtype not in cls._instance:
            cls._instance[subtype] = super().__new__(cls)
        return cls._instance[subtype]

    contains: Type

    def __post_init__(self):
        assert self.contains is not None

    def encode(self):
        return "[" + self.contains.encode()  # ]

    def math(self):
        return f"array {self.contains.math()}"


@dataclass(frozen=True)
class Long(StackType):
    """
    A 64bit signed integer
    """

    _instance = None

    def __new__(cls) -> "Long":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def encode(self):
        return "J"  # J is used for long in JVM

    def math(self):
        return "long"


@dataclass(frozen=True)
class Float(Type):
    """
    A 32bit floating point number
    """

    _instance = None

    def __new__(cls) -> "Float":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def encode(self):
        return "F"

    def math(self):
        return "float"


@dataclass(frozen=True)
class Double(StackType):
    """
    A 64bit floating point number
    """

    _instance = None

    def __new__(cls) -> "Double":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def encode(self):
        return "D"

    def math(self):
        return "double"


@dataclass(frozen=True, order=True)
class ParameterType:
    """A list of parameters types"""

    _elements: tuple[Type, ...]

    def __getitem__(self, index):
        return self._elements.__getitem__(index)

    def __len__(self):
        return self._elements.__len__()
    
    def __iter__(self):
        return self._elements.__iter__()

    def encode(self):
        return "".join(e.encode() for e in self._elements)

    @staticmethod
    def decode(input: str) -> "ParameterType":
        params = []
        while input:
            (tt, input) = Type.decode(input)
            params.append(tt)

        return ParameterType(tuple(params))

    @staticmethod
    def from_json(inputs: list[dict], annotated=False) -> "ParameterType":
        params: list[Type] = []
        for t in inputs:
            if annotated:
                assert "annotations" in t, f"parameters should be annotated was: {t}"
                params.append(Type.from_json(t["type"]))
            else:
                params.append(Type.from_json(t))

        return ParameterType(tuple(params))

    def math(self):
        return "double"


METHOD_ID_RE_RAW = r"(?P<method_name>.*)\:\((?P<params>.*)\)(?P<return>.*)"
METHOD_ID_RE = re.compile(METHOD_ID_RE_RAW)


@dataclass(frozen=True, order=True)
class MethodID:
    """A method ID consist of a name, a list of parameter types and a return type."""

    name: str
    params: ParameterType
    return_type: Type | None

    @staticmethod
    def decode(input: str):
        if (match := METHOD_ID_RE.match(input)) is None:
            raise ValueError("invalid method name: %r", input)

        return_type = None
        if match["return"] != "V":
            return_type, more = Type.decode(match["return"])
            if more:
                raise ValueError(
                    f"could not decode method id, bad return type {match['return']!r}"
                )

        return MethodID(
            name=match["method_name"],
            params=ParameterType.decode(match["params"]),
            return_type=return_type,
        )

    def encode(self) -> str:
        rt = self.return_type.encode() if self.return_type is not None else "V"
        return f"{self.name}:({self.params.encode()}){rt}"


@dataclass(frozen=True, order=True)
class FieldID:
    """A field ID consists of a name and a type."""

    name: str
    type: Type

    def encode(self) -> str:
        return f"{self.name}:{self.type.encode()}"

    @staticmethod
    def decode(input: str) -> "FieldID":
        if ":" not in input:
            raise ValueError(f"invalid field id format: {input}")
        name, type_str = input.split(":", 1)
        type_obj, remaining = Type.decode(type_str)
        if remaining:
            raise ValueError(f"extra characters in field type: {remaining}")
        return FieldID(name=name, type=type_obj)

    def __str__(self) -> str:
        return self.encode()


class Encodable(Protocol):
    def encode(self) -> str: ...


ABSOLUTE_RE = re.compile(r"(?P<class_name>.+)\.(?P<rest>.*)")


@dataclass(frozen=True, order=True)
class Absolute[T: Encodable](ABC):
    classname: ClassName
    extension: T

    def __post_init__(self):
        assert (
            self.__class__ != Absolute
        ), "Do not use absolute directly, use AbsMethodId or AbsFieldID"

    @classmethod
    def decode(cls, input, decode: Callable[[str], T]) -> "Self":
        if (match := ABSOLUTE_RE.match(input)) is None:
            raise ValueError("invalid absolute method name: %r", input)

        return cls(ClassName.decode(match["class_name"]), decode(match["rest"]))

    def encode(self) -> str:
        return f"{self.classname.encode()}.{self.extension.encode()}"

    def __str__(self):
        return self.encode()


class AbsMethodID(Absolute[MethodID]):

    @classmethod
    def decode(cls, input) -> "Self":
        return super().decode(input, MethodID.decode)

    @property
    def methodid(self):
        return self.extension

    @classmethod
    def from_json(cls, json: dict) -> "Self":
        return cls(
            classname=ClassName.decode(json["ref"]["name"]),
            extension=MethodID(
                name=json["name"],
                params=ParameterType.from_json(json["args"]),
                return_type=(
                    Type.from_json(json["returns"])
                    if json["returns"] is not None
                    else None
                ),
            ),
        )


class AbsFieldID(Absolute[FieldID]):

    @classmethod
    def decode(cls, input) -> "Self":
        return super().decode(input, FieldID.decode)

    @property
    def fieldid(self):
        return self.extension


@dataclass(frozen=True, order=True)
class Value:
    type: Type
    value: object

    @staticmethod
    def decode_many(input) -> list["Value"]:
        vp = ValueParser(input)
        values = vp.parse_comma_seperated_values()
        vp.eof()
        return values

    @staticmethod
    def decode(input) -> list["Value"]:
        vp = ValueParser(input)
        value = vp.parse_comma_seperated_values()
        vp.eof()
        return value

    def encode(self) -> str:
        match self.type:
            case Boolean():
                return "true" if self.value else "false"
            case Int():
                return str(self.value)
            case Char():
                return f"'{self.value}'"
            case Array(content):
                assert isinstance(self.value, Iterable)
                match content:
                    case Int():
                        ints = ", ".join(map(str, self.value))
                        return f"[I:{ints}]"
                    case Char():
                        chars = ", ".join(map(lambda a: f"'{a}'", self.value))
                        return f"[C:{chars}]"
                    case _:
                        raise NotImplementedError()
            case _:
                raise NotImplementedError(f"Cannot encode {self.type}")

    @classmethod
    def int(cls, n: int) -> Self:
        return cls(Int(), n)

    @classmethod
    def boolean(cls, n: bool) -> Self:
        return cls(Boolean(), n)

    @classmethod
    def char(cls, char: str) -> Self:
        assert len(char) == 1, f"string should be exactly one char, was {char!r}"
        return cls(Char(), char)

    @classmethod
    def array(cls, type: Type, content: Iterable) -> Self:
        return cls(Array(type), tuple(content))

    @classmethod
    def from_json(cls, json: dict | None) -> Self:
        if json is None:
            return cls(Reference(), None)
        try:
            type = Type.from_json(json["type"])
        except NotImplementedError as e:
            raise NotImplementedError(f"Cannot handle {json!r}") from e

        return cls(type, json["value"])

    def __str__(self) -> str:
        return self.math()

    def math(self) -> str:
        return f"({self.type.math()} {self.value})"


@dataclass
class ValueParser:
    Token = namedtuple("Token", "kind value")

    input: str
    head: Optional["ValueParser.Token"]
    _tokens: Iterator["ValueParser.Token"]

    def __init__(self, input) -> None:
        self.input = input
        self._tokens = ValueParser.tokenize(input)
        self.next()

    @staticmethod
    def tokenize(string):
        token_specification = [
            ("OPEN_ARRAY", r"\[[IC]:"),
            ("CLOSE_ARRAY", r"\]"),
            ("INT", r"-?\d+"),
            ("BOOL", r"true|false"),
            ("CHAR", r"'[^']'"),
            ("COMMA", r","),
            ("SKIP", r"[ \t]+"),
        ]
        tok_regex = "|".join(f"(?P<{n}>{m})" for n, m in token_specification)

        for m in re.finditer(tok_regex, string):
            kind, value = m.lastgroup, m.group()
            if kind == "SKIP":
                continue
            yield ValueParser.Token(kind, value)

    @staticmethod
    def parse(string) -> list[Value]:
        return ValueParser(string).parse_comma_seperated_values()

    def next(self):
        try:
            self.head = next(self._tokens)
        except StopIteration:
            self.head = None

    def expected(self, expected) -> NoReturn:
        raise ValueError(f"Expected {expected} but got {self.head} in {self.input}")

    def expect(self, expect) -> Token:
        head = self.head
        if head is None:
            self.expected(repr(expect))
        elif expect != head.kind:
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
                return Value.int(self.parse_int())
            case "CHAR":
                return Value.char(self.parse_char())
            case "BOOL":
                return Value.boolean(self.parse_bool())
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

    def parse_array(self):
        key = self.expect("OPEN_ARRAY")
        if key.value == "[I:":  # ]
            type = Array(Int())
            parser = self.parse_int
        elif key.value == "[C:":  # ]
            type = Array(Char())
            parser = self.parse_char
        else:
            self.expected("int or char array")

        inputs = self.parse_comma_seperated_values(parser, "CLOSE_ARRAY")

        self.expect("CLOSE_ARRAY")

        return Value(type, tuple(inputs))

    def parse_comma_seperated_values(self, parser=None, end_by=None):
        if self.head is None:
            return []

        if end_by is not None and self.head.kind == end_by:
            return []

        parser = parser or self.parse_value
        inputs = [parser()]

        while self.head and self.head.kind == "COMMA":
            self.next()
            inputs.append(parser())

        return inputs
