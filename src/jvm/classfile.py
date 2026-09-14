import re
from abc import ABC
from collections.abc import Callable
from dataclasses import dataclass
from typing import Self

import sexpr
from jvm.base import JSON, Encodable, json_dict, json_str
from jvm.type import ClassName, Type


@dataclass(frozen=True, order=True)
class Parameters:
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
    def decode(input: str) -> Self:
        params = []
        while input:
            (tt, input) = Type.decode(input)
            params.append(tt)

        return Parameters(tuple(params))

    @staticmethod
    def from_json(json: JSON, annotated=False) -> Self:
        if not isinstance(json, list):
            raise NotImplementedError(f"Cannot handle {json!r}")

        params: list[Type] = []
        for t in json:
            if annotated:
                t = json_dict(t)
                assert "annotations" in t, f"parameters should be annotated was: {t}"
                params.append(Type.from_json(t["type"]))
            else:
                params.append(Type.from_json(t))

        return Parameters(tuple(params))


METHOD_ID_RE_RAW = r"(?P<method_name>.*)\:\((?P<params>.*)\)(?P<return>.*)"
METHOD_ID_RE = re.compile(METHOD_ID_RE_RAW)


@dataclass(frozen=True, order=True)
class MethodID:
    """A method ID consist of a name, a list of parameter types and a return type."""

    name: str
    params: Parameters
    return_type: Type | None

    def __post_init__(self):
        if "." in self.name:
            raise ValueError(f"No '.' allowed in name: {self.name!r}")

    @staticmethod
    def decode(input: str):
        if (match := METHOD_ID_RE.match(input)) is None:
            raise ValueError(f"invalid method name: {input!r}")

        return_type = None
        if match["return"] != "V":
            return_type, more = Type.decode(match["return"])
            if more:
                raise ValueError(
                    f"could not decode method id, bad return type {match['return']!r}"
                )

        return MethodID(
            name=match["method_name"],
            params=Parameters.decode(match["params"]),
            return_type=return_type,
        )

    def encode(self) -> str:
        rt = self.return_type.encode() if self.return_type is not None else "V"
        return f"{self.name}:({self.params.encode()}){rt}"

    def __str__(self) -> str:
        return self.encode()


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

    def __sexpr__(self) -> str:
        return self.encode()


ABSOLUTE_RE = re.compile(r"(?P<class_name>.+)\.(?P<rest>.+)")


@dataclass(frozen=True)
class Absolute[T: Encodable](ABC):
    classname: ClassName
    extension: T

    def __post_init__(self):
        assert self.__class__ != Absolute, (
            "Do not use absolute directly, use AbsMethodId or AbsFieldID"
        )

    @classmethod
    def decode_with(cls, code: str, decode: Callable[[str], T]) -> "Self":
        if (match := ABSOLUTE_RE.match(code)) is None:
            raise ValueError(f"invalid absolute method name: {code!r}")

        return cls(ClassName.decode(match["class_name"]), decode(match["rest"]))

    def encode(self) -> str:
        return f"{self.classname.encode()}.{self.extension.encode()}"

    def __str__(self):
        return self.encode()


ParameterType = Parameters


@dataclass(frozen=True, order=True)
class AbsMethodID(Absolute[MethodID]):
    @classmethod
    def decode(cls, code: str) -> Self:
        return cls.decode_with(code, MethodID.decode)

    @property
    def methodid(self):
        return self.extension

    @classmethod
    def from_json(cls, json: JSON) -> "Self":
        if not isinstance(json, dict):
            raise NotImplementedError(f"Cannot handle {json!r}")

        return cls(
            classname=ClassName.from_slashed(json_str(json_dict(json["ref"])["name"])),
            extension=MethodID(
                name=json_str(json["name"]),
                params=Parameters.from_json(json["args"]),
                return_type=(
                    Type.from_json(json["returns"])
                    if json["returns"] is not None
                    else None
                ),
            ),
        )

    def __sexpr__(self) -> sexpr.SExpr:
        return self.encode()

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> Self:
        return cls.decode(sexpr.to_str(expr))


@dataclass(frozen=True, order=True)
class AbsFieldID(Absolute[FieldID]):
    @classmethod
    def decode(cls, code: str) -> "Self":
        return cls.decode_with(code, FieldID.decode)

    @property
    def fieldid(self):
        return self.extension

    def __sexpr__(self) -> sexpr.SExpr:
        return self.encode()

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> Self:
        return cls.decode(sexpr.to_str(expr))
