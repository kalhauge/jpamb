"""
jpamb.jvm.opcode

This module contains the decompilation of the output of jvm2json
into a python structure, as well documentation and semantics for
each instruction.

"""

from dataclasses import dataclass, fields
from abc import ABC, abstractmethod
from typing import Self

import enum
import sys
from loguru import logger
from jpamb.jvm import base as jvm

logger.add(sys.stderr, format="[{level}] {message}")


@dataclass(frozen=True, order=True)
class Opcode(ABC):
    """An opcode, as parsed from the jvm2json output."""

    offset: int

    def __post_init__(self):
        for f in fields(self):
            v = getattr(self, f.name)
            assert isinstance(
                v, f.type
            ), f"Expected {f.name!r} to be type {f.type}, but was {v!r}, in {self!r}"

    @classmethod
    def from_json(cls, json: dict) -> "Opcode":
        match json["opr"]:
            case "put":
                opr = Put
            case "push":
                opr = Push
            case "newarray":
                opr = NewArray
            case "dup":
                opr = Dup
            case "array_store":
                opr = ArrayStore
            case "array_load":
                opr = ArrayLoad
            case "binary":
                opr = Binary
            case "store":
                opr = Store
            case "load":
                opr = Load
            case "arraylength":
                opr = ArrayLength
            case "if":
                opr = If
            case "get":
                opr = Get
            case "ifz":
                opr = Ifz
            case "cast":
                opr = Cast
            case "new":
                opr = New
            case "throw":
                opr = Throw
            case "incr":
                opr = Incr
            case "goto":
                opr = Goto
            case "return":
                opr = Return
            case "invoke":
                match json["access"]:
                    case "virtual":
                        opr = InvokeVirtual
                    case "static":
                        opr = InvokeStatic
                    case "interface":
                        opr = InvokeInterface
                    case "special":
                        opr = InvokeSpecial
                    case access:
                        raise NotImplementedError(
                            f"Unhandled invoke access {access!r} (implement yourself)"
                        )
            case opr:
                raise NotImplementedError(
                    f"Unhandled opcode {opr!r} (implement yourself)"
                )
        try:
            return opr.from_json(json)
        except NotImplementedError as e:
            raise NotImplementedError(f"Unhandled opcode {json!r}") from e

    def help(self):
        logger.warning("Instructions can be found at: " + self.url())
        if self.semantics():
            logger.debug(f"Semantics:\n {self.semantics()}")

    def real(self) -> str:
        """return the real opcode, as documented in the jvm spec."""
        raise NotImplementedError(f"Unhandled real {self!r}")

    @abstractmethod
    def mnemonic(self) -> str: ...

    def url(self) -> str:
        return (
            "https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5."
            + self.mnemonic()
        )

@dataclass(frozen=True, order=True)
class Put(Opcode):
    """The put opcode for setting instance fields"""
    static: bool
    field: jvm.AbsFieldID

    @classmethod
    def from_json(cls, json: dict) -> "Opcode":
        # Construct field object from the json data
        field = jvm.AbsFieldID(
            classname=jvm.ClassName.decode(json["field"]["class"]),
            extension=jvm.FieldID(
                name=json["field"]["name"],
                type=jvm.Type.from_json(json["field"]["type"]),
            ),
        )

        return cls(offset=json["offset"], static=json["static"], field=field)


    def real(self) -> str:
        access = "static" if self.static else "field"
        return f"put{access} {self.field}"

    def semantics(self) -> str | None:
        return None

    def mnemonic(self) -> str:
        return "putfield" if not self.static else "putstatic"

