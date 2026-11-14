"""Tier 0a: opcode-absence analysis.

An outcome is impossible if no instruction that can cause it is reachable.
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

# how JPAMB maps exceptions to outcomes
THROWABLE_OUTCOME = {
    "java/lang/AssertionError": ASSERTION,
    "java/lang/ArithmeticException": DIVZERO,
    "java/lang/ArrayIndexOutOfBoundsException": OOB,
    "java/lang/NullPointerException": NULL,
}

# instructions that cannot cause an outcome
HARMLESS = frozenset({
    "push", "load", "store", "dup", "pop", "incr", "return",
    "cast", "negate", "new", "newarray", "checkcast", "instanceof",
})

# library methods we trust to terminate and cause no outcome
SAFE_LIBRARY_METHODS = frozenset({
    "java.lang.Object.<init>:()V",
    "java.lang.AssertionError.<init>:()V",
    "java.lang.Class.desiredAssertionStatus:()Z",
    "java.lang.String.equals:(Ljava/lang/Object;)Z",
    "java.lang.String.length:()I",
    "java.lang.String.charAt:(I)C",
})


def jump_targets(ins: dict) -> list[int]:
    """Indices a jump can go to."""
    match ins["opr"]:
        case "goto" | "if" | "ifz":
            return [ins["target"]]
        case "tableswitch":
            return [ins["default"], *ins["targets"]]
        case "lookupswitch":
            return [ins["default"], *(t["target"] for t in ins["targets"])]
    return []


def thrown_class(code: list[dict], index: int) -> str | None:
    """Class thrown at `index` if preceded by its constructor call, else None."""
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
    """The rule table: outcomes the instruction at `index` can cause by itself."""
    ins = code[index]
    opr = ins["opr"]

    if opr in HARMLESS:
        return set()

    match opr:
        case "goto" | "if" | "ifz" | "tableswitch" | "lookupswitch":
            # backward jump = loop
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
            return set() if ins["static"] else {NULL}

        case "invoke":
            # null receiver; the callee itself is handled in analyse
            access = ins["access"]
            if access in ("virtual", "interface"):
                return {NULL}
            if access == "special" and ins["method"]["name"] != "<init>":
                return {NULL}
            return set()

        case "throw":
            cls = thrown_class(code, index)
            if cls is None:
                return set(ALL_OUTCOMES)
            if cls in THROWABLE_OUTCOME:
                return {THROWABLE_OUTCOME[cls]}
            return set()  # TODO: subclasses of the four exception classes

    # unknown instruction: assume the worst
    return set(ALL_OUTCOMES)


def method_sites(code: list[dict]) -> dict[str, list[int]]:
    """Per outcome, the indices in `code` that can cause it."""
    sites: dict[str, list[int]] = {outcome: [] for outcome in ALL_OUTCOMES}
    for index in range(len(code)):
        for outcome in local_outcomes(code, index):
            sites[outcome].append(index)
    return sites


def method_id(classname: jvm.ClassName, mjson: dict) -> AbsMethodID:
    """Method id from its decompiled JSON."""
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
    """All decompiled benchmark classes, loaded once."""

    def __init__(self, suite: jpamb.Suite, eff):
        self.classes: dict[str, dict] = {}
        self.methods: dict[AbsMethodID, dict] = {}
        # (name, params) -> methods with that signature, for virtual calls
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
        """Instructions of a method, or None if it has no bytecode."""
        mjson = self.methods.get(mid)
        if mjson is None or mjson.get("code") is None:
            return None
        return mjson["code"]["bytecode"]

    def superclass(self, cls: str) -> str | None:
        """Superclass of a benchmark class."""
        sup = self.classes[cls].get("super")
        return sup["name"] if sup else None


def call_targets(program: Program, ins: dict) -> list[AbsMethodID] | None:
    """Methods an `invoke` may run, or None if unknown."""
    if ins["access"] == "dynamic":
        return None

    named = AbsMethodID.from_json(ins["method"])
    if ins["access"] in ("virtual", "interface"):
        # any override may run: follow all methods with the same signature
        key = (named.extension.name, named.extension.params)
        others = [m for m in program.by_signature.get(key, []) if m != named]
        return [named, *others]
    return [named]


def reaches(calls: dict[AbsMethodID, list[tuple[int, AbsMethodID]]], src: AbsMethodID, dst: AbsMethodID) -> bool:
    """True if `src` can reach `dst` through calls."""
    todo = [src]
    seen: set[AbsMethodID] = set()
    while todo:
        m = todo.pop()
        if m == dst:
            return True
        if m in seen:
            continue
        seen.add(m)
        todo.extend(callee for _, callee in calls.get(m, []))
    return False


def recursive_calls(calls: dict[AbsMethodID, list[tuple[int, AbsMethodID]]]) -> list[tuple[AbsMethodID, int]]:
    """Call sites whose callee can call back into the caller."""
    return [
        (caller, index)
        for caller, edges in calls.items()
        for index, callee in edges
        if reaches(calls, callee, caller)
    ]


def analyse(program: Program, entry: AbsMethodID) -> dict[str, list[tuple[AbsMethodID, int]]]:
    """Per outcome, the fault sites (method, index) reachable from `entry`.

    Index -1 means somewhere inside a method without bytecode.
    """
    sites: dict[str, list[tuple[AbsMethodID, int]]] = {o: [] for o in ALL_OUTCOMES}
    todo = [entry]
    seen: set[AbsMethodID] = set()
    calls: dict[AbsMethodID, list[tuple[int, AbsMethodID]]] = {}

    while todo:
        mid = todo.pop()
        if mid in seen:
            continue
        seen.add(mid)

        code = program.code(mid)
        if code is None:
            if mid.encode() in SAFE_LIBRARY_METHODS:
                continue
            for outcome in ALL_OUTCOMES:
                sites[outcome].append((mid, -1))
            continue

        for outcome, indices in method_sites(code).items():
            sites[outcome].extend((mid, i) for i in indices)

        for index, ins in enumerate(code):
            if ins["opr"] != "invoke":
                continue
            targets = call_targets(program, ins)
            if targets is None:
                for outcome in ALL_OUTCOMES:
                    sites[outcome].append((mid, index))
            else:
                todo.extend(targets)
                calls.setdefault(mid, []).extend((index, t) for t in targets)

    sites[NONTERM].extend(recursive_calls(calls))
    return sites


def main():
    methodid = jpamb.getmethodid(
        "tier0-absence", "0.1", "Group 21", ["syntactic", "python"], for_science=True
    )
    suite, eff = jpamb.setup()
    sites = analyse(Program(suite, eff), methodid)

    for query in jpamb.QUERIES:
        if query in ALL_OUTCOMES and not sites[query]:
            print(f"{query};0%")
        else:
            print(f"{query};maybe")


if __name__ == "__main__":
    main()
