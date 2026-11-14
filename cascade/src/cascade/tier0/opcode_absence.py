"""Tier 0a: opcode-absence analysis.

Check for code that could cause an outcome, if that instruction is not found, answer no
"""

import jpamb
import jvm
from jvm.classfile import AbsMethodID, MethodID, Parameters
from jvm.type import Type

ASSERTION = "assertion error"
DIVZERO = "divide by zero"
NULL = "null pointer"
OOB = "out of bounds"
NONTERM = "*"

ALL_OUTCOMES = frozenset({ASSERTION, DIVZERO, NULL, OOB, NONTERM})

THROWABLE_OUTCOME = {
    "java/lang/AssertionError": ASSERTION,
    "java/lang/ArithmeticException": DIVZERO,
    "java/lang/ArrayIndexOutOfBoundsException": OOB,
    "java/lang/NullPointerException": NULL,
}

# assumptions by us, these intructions cannot cause an error by themselves
HARMLESS = frozenset({
    "push", "load", "store", "dup", "pop", "incr", "return",
    "cast", "negate", "new", "newarray", "checkcast", "instanceof",
})


def jump_targets(ins: dict) -> list[int]:
    """The instruction indices a jump can go to."""
    match ins["opr"]:
        case "goto" | "if" | "ifz":
            return [ins["target"]]
        case "tableswitch":
            return [ins["default"], *ins["targets"]]
        case "lookupswitch":
            return [ins["default"], *(t["target"] for t in ins["targets"])]
    return []


def thrown_class(code: list[dict], index: int) -> str | None:
    """The class thrown at `index`, if it matches the javac idiom
    `new C; dup; ...; invokespecial C.<init>; throw`. None if unknown."""
    if index == 0:
        return None
    prev = code[index - 1]
    if (
        prev["opr"] == "invoke"
        and prev["access"] == "special"
        and prev["method"]["name"] == "<init>"
    ):
        return prev["method"]["ref"]["name"]
    return None


def local_outcomes(code: list[dict], index: int) -> set[str]:
    """The rule table: outcomes the instruction at `index` can cause by itself.

    Calls are only checked for a null receiver here; following them into the
    callee comes later.
    """
    ins = code[index]
    opr = ins["opr"]

    if opr in HARMLESS:
        return set()

    match opr:
        case "goto" | "if" | "ifz" | "tableswitch" | "lookupswitch":
            # if instruction jumps it can be a loop
            return {NONTERM} if any(t <= index for t in jump_targets(ins)) else set()

        case "binary":
            if ins["operant"] in ("div", "rem") and ins["type"] in ("int", "long"):
                return {DIVZERO}
            return set()

        case "array_load" | "array_store":
            return {OOB, NULL}

        case "arraylength":
            return {NULL}

        case "get" | "put":
            # static fields have no object to dereference.
            return set() if ins["static"] else {NULL}

        case "invoke":
            access = ins["access"]
            if access in ("virtual", "interface"):
                return {NULL}
            if access == "special" and ins["method"]["name"] != "<init>":
                return {NULL}
            return set()

        case "throw":
            cls = thrown_class(code, index)
            if cls is None:
                return set(ALL_OUTCOMES)  # unknown object so assume the worst
            if cls in THROWABLE_OUTCOME:
                return {THROWABLE_OUTCOME[cls]}
            return set()  # TODO: subclasses of the four exception classes

    # worst case
    return set(ALL_OUTCOMES)


def method_sites(code: list[dict]) -> dict[str, list[int]]:
    """For every outcome, the indices of the instructions in `code` that can cause it.

    empty list has no fault site in this method.
    """
    sites: dict[str, list[int]] = {outcome: [] for outcome in ALL_OUTCOMES}
    for index in range(len(code)):
        for outcome in local_outcomes(code, index):
            sites[outcome].append(index)
    return sites


def method_id(classname: jvm.ClassName, mjson: dict) -> AbsMethodID:
    """Build the id of a method from its decompiled JSON."""
    rtype = mjson["returns"]["type"]
    return AbsMethodID(
        classname,
        MethodID(
            name=mjson["name"],
            params=Parameters.from_json(mjson["params"], annotated=True),
            return_type=Type.from_json(rtype) if rtype is not None else None,
        ),
    )


class Program:
    """All decompiled classes of the benchmark, loaded once."""

    def __init__(self, suite: jpamb.Suite, eff):
        self.classes: dict[str, dict] = {}         # "jpamb/cases/Calls" -> class JSON
        self.methods: dict[AbsMethodID, dict] = {}  # method id -> method JSON
        # (name, params) -> every benchmark method with that signature (for virtual calls)
        self.by_signature: dict[tuple[str, Parameters], list[AbsMethodID]] = {}

        for cn in suite.classes(eff=eff):
            cjson = suite.findclass(cn, eff=eff)
            self.classes[cn.slashed()] = cjson
            for mjson in cjson["methods"]:
                mid = method_id(cn, mjson)
                self.methods[mid] = mjson
                key = (mid.extension.name, mid.extension.params)
                self.by_signature.setdefault(key, []).append(mid)

    def code(self, mid: AbsMethodID) -> list[dict] | None:
        """The instructions of a method, or None if we don't have its bytecode
        (a library method, or an abstract method)."""
        mjson = self.methods.get(mid)
        if mjson is None or mjson.get("code") is None:
            return None
        return mjson["code"]["bytecode"]

    def superclass(self, cls: str) -> str | None:
        """The superclass of a benchmark class, e.g. "java/lang/Object"."""
        sup = self.classes[cls].get("super")
        return sup["name"] if sup else None


def call_targets(program: Program, ins: dict) -> list[AbsMethodID] | None:
    """The methods an `invoke` instruction may run. None if we cannot tell."""
    if ins["access"] == "dynamic":
        return None  # target is decided at runtime by a bootstrap method

    named = AbsMethodID.from_json(ins["method"])
    if ins["access"] in ("virtual", "interface"):
        # The runtime object picks the override: follow every benchmark
        # method with the same name and parameters (design decision 3).
        key = (named.extension.name, named.extension.params)
        others = [m for m in program.by_signature.get(key, []) if m != named]
        return [named, *others]
    # static / special: exactly the named method.
    return [named]


def analyse(program: Program, entry: AbsMethodID) -> dict[str, list[tuple[AbsMethodID, int]]]:
    """Fault sites of every outcome in all methods reachable from `entry`.

    A site is (method, instruction index); index -1 means "somewhere inside a
    method we cannot see".
    """
    sites: dict[str, list[tuple[AbsMethodID, int]]] = {o: [] for o in ALL_OUTCOMES}
    todo = [entry]
    seen: set[AbsMethodID] = set()

    while todo:
        mid = todo.pop()
        if mid in seen:
            continue
        seen.add(mid)

        code = program.code(mid)
        if code is None:
            # No bytecode (library / abstract method) - assume the worst.
            for outcome in ALL_OUTCOMES:
                sites[outcome].append((mid, -1))
            continue

        # 1. the method's own fault sites (the rule table)
        for outcome, indices in method_sites(code).items():
            sites[outcome].extend((mid, i) for i in indices)

        # 2. follow every call
        for index, ins in enumerate(code):
            if ins["opr"] != "invoke":
                continue
            targets = call_targets(program, ins)
            if targets is None:
                # Cannot tell what runs - assume the worst at the call.
                for outcome in ALL_OUTCOMES:
                    sites[outcome].append((mid, index))
            else:
                todo.extend(targets)

    return sites