@dataclass(frozen=True, order=True)
class Push(Opcode):
    """The push opcode"""

    value: jvm.Value

    @classmethod
    def from_json(cls, json: dict) -> Opcode:
        return cls(
            offset=json["offset"],
            value=jvm.Value.from_json(json["value"]),
        )

    def real(self) -> str:
        match self.value.type:
            case jvm.Int():
                match self.value.value:
                    case -1:
                        return "iconst_m1"
                    case 0:
                        return "iconst_0"
                    case 1:
                        return "iconst_1"
                    case 2:
                        return "iconst_2"
                    case 3:
                        return "iconst_3"
                    case 4:
                        return "iconst_4"
                    case 5:
                        return "iconst_5"
                return f"ldc [{self.value.value}]"
            case jvm.Reference():
                assert self.value.value is None, f"what is {self.value}"
                return "aconst_null"

        raise NotImplementedError(f"Unhandled {self!r}")

    def semantics(self) -> str | None:
        semantics = """
        bc[i].opr = 'push'
        bc[i].value = v
        -------------------------[push]
        bc |- (i, s) -> (i+1, s + [v])
        """

        return None

    def mnemonic(self) -> str:
        match self.value.type:
            case jvm.Int():
                if -2 < self.value.value and self.value.value < 5:
                    return "iconst_i"
                else:
                    return "ldc"
            case jvm.Reference():
                return "aconst_null"

        raise NotImplementedError(f"Unhandled {self!r}")

    def __str__(self):
        return f"push:{self.value.type} {self.value.value}"


@dataclass(frozen=True, order=True)
class NewArray(Opcode):
    """The new array opcode"""

    type: jvm.Type
    dim: int

    @classmethod
    def from_json(cls, json: dict) -> Opcode:
        return cls(
            offset=json["offset"],
            type=jvm.Type.from_json(json["type"]),
            dim=json["dim"],
        )

    def real(self) -> str:
        if self.dim == 1:
            return f"newarray {self.type}"
        else:
            return f"multianewarray {self.type} {self.dim}"

    def semantics(self) -> str | None:
        if self.dim == 1:
            return "newarray"
        else:
            return "multianewarray"

        return None

    def mnemonic(self) -> str:
        if self.dim == 1:
            return "newarray"
        else:
            return "multianewarray"

    def __str__(self):
        return f"newarray[{self.dim}D] {self.type}"


@dataclass(frozen=True, order=True)
class Dup(Opcode):
    """The dublicate the stack opcode"""

    words: int

    @classmethod
    def from_json(cls, json: dict) -> Opcode:
        return cls(
            offset=json["offset"],
            words=json["words"],
        )

    def real(self) -> str:
        if self.words == 1:
            return "dup"
        return super().real()

    def semantics(self) -> str | None:
        semantic = """
        bc[i].opr = 'dup'
        bc[i].words = 1
        -------------------------[dup1]
        (i, s + [v]) -> (i+1, s + [v, v])
        """

        return semantic

    def mnemonic(self) -> str:
        return self.real()

    def __str__(self):
        return f"dup {self.words}"


@dataclass(frozen=True, order=True)
class ArrayStore(Opcode):
    """The Array Store command that stores a value in the array."""

    type: jvm.Type

    @classmethod
    def from_json(cls, json: dict) -> Opcode:
        return cls(
            offset=json["offset"],
            type=jvm.Type.from_json(json["type"]),
        )

    def real(self) -> str:
        match self.type:
            case jvm.Reference():
                return "aastore"
            case jvm.Int():
                return "iastore"

        return super().real()

    def semantics(self) -> str | None:
        return None

    def mnemonic(self) -> str:
        return self.real()

    def __str__(self):
        return f"array_store {self.type}"


@dataclass(frozen=True, order=True)
class Cast(Opcode):
    """Cast one type to another"""

    from_: jvm.Type
    to_: jvm.Type

    @classmethod
    def from_json(cls, json: dict) -> Opcode:
        return cls(
            offset=json["offset"],
            from_=jvm.Type.from_json(json["from"]),
            to_=jvm.Type.from_json(json["to"]),
        )

    def real(self) -> str:
        match self.from_:
            case jvm.Int():
                match self.to_:
                    case jvm.Short():
                        return "i2s"

        return super().real()

    def semantics(self) -> str | None:
        return None

    def mnemonic(self) -> str:
        return self.real()

    def __str__(self):
        return f"cast {self.from_} {self.to_}"


@dataclass(frozen=True, order=True)
class ArrayLoad(Opcode):
    """The Array Load command that load a value from the array."""

    type: jvm.Type

    @classmethod
    def from_json(cls, json: dict) -> Opcode:
        return cls(
            offset=json["offset"],
            type=jvm.Type.from_json(json["type"]),
        )

    def real(self) -> str:
        match self.type:
            case jvm.Reference():
                return "aaload"
            case jvm.Int():
                return "iaload"
            case jvm.Char():
                return "caload"

        return super().real()

    def semantics(self) -> str | None:
        return None

    def mnemonic(self) -> str:
        return self.real()

    def __str__(self):
        return f"array_load:{self.type}"


