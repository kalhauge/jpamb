"""
jvm.base

This module provides primitives to talk about the contents of java bytefiles,
as well as names and types.

It is recommended to import this module qualified

import jvm

"""

from dataclasses import dataclass
from typing import Protocol, Self

import sexpr


class Encodable(Protocol):
    def encode(self) -> str: ...


type JSON = list[JSON] | dict[str, JSON] | str | int | None | float


def json_str(json: JSON) -> str:
    if not isinstance(json, str):
        raise NotImplementedError(f"Cannot handle {json!r}")
    return json


def json_dict(json: JSON) -> dict[str, JSON]:
    if not isinstance(json, dict):
        raise NotImplementedError(f"Cannot handle {json!r}")
    return json


@dataclass(frozen=True, order=True)
class ClassName:
    """The name of a class, inner classes must use the $ syntax"""

    _as_string: str

    def __post_init__(self):
        if "/" in self._as_string:
            raise ValueError(f"Use '.' as a seperator in {self._as_string!r}")

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

    def slashed(self) -> str:
        return "/".join(self.parts)

    @classmethod
    def from_slashed(cls, code: str) -> Self:
        return cls.from_parts(*code.split("/"))

    def dotted(self) -> str:
        return self._as_string

    def __str__(self) -> str:
        return self.dotted()

    def __repr__(self) -> str:
        return f"ClassName({self.dotted()!r})"

    @classmethod
    def decode(cls, code: str) -> Self:
        return cls(code)

    def encode(self) -> str:
        return self._as_string

    @classmethod
    def from_parts(cls, *args: str) -> Self:
        return cls(".".join(args))

    def __sexpr__(self) -> sexpr.SExpr:
        return sexpr.sexpr(self.encode())

    @classmethod
    def from_sexpr(cls, exp: sexpr.SExpr) -> Self:
        return cls.decode(sexpr.to_str(exp))
