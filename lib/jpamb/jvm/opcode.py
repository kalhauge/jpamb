"""
jpamb.jvm.opcode

This module contains the decompilation of the output of jvm2json
into a python structure, as well documentation and semantics for
each instruction.

"""

from dataclasses import dataclass
from abc import ABC
from typing import Self

import enum

from jpamb.jvm import base as jvm


@dataclass(frozen=True, order=True)
class Opcode(ABC):
    """An opcode, as parsed from the jvm2json output."""

    offset: int

    @classmethod
    def from_json(cls, json: dict) -> "Opcode":
        match json["opr"]:
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
        return opr.from_json(json)

    def real(self) -> str:
        """return the real opcode, as documented in the jvm spec."""
        raise NotImplementedError(f"Unhandled real {self!r}")


@dataclass(frozen=True)
class Push(Opcode):
    """The push opcode"""

    docs = [
        "https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.iconst_i"
    ]

    semantics = """
    bc[i].opr = 'push'
    bc[i].value = v
    -------------------------[push]
    bc |- (i, s) -> (i+1, s + [v])
    """

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

    def __str__(self):
        return f"push {self.value}"


@dataclass(frozen=True)
class NewArray(Opcode):
    """The new array opcode"""

    docs = [
        "https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.newarray"
        "https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.multianewarray"
    ]

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

    def __str__(self):
        return f"newarray[{self.dim}D] {self.type}"


@dataclass(frozen=True)
class Dup(Opcode):
    """The dublicate the stack opcode"""

    docs = [
        "https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.dup"
    ]

    words: int

    @classmethod
    def from_json(cls, json: dict) -> Opcode:
        return cls(
            offset=json["offset"],
            words=json["words"],
        )

    def real(self) -> str:
        if self.words == 1:
            return f"dup"
        return super().real()

    def __str__(self):
        return f"dup {self.words}"


@dataclass(frozen=True)
class ArrayStore(Opcode):
    """The Array Store command that stores a value in the array."""

    docs = [
        "https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.aastore"
        "https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.iastore"
    ]

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

    def __str__(self):
        return f"array_store {self.type}"


@dataclass(frozen=True)
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

    def __str__(self):
        return f"cast {self.from_} {self.to_}"


@dataclass(frozen=True)
class ArrayLoad(Opcode):
    """The Array Load command that load a value from the array."""

    docs = [
        "https://docs.oracle.com/javase/specs/jvms/se24/html/jvms-4.html#jvms-4.10.1.9.aaload"
    ]

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

    def __str__(self):
        return f"array_load {self.type}"


@dataclass(frozen=True)
class ArrayLength(Opcode):
    """
    arraylength:
     - Takes an array reference from the operand stack
     - Pushes the length of the array onto the operand stack
     - Throws NullPointerException if the array reference is null
    """

    docs = [
        "https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.arraylength"
    ]

    @classmethod
    def from_json(cls, json: dict) -> "Opcode":
        return cls(
            offset=json["offset"],
        )

    def real(self) -> str:
        return "arraylength"

    def __str__(self):
        return "arraylength"


@dataclass(frozen=True)  # make it work for
class InvokeVirtual(Opcode):
    """The invoke virtual opcode for calling instance methods"""

    docs = [
        "https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.invokevirtual"
    ]

    method: jvm.Absolute[jvm.MethodID]

    @classmethod
    def from_json(cls, json: dict) -> "Opcode":
        assert json["opr"] == "invoke" and json["access"] == "virtual"
        return cls(
            offset=json["offset"],
            method=json["method"],
        )

    def real(self) -> str:
        return f"invokevirtual {self.method}"

    def __str__(self):
        return f"invoke virtual {self.method}"


@dataclass(frozen=True)
class InvokeStatic(Opcode):
    """The invoke static opcode for calling static methods"""

    docs = [
        "https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.invokestatic"
    ]

    method: jvm.Absolute[jvm.MethodID]

    @classmethod
    def from_json(cls, json: dict) -> "Opcode":
        assert json["opr"] == "invoke" and json["access"] == "static"
        return cls(
            offset=json["offset"],
            method=json["method"],
        )

    def real(self) -> str:
        return f"invokestatic {self.method}"

    def __str__(self):
        return f"invoke static {self.method}"