@dataclass(frozen=True, order=True)
class ArrayLength(Opcode):
    """
    arraylength:
     - Takes an array reference from the operand stack
     - Pushes the length of the array onto the operand stack
     - Throws NullPointerException if the array reference is null
    """

    @classmethod
    def from_json(cls, json: dict) -> "Opcode":
        return cls(
            offset=json["offset"],
        )

    def real(self) -> str:
        return "arraylength"

    def semantics(self) -> str | None:
        semantics = """
        bc[i].opr = 'arraylength'
        -------------------------[arraylength]
        bc |- (i, s + [arrayref]) -> (i+1, s + [length])
        """

        return None

    def mnemonic(self) -> str:
        return self.real()

    def __str__(self):
        return "arraylength"


@dataclass(frozen=True, order=True)  # make it work for
class InvokeVirtual(Opcode):
    """The invoke virtual opcode for calling instance methods"""

    method: jvm.AbsMethodID

    @classmethod
    def from_json(cls, json: dict) -> "Opcode":
        assert json["opr"] == "invoke" and json["access"] == "virtual"
        return cls(
            offset=json["offset"],
            method=jvm.AbsMethodID.from_json(json["method"]),
        )

    def real(self) -> str:
        return f"invokevirtual {self.method.dashed()}"

    def semantics(self) -> str | None:
        semantics = """
        bc[i].opr = 'invoke'
        bc[i].access = 'virtual'
        bc[i].method = m
        -------------------------[invokevirtual]
        bc |- (i, s + args) -> (i+1, s + [result])
        """

        return None

    def mnemonic(self) -> str:
        return "invokevirtual"

    def __str__(self):
        return f"invoke virtual {self.method}"


@dataclass(frozen=True, order=True)
class InvokeStatic(Opcode):
    """The invoke static opcode for calling static methods"""

    method: jvm.AbsMethodID

    @classmethod
    def from_json(cls, json: dict) -> "Opcode":
        assert json["opr"] == "invoke" and json["access"] == "static"
        return cls(
            offset=json["offset"],
            method=jvm.AbsMethodID.from_json(json["method"]),
        )

    def real(self) -> str:
        return f"invokestatic {self.method}"

    def semantics(self) -> str | None:
        semantics = """
        bc[i].opr = 'invoke'
        bc[i].access = 'static'
        bc[i].method = m
        -------------------------[invokestatic]
        bc |- (i, s + args) -> (i+1, s + [result])
        """

        return None

    def mnemonic(self) -> str:
        return "invokestatic"

    def __str__(self):
        return f"invoke static {self.method}"


@dataclass(frozen=True, order=True)
class InvokeInterface(Opcode):
    """The invoke interface opcode for calling interface methods"""

    method: jvm.AbsMethodID
    stack_size: int

    @classmethod
    def from_json(cls, json: dict) -> "Opcode":
        assert json["opr"] == "invoke" and json["access"] == "interface"
        return cls(
            offset=json["offset"],
            method=jvm.AbsMethodID.from_json(json["method"]),
            stack_size=json["stack_size"],
        )

    def real(self) -> str:
        return f"invokeinterface {self.method} {self.stack_size}"

    def semantics(self) -> str | None:
        semantics = """
        bc[i].opr = 'invoke'
        bc[i].access = 'interface'
        bc[i].method = m
        bc[i].stack_size = n
        -------------------------[invokeinterface]
        bc |- (i, s + args) -> (i+1, s + [result])
        """

        return None

    def mnemonic(self) -> str:
        return "invokeinterface"

    def __str__(self):
        return f"invoke interface {self.method} (stack_size={self.stack_size})"


