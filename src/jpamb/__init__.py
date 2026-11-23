"""
jpamb

This module provides the basic data model for working with the JPAMB.

"""

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import NoReturn

import jvm
import jvm.state
import sexpr
from jpamb.analyse import QUERIES as QUERIES
from jpamb.case import Case as Case
from jpamb.case import Input
from jpamb.report import AnalysisInfo as AnalysisInfo
from jpamb.suite import Suite
from jpamb.utils import Effect
from jpamb.version import __version__ as __version__


@dataclass
class Bytecode:
    suite: Suite
    eff: Effect
    methods: dict[jvm.AbsMethodID, jvm.Method] = field(default_factory=dict)

    def getmethod(self, methodid: jvm.AbsMethodID) -> jvm.Method:
        try:
            method = self.methods[methodid]
        except KeyError:
            opcodes = list(self.suite.method_opcodes(methodid, eff=self.eff))
            max_locals = self.suite.method_max_locals(methodid, eff=self.eff)
            method = jvm.Method(methodid, opcodes, max_locals)
            self.methods[methodid] = method
        return method

    def __getitem__(self, pc: jvm.state.PC) -> jvm.Opcode:
        return self.getmethod(pc.method).opcodes[pc.offset]

    def __contains__(self, pc: jvm.state.PC) -> bool:
        return pc.offset < len(self.getmethod(pc.method).opcodes)


def setup() -> tuple[Suite, Effect]:
    """Get a suite in the current working directory"""

    eff = Effect(None)
    return (Suite.from_workdir(Path.cwd()), eff)


def getmethodid(
    name: str,
    version: str,
    group: str,
    tags: list[str],
    for_science: bool,
) -> jvm.AbsMethodID:
    """Get the method id from the program arguments, or output the info."""

    if len(sys.argv) == 2 and sys.argv[1] == "info":
        printinfo(name, version, group, tags, for_science)

    assert len(sys.argv) == 2, f"expected only one argument but got {sys.argv[1:]}"

    mid = sys.argv[1]
    return parse_methodid(mid)


def getexperiment(
    name: str,
    version: str,
    group: str,
    tags: list[str],
    for_science: bool,
) -> tuple[jvm.AbsMethodID, Input | None, int]:
    """Get the experiment from the program arguments."""

    if len(sys.argv) == 2 and sys.argv[1] == "info":
        printinfo(name, version, group, tags, for_science)

    assert len(sys.argv) == 4, (
        f"expected exactly three arguments but got {sys.argv[1:]}"
    )

    mid = parse_methodid(sys.argv[1])
    i = parse_input(sys.argv[2])
    max_iter = int(sys.argv[3])

    return mid, i, max_iter


def getcase(
    name: str,
    version: str,
    group: str,
    tags: list[str],
    for_science: bool,
) -> tuple[jvm.AbsMethodID, Input | None, int]:
    return getexperiment(name, version, group, tags, for_science)


def printinfo(
    name: str,
    version: str,
    group: str,
    tags: list[str],
    for_science: bool,
) -> NoReturn:
    sys.stdout.write(f"{name}\n")
    sys.stdout.write(f"{version}\n")
    sys.stdout.write(f"{group}\n")
    sys.stdout.write(f"{','.join(tags)}\n")

    if for_science:
        import platform

        sys.stdout.write(f"{platform.platform()}\n")

    sys.exit(0)


def parse_methodid(mid) -> jvm.AbsMethodID:
    return jvm.AbsMethodID.decode(mid)


def parse_input(i) -> Input | None:
    if i == "ALL":
        return None
    return Input.decode(i)


def emit_init(state: jvm.state.State) -> sexpr.SExpr:
    import sys

    import jpamb.interpret

    expr = sexpr.sexpr(state)
    out = sexpr.pretty(sexpr.sexpr(jpamb.interpret.Init(expr)), indent=2)
    sys.stderr.write(out + "\n")
    sys.stdout.write(out + "\n")
    return expr


def emit_step(
    before: sexpr.SExpr, pc: jvm.state.PC, after: jvm.state.State | str, depth=2
) -> sexpr.SExpr:
    import jpamb.interpret

    assert sexpr.issexpr(before), "Input the output of emit_step or emit_init"
    assert isinstance(pc, jvm.state.PC), f"Expected PC but got {pc!r}"

    expr = sexpr.sexpr(after)
    diff = sexpr.diff(before, expr, depth=depth)
    out = sexpr.pretty(sexpr.sexpr(jpamb.interpret.Step(pc, tuple(diff))), indent=2)
    sys.stderr.write(out + "\n")
    sys.stdout.write(out + "\n")
    return expr