@dataclass(frozen=True)
class InvokeInterface(Opcode):
    """The invoke interface opcode for calling interface methods"""

    docs = [
        "https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.invokeinterface"
    ]

    method: jvm.Absolute[jvm.MethodID]
    stack_size: int

    @classmethod
    def from_json(cls, json: dict) -> "Opcode":
        assert json["opr"] == "invoke" and json["access"] == "interface"
        return cls(
            offset=json["offset"],
            method=json["method"],
            stack_size=json["stack_size"],
        )

    def real(self) -> str:
        return f"invokeinterface {self.method} {self.stack_size}"

    def __str__(self):
        return f"invoke interface {self.method} (stack_size={self.stack_size})"


@dataclass(frozen=True)
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

    docs = [
        "https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.5.invokespecial"
    ]


    method: jvm.Absolute[jvm.MethodID]
    is_interface: bool  # Whether the method is from an interface

    @classmethod
    def from_json(cls, json: dict) -> "Opcode":
        assert json["opr"] == "invoke" and json["access"] == "special"

        # Extract class name from SimpleReferenceType
        ref = json["method"]["ref"]
        assert ref["kind"] == "class"
        class_name = ref["name"]

        # Get method details
        method_name = json["method"]["name"]

        # Convert args array to proper JVM type encoding
        args = ""
        if "args" in json["method"]:
            args_types = []
            for arg in json["method"]["args"]:
                if isinstance(arg, str):  # Basic type
                    args_types.append(arg)
                else:  # Complex type (like class or array)
                    if arg["kind"] == "class":
                        args_types.append(f"L{arg['name']};")
                    elif arg["kind"] == "array":
                        # Recursively handle array types if needed
                        args_types.append("[" + arg["type"])
            args = "".join(args_types)

        # Handle return type - use 'V' for void when returns is None/not present
        returns = json["method"].get("returns")
        if returns is None:
            return_type = "V"
        else:
            if isinstance(returns, str):  # Basic type
                return_type = returns
            else:  # Complex type
                if returns["kind"] == "class":
                    return_type = f"L{returns['name']};"
                elif returns["kind"] == "array":
                    return_type = "[" + returns["type"]

        # Construct method string in format: className.methodName:(args)returnType
        method_str = f"{class_name}.{method_name}:({args}){return_type}"

        return cls(
            offset=json["offset"],
            method=jvm.Absolute.decode(method_str, jvm.MethodID.decode),
            is_interface=json["method"]["is_interface"],
        )

    def real(self) -> str:
        return f"invokespecial {self.method}"

    def __str__(self):
        interface_str = " interface" if self.is_interface else ""
        return f"invoke special{interface_str} {self.method}"


@dataclass(frozen=True)
class Store(Opcode):
    """The store opcode that stores values to local variables"""

    docs = [
        "https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.istore",
        "https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.5.astore",
    ]

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

    def __str__(self):
        return f"store {self.type} {self.index}"


class BinaryOpr(enum.Enum):
    Add = enum.auto()
    Sub = enum.auto()
    Mul = enum.auto()
    Div = enum.auto()
    Rem = enum.auto()

    @staticmethod
    def from_json(json: str) -> Self:
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


@dataclass(frozen=True)
class Binary(Opcode):

    type: jvm.Type
    operant: BinaryOpr

    docs = [
        "https://docs.oracle.com/javase/specs/jvms/se24/html/jvms-4.html#jvms-4.10.1.9.dadd",
    ]

    @classmethod
    def from_json(cls, json: dict) -> "Opcode":
        return cls(
            offset=json["offset"],
            type=jvm.Type.from_json(json["type"]),
            operant=BinaryOpr.from_json(json["operant"]),
        )

    def __str__(self):
        return f"{self.operant} {self.type}"

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


@dataclass(frozen=True)
class Load(Opcode):
    """The load opcode that loads values from local variables"""

    docs = [
        "https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.iload",
        "https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.5.aload",
    ]

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

    def __str__(self):
        return f"load {self.type} {self.index}"


@dataclass(frozen=True)
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

    docs = [
        "https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.if_icmpeq",
        "https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.5.if_acmpeq",
    ]

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

    def __str__(self):
        return f"if {self.condition} {self.target}"