@dataclass(frozen=True, order=True)
class InvokeSpecial(Opcode):
    """The invoke special opcode for calling constructors, private methods,
    and superclass methods.

    According to the JVM spec, invokespecial:
    - Invokes instance method specially (non-virtual dispatch)
    - Used for:
      * Instance initialization methods (<init>)
      * Private methods
      * Methods of a superclass
    - The first argument must be an instance of current class or a subclass
    """

    method: jvm.AbsMethodID
    is_interface: bool  # Whether the method is from an interface

    @classmethod
    def from_json(cls, json: dict) -> "Opcode":
        assert json["opr"] == "invoke" and json["access"] == "special"

        return cls(
            offset=json["offset"],
            method=jvm.AbsMethodID.from_json(json["method"]),
            is_interface=json["method"]["is_interface"],
        )

    def real(self) -> str:
        return f"invokespecial {self.method}"

    def semantics(self) -> str | None:
        semantics = """
        bc[i].opr = 'invoke'
        bc[i].access = 'special'
        bc[i].method = m
        -------------------------[invokespecial]
        bc |- (i, s + [objectref, args...]) -> (i+1, s + [result])
        where objectref must be an instance of current class or subclass
        """

        return None

    def mnemonic(self) -> str:
        return "invokespecial"

    def __str__(self):
        interface_str = " interface" if self.is_interface else ""
        return f"invoke special{interface_str} {self.method}"


@dataclass(frozen=True, order=True)
class Store(Opcode):
    """The store opcode that stores values to local variables"""

    type: jvm.Type
    index: int  # Adding the index field from CODEC.txt

    @classmethod
    def from_json(cls, json: dict) -> "Opcode":
        return cls(
            offset=json["offset"],
            type=jvm.Type.from_json(json["type"]),
            index=json["index"],
        )

    def real(self) -> str:
        # Handle reference type specifically since we see it in the error
        if isinstance(self.type, jvm.Reference):
            return f"astore_{self.index}" if self.index < 4 else f"astore {self.index}"
        # Handle integer type
        elif isinstance(self.type, jvm.Int):
            return f"istore_{self.index}" if self.index < 4 else f"istore {self.index}"
        return super().real()

    def semantics(self) -> str | None:
        return None

    def mnemonic(self) -> str:
        if isinstance(self.type, jvm.Reference):
            return "astore_n" if self.index < 4 else "astore"
        # Handle integer type
        elif isinstance(self.type, jvm.Int):
            return "istore_n" if self.index < 4 else "istore"
        return ""

        return self.real()

    def __str__(self):
        return f"store:{self.type} {self.index}"


class BinaryOpr(enum.Enum):
    Add = enum.auto()
    Sub = enum.auto()
    Mul = enum.auto()
    Div = enum.auto()
    Rem = enum.auto()

    @staticmethod
    def from_json(json: str) -> "BinaryOpr":
        match json:
            case "add":
                return BinaryOpr.Add
            case "sub":
                return BinaryOpr.Sub
            case "mul":
                return BinaryOpr.Mul
            case "div":
                return BinaryOpr.Div
            case "rem":
                return BinaryOpr.Rem
            case _:
                raise NotImplementedError()

    def __str__(self):
        return self.name.lower()


@dataclass(frozen=True, order=True)
class Binary(Opcode):
    type: jvm.Type
    operant: BinaryOpr

    @classmethod
    def from_json(cls, json: dict) -> "Opcode":
        return cls(
            offset=json["offset"],
            type=jvm.Type.from_json(json["type"]),
            operant=BinaryOpr.from_json(json["operant"]),
        )

    def __str__(self):
        return f"binary:{self.type} {self.operant}"

    def real(self) -> str:
        match (self.type, self.operant):
            case (jvm.Int(), BinaryOpr.Add):
                return "iadd"
            case (jvm.Int(), BinaryOpr.Rem):
                return "irem"
            case (jvm.Int(), BinaryOpr.Div):
                return "idiv"
            case (jvm.Int(), BinaryOpr.Mul):
                return "imul"
            case (jvm.Int(), BinaryOpr.Sub):
                return "isub"
        raise NotImplementedError(f"Unhandled real {self!r}")

    def semantics(self) -> str | None:
        return None

    def mnemonic(self) -> str:
        return self.real()


