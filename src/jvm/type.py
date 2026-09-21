from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import total_ordering
from typing import ClassVar, Self

import sexpr
from jvm.base import *
from sexpr import SExpr


@total_ordering
class Type(ABC):
    """A jvm type"""

    @abstractmethod
    def encode(self) -> str: ...

    @abstractmethod
    def math(self) -> str: ...

    @abstractmethod
    def __sexpr__(self) -> SExpr: ...

    def is_stacktype(self) -> bool:
        return False

    @staticmethod
    def decode(code: str) -> "Type":
        ex, rem = Type.decode_more(code)
        if rem != "":
            raise ValueError(f"Expected only one type, but got {rem!r}")
        return ex

    @staticmethod
    def decode_more(input) -> tuple["Type", str]:
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
                case "A":
                    r = Reference()
                case "L":
                    i += 1
                    start = i
                    while input[i] != ";":
                        i += 1
                    r = Object(ClassName.from_slashed(input[start:i]))
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
    def from_json(json: JSON) -> "Type":
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
                case "string":
                    return Object(ClassName("java.lang.String"))

        json = json_dict(json)

        if "base" in json:
            return Type.from_json(json["base"])
        if "kind" in json:
            match json["kind"]:
                case "array":
                    return Array(Type.from_json(json["type"]))
                case "class":
                    return Object(ClassName.from_slashed(json_str(json["name"])))
                case kind:
                    raise NotImplementedError(
                        f"Unknown kind {kind}, in Type.from_json: {json!r}"
                    )

        raise NotImplementedError(f"Type.from_json: {json!r}")

    def __str__(self) -> str:
        return self.encode()

    @classmethod
    def from_sexpr(cls, expr: SExpr) -> "Type":
        match expr:
            case "bool":
                return Boolean()
            case "int":
                return Int()
            case "char":
                return Char()
            case "double":
                return Double()
            case "long":
                return Long()
            case "float":
                return Float()
            case "ref":
                return Reference()

        if isinstance(expr, str):
            raise sexpr.FromSExprError(f"Could not parse expr {expr!r} as type")

        match expr[0].unitem():
            case "object":
                return Object(ClassName.from_sexpr(expr[1].unitem()))
            case "array":
                return Array(Type.from_sexpr(expr[1].unitem()))

        raise NotImplementedError(expr)


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

    def __new__(cls) -> "Self":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def encode(self):
        return "Z"

    def __sexpr__(self):
        return "bool"

    def math(self):
        return "bool"


@dataclass(frozen=True)
class Int(StackType):
    """
    A 32bit signed integer
    """

    _instance = None

    def __new__(cls) -> "Self":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def encode(self):
        return "I"

    def math(self):
        return "int"

    def __sexpr__(self):
        return "int"


@dataclass(frozen=True)
class Byte(Type):
    """
    An 8bit signed integer
    """

    _instance = None

    def __new__(cls) -> "Self":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def encode(self):
        return "B"

    def math(self):
        return "byte"

    def __sexpr__(self):
        return "byte"


@dataclass(frozen=True)
class Char(Type):
    """
    An 16bit character
    """

    _instance = None

    def __new__(cls) -> "Self":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def encode(self):
        return "C"

    def math(self):
        return "char"

    def __sexpr__(self):
        return "char"


@dataclass(frozen=True)
class Short(Type):
    """
    An 16bit signed integer
    """

    _instance = None

    def __new__(cls) -> "Self":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def encode(self):
        return "S"

    def math(self):
        return "short"

    def __sexpr__(self):
        return "short"


@dataclass(frozen=True, order=True)
class Reference(StackType):
    """An unknown reference"""

    _instance = None

    def __new__(cls) -> "Self":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def encode(self):
        return "A"

    def math(self):
        return "ref"

    def __sexpr__(self):
        return "ref"


@dataclass(frozen=True, order=True)
class Object(Type):
    """
    A reference to an object of an known class.
    """

    _instance: ClassVar = {}

    def __new__(cls, subtype) -> "Self":
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

    def __sexpr__(self):
        return sexpr.values(["object", self.name])


@dataclass(frozen=True, order=True)
class Array(Type):
    """
    A reference to an array of known type
    """

    _instance: ClassVar = {}

    def __new__(cls, subtype) -> "Self":
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

    def __sexpr__(self) -> sexpr.SExpr:
        return sexpr.values(["array", self.contains])


@dataclass(frozen=True)
class Long(StackType):
    """
    A 64bit signed integer
    """

    _instance = None

    def __new__(cls) -> "Self":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def encode(self):
        return "J"  # J is used for long in JVM

    def math(self):
        return "long"

    def __sexpr__(self):
        return "long"


@dataclass(frozen=True)
class Float(StackType):
    """
    A 32bit floating point number
    """

    _instance = None

    def __new__(cls) -> "Self":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def encode(self):
        return "F"

    def math(self):
        return "float"

    def __sexpr__(self):
        return "float"


@dataclass(frozen=True)
class Double(StackType):
    """
    A 64bit floating point number
    """

    _instance = None

    def __new__(cls) -> "Self":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def encode(self):
        return "D"

    def math(self):
        return "double"

    def __sexpr__(self):
        return "double"