@dataclass(frozen=True)
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

    docs = [
        "https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.getfield",
        "https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.5.getstatic",
    ]


    static: bool
    field: jvm.Absolute[jvm.FieldID]  # We need to add FieldID to base.py

    @classmethod
    def from_json(cls, json: dict) -> "Opcode":
        # Construct field object from the json data
        field = jvm.Absolute(
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

    def __str__(self):
        kind = "static" if self.static else "field"
        return f"get {kind} {self.field}"


@dataclass(frozen=True)
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

    docs = [
        "https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.ifeq",
        "https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.5.ifnull",
    ]


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

    def __str__(self):
        return f"ifz {self.condition} {self.target}"


@dataclass(frozen=True)
class New(Opcode):
    """The new opcode that creates a new instance of a class.

    According to the JVM spec:
    - Creates a new instance of the specified class
    - Pushes a reference to the new instance onto the operand stack
    - The instance is uninitialized
    - Must be followed by an invokespecial to call <init> before use
    - May trigger class initialization if the class is not yet initialized
    """

    docs = [
        "https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.new"
    ]


    classname: jvm.ClassName  # The class to instantiate

    @classmethod
    def from_json(cls, json: dict) -> "Opcode":
        return cls(offset=json["offset"], classname=jvm.ClassName.decode(json["class"]))

    def real(self) -> str:
        return f"new {self.classname.slashed()}"

    def __str__(self):
        return f"new {self.classname}"


@dataclass(frozen=True)
class Throw(Opcode):
    """The throw opcode that throws an exception object.

    According to the JVM spec:
    - Throws objectref as an exception
    - objectref must be a reference to an instance of class Throwable or a subclass
    - If objectref is null, throws NullPointerException instead
    - The objectref is cleared from the current operand stack and pushed onto
      the operand stack of the exception handler if the exception is caught
    """

    docs = [
        "https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.athrow"
    ]


    @classmethod
    def from_json(cls, json: dict) -> "Opcode":
        return cls(offset=json["offset"])

    def real(self) -> str:
        return "athrow"

    def __str__(self):
        return "throw"


@dataclass(frozen=True)
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

    docs = [
        "https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.iinc"
    ]


    index: int  # Index of the local variable
    amount: int  # Constant to add to the variable

    @classmethod
    def from_json(cls, json: dict) -> "Opcode":
        return cls(offset=json["offset"], index=json["index"], amount=json["amount"])

    def real(self) -> str:
        return f"iinc {self.index} {self.amount}"

    def __str__(self):
        return f"incr {self.index} by {self.amount}"


@dataclass(frozen=True)
class Goto(Opcode):
    """The goto opcode that performs an unconditional jump.

    According to the JVM spec:
    - Continues execution from the instruction at target
    - Target address must be that of an opcode of an instruction within the method
    - No stack effects (doesn't change stack)
    - Has standard form (goto) and wide form (goto_w) for different offset ranges
    """

    docs = [
        "https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.goto",
        "https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.goto_w",
    ]

    target: int  # Jump target offset

    @classmethod
    def from_json(cls, json: dict) -> "Opcode":
        return cls(offset=json["offset"], target=json["target"])

    def real(self) -> str:
        # Note: We don't distinguish between goto and goto_w here
        # as that's typically determined by the bytecode assembler
        return f"goto {self.target}"

    def __str__(self):
        return f"goto {self.target}"


@dataclass(frozen=True)
class Return(Opcode):
    """The return opcode that returns (with optional value) from a method.

    According to the JVM spec:
    - Returns control to the invoker of the current method
    - If type is present, returns a value of that type to invoker
    - If type is None (void return), returns no value
    - Must match method's declared return type
    - Return value (if any) must be assignable to declared return type
    """

    docs = [
        "https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.ireturn",
        "https://docs.oracle.com/javase/specs/jvms/se23/html/jvms-6.html#jvms-6.5.return",
    ]


    type: jvm.Type | None  # Return type (None for void return)

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
            case jvm.Reference() | jvm.Object(_):
                return "areturn"
            case _:
                raise ValueError(f"Unknown return type: {self.type}")

    def __str__(self):
        return f"return{f' {self.type}' if self.type is not None else ''}"