@dataclass(frozen=True, order=True)
class Load(Opcode):
    """The load opcode that loads values from local variables"""

    type: jvm.Type
    index: int

    @classmethod
    def from_json(cls, json: dict) -> "Opcode":
        return cls(
            offset=json["offset"],
            type=jvm.Type.from_json(json["type"]),
            index=json["index"],
        )

    def real(self) -> str:
        # Handle reference type
        if isinstance(self.type, jvm.Reference):
            return f"aload_{self.index}" if self.index < 4 else f"aload {self.index}"
        # Handle integer type
        elif isinstance(self.type, jvm.Int):
            return f"iload_{self.index}" if self.index < 4 else f"iload {self.index}"
        return super().real()

    def semantics(self) -> str | None:
        return None

    def mnemonic(self) -> str:
        if isinstance(self.type, jvm.Reference):
            return "aload_n" if self.index < 4 else "aload"
        # Handle integer type
        elif isinstance(self.type, jvm.Int):
            return "iload_n" if self.index < 4 else "iload"
        return ""

    def __str__(self):
        return f"load:{self.type} {self.index}"


@dataclass(frozen=True, order=True)
class If(Opcode):
    """The if opcode that performs conditional jumps based on comparison of two values.

    According to the JVM spec, if instructions:
    - Pop two values from the operand stack
    - Compare them according to the condition
    - Jump to target instruction if condition is true
    - Continue to next instruction if condition is false

    There are two main categories:
    1. Integer comparisons (if_icmp*)
    2. Reference comparisons (if_acmp*)
    """

    condition: str  # One of the CmpOpr values
    target: int  # Jump target offset

    @classmethod
    def from_json(cls, json: dict) -> "Opcode":
        return cls(
            offset=json["offset"], condition=json["condition"], target=json["target"]
        )

    def real(self) -> str:
        # Map our condition to actual JVM instruction
        # For integer comparisons
        int_cmp_map = {
            "eq": "if_icmpeq",
            "ne": "if_icmpne",
            "lt": "if_icmplt",
            "ge": "if_icmpge",
            "gt": "if_icmpgt",
            "le": "if_icmple",
        }

        # For reference comparisons
        ref_cmp_map = {"is": "if_acmpeq", "isnot": "if_acmpne"}

        if self.condition in int_cmp_map:
            return f"{int_cmp_map[self.condition]} {self.target}"
        elif self.condition in ref_cmp_map:
            return f"{ref_cmp_map[self.condition]} {self.target}"
        else:
            raise ValueError(f"Unknown comparison condition: {self.condition}")

    def semantics(self) -> str | None:
        semantics = """
        bc[i].opr = 'if'
        bc[i].condition = cond
        bc[i].target = t
        -------------------------[if]
        bc |- (i, s + [value1, value2]) -> (t, s) if condition is true
        bc |- (i, s + [value1, value2]) -> (i+1, s) if condition is false
        """

        return None

    def mnemonic(self) -> str:
        return "if_icmp_cond"

    def __str__(self):
        return f"if {self.condition} {self.target}"


@dataclass(frozen=True, order=True)
class Get(Opcode):
    """The get opcode that retrieves field values (static or instance).

    According to the JVM spec:
    - For non-static fields (getfield):
      * Pops an object reference from the stack
      * Pushes the value of the specified field onto the stack
      * Throws NullPointerException if object reference is null

    - For static fields (getstatic):
      * Pushes the value of the specified static field onto the stack
      * May trigger class initialization if not yet initialized
    """

    static: bool
    field: jvm.AbsFieldID  # We need to add FieldID to base.py

    @classmethod
    def from_json(cls, json: dict) -> "Opcode":
        # Construct field object from the json data
        field = jvm.AbsFieldID(
            classname=jvm.ClassName.decode(json["field"]["class"]),
            extension=jvm.FieldID(
                name=json["field"]["name"],
                type=jvm.Type.from_json(json["field"]["type"]),
            ),
        )

        return cls(offset=json["offset"], static=json["static"], field=field)

    def real(self) -> str:
        opcode = "getstatic" if self.static else "getfield"
        return f"{opcode} {self.field}"

    def semantics(self) -> str | None:
        semantics = """
        bc[i].opr = 'get'
        bc[i].static = false
        bc[i].field = f
        -------------------------[getfield]
        bc |- (i, s + [objectref]) -> (i+1, s + [value])

        bc[i].opr = 'get'
        bc[i].static = true
        bc[i].field = f
        -------------------------[getstatic]
        bc |- (i, s) -> (i+1, s + [value])
        """

        return None

    def mnemonic(self) -> str:
        mnemonic = "getstatic" if self.static else "getfield"
        return mnemonic

    def __str__(self):
        kind = "static" if self.static else "field"
        return f"get {kind} {self.field}"


@dataclass(frozen=True, order=True)
class Ifz(Opcode):
    """The ifz opcode that performs conditional jumps based on comparison with zero/null.

    According to the JVM spec, ifz instructions:
    - Pop one value from the operand stack
    - Compare it against zero (for integers) or null (for references)
    - Jump to target instruction if condition is true
    - Continue to next instruction if condition is false

    There are two categories:
    1. Integer comparisons against zero (ifeq, ifne, etc.)
    2. Reference comparisons against null (ifnull, ifnonnull)
    """

    condition: str  # One of the CmpOpr values
    target: int  # Jump target offset

    @classmethod
    def from_json(cls, json: dict) -> "Opcode":
        return cls(
            offset=json["offset"], condition=json["condition"], target=json["target"]
        )

    def real(self) -> str:
        # Map our condition to actual JVM instruction
        # For integer comparisons against zero
        int_cmp_map = {
            "eq": "ifeq",  # value == 0
            "ne": "ifne",  # value != 0
            "lt": "iflt",  # value < 0
            "ge": "ifge",  # value >= 0
            "gt": "ifgt",  # value > 0
            "le": "ifle",  # value <= 0
        }

        # For reference comparisons against null
        ref_cmp_map = {
            "is": "ifnull",  # value == null
            "isnot": "ifnonnull",  # value != null
        }

        if self.condition in int_cmp_map:
            return f"{int_cmp_map[self.condition]} {self.target}"
        elif self.condition in ref_cmp_map:
            return f"{ref_cmp_map[self.condition]} {self.target}"
        else:
            raise ValueError(f"Unknown comparison condition: {self.condition}")

    def semantics(self) -> str | None:
        semantics = """
        bc[i].opr = 'ifz'
        bc[i].condition = cond
        bc[i].target = t
        -------------------------[ifz]
        bc |- (i, s + [value]) -> (t, s) if condition against zero/null is true
        bc |- (i, s + [value]) -> (i+1, s) if condition against zero/null is false
        """

        return None

    def mnemonic(self) -> str:
        return "if_cond"

    def __str__(self):
        return f"ifz {self.condition} {self.target}"


@dataclass(frozen=True, order=True)
class New(Opcode):
    """The new opcode that creates a new instance of a class.

    According to the JVM spec:
    - Creates a new instance of the specified class
    - Pushes a reference to the new instance onto the operand stack
    - The instance is uninitialized
    - Must be followed by an invokespecial to call <init> before use
    - May trigger class initialization if the class is not yet initialized
    """

    classname: jvm.ClassName  # The class to instantiate

    @classmethod
    def from_json(cls, json: dict) -> "Opcode":
        return cls(offset=json["offset"], classname=jvm.ClassName.decode(json["class"]))

    def real(self) -> str:
        return f"new {self.classname.slashed()}"

    def semantics(self) -> str | None:
        semantics = """
        bc[i].opr = 'new'
        bc[i].class = c
        -------------------------[new]
        bc |- (i, s) -> (i+1, s + [objectref])
        where objectref is a fresh instance of class c
        """

        return None

    def mnemonic(self) -> str:
        return "new"

    def __str__(self):
        return f"new {self.classname}"


@dataclass(frozen=True, order=True)
class Throw(Opcode):
    """The throw opcode that throws an exception object.

    According to the JVM spec:
    - Throws objectref as an exception
    - objectref must be a reference to an instance of class Throwable or a subclass
    - If objectref is null, throws NullPointerException instead
    - The objectref is cleared from the current operand stack and pushed onto
      the operand stack of the exception handler if the exception is caught
    """

    @classmethod
    def from_json(cls, json: dict) -> "Opcode":
        return cls(offset=json["offset"])

    def real(self) -> str:
        return "athrow"

    def semantics(self) -> str | None:
        semantic = """
        bc[i].opr = 'throw'
        -------------------------[throw]
        bc |- (i, s + [objectref]) -> (handler_pc, [objectref]) if exception is caught
        bc |- (i, s + [objectref]) -> (⊥, [objectref]) if exception is uncaught
        where objectref must be an instance of Throwable or subclass
        """

        return semantic

    def mnemonic(self) -> str:
        return "athrow"

    def __str__(self):
        return "throw"


@dataclass(frozen=True, order=True)
class Incr(Opcode):
    """The increment opcode that adds a constant value to a local variable.

    According to the JVM spec:
    - Increments a local variable by a constant value
    - Local variable must contain an int
    - Can increment by -128 to 127 in standard form
    - Wide format allows -32768 to 32767
    - The increment operation is done in place
      (no stack operations involved)
    """

    index: int  # Index of the local variable
    amount: int  # Constant to add to the variable

    @classmethod
    def from_json(cls, json: dict) -> "Opcode":
        return cls(offset=json["offset"], index=json["index"], amount=json["amount"])

    def real(self) -> str:
        return f"iinc {self.index} {self.amount}"

    def semantics(self) -> str | None:
        semantic = """
        bc[i].opr = 'incr'
        bc[i].index = idx
        bc[i].amount = const
        -------------------------[iinc]
        bc |- (i, s) -> (i+1, s)
        where locals[idx] = locals[idx] + const
        """

        return semantic

    def mnemonic(self) -> str:
        return "iinc"

    def __str__(self):
        return f"incr {self.index} by {self.amount}"


@dataclass(frozen=True, order=True)
class Goto(Opcode):
    """The goto opcode that performs an unconditional jump.

    According to the JVM spec:
    - Continues execution from the instruction at target
    - Target address must be that of an opcode of an instruction within the method
    - No stack effects (doesn't change stack)
    - Has standard form (goto) and wide form (goto_w) for different offset ranges
    """

    target: int  # Jump target offset

    @classmethod
    def from_json(cls, json: dict) -> "Opcode":
        return cls(offset=json["offset"], target=json["target"])

    def real(self) -> str:
        # Note: We don't distinguish between goto and goto_w here
        # as that's typically determined by the bytecode assembler
        return f"goto {self.target}"

    def semantics(self) -> str | None:
        semantic = """
        bc[i].opr = 'goto'
        bc[i].target = t
        -------------------------[goto]
        bc |- (i, s) -> (t, s)
        where t must be a valid instruction offset
        """

        return semantic

    def mnemonic(self) -> str:
        return "goto"

    def __str__(self):
        return f"goto {self.target}"


@dataclass(frozen=True, order=True)
class Return(Opcode):
    """The return opcode that returns (with optional value) from a method.

    According to the JVM spec:
    - Returns control to the invoker of the current method
    - If type is present, returns a value of that type to invoker
    - If type is None (void return), returns no value
    - Must match method's declared return type
    - Return value (if any) must be assignable to declared return type
    """

    type: jvm.Type | None  # Return type (None for void return)

    def __post_init__(self):
        assert (
            self.type is None or self.type.is_stacktype()
        ), "return only handles stack types {self.type()}"

    @classmethod
    def from_json(cls, json: dict) -> "Opcode":
        type_info = json.get("type")
        if type_info is None:
            return_type = None
        else:
            return_type = jvm.Type.from_json(type_info)

        return cls(offset=json["offset"], type=return_type)

    def real(self) -> str:
        if self.type is None:
            return "return"  # void return

        # Map type to appropriate return instruction
        match self.type:
            case jvm.Int():
                return "ireturn"
            case jvm.Long():
                return "lreturn"
            case jvm.Float():
                return "freturn"
            case jvm.Double():
                return "dreturn"
            case jvm.Reference():
                return "areturn"
            case _:
                raise ValueError(f"Unknown return type: {self.type}")

    def semantics(self) -> str | None:
        semantics = """
        bc[i].opr = 'return'
        bc[i].type = t where t != None
        -------------------------[return_value]
        bc |- (i, s + [value]) -> return value

        bc[i].opr = 'return'
        bc[i].type = None
        -------------------------[return_void]
        bc |- (i, s) -> return
        """
        return None

    def mnemonic(self) -> str:
        return self.real()

    def __str__(self):
        type = str(self.type) if self.type is not None else "V"
        return f"return:{type}"
