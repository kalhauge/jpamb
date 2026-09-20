"""Shared metadata and reporting helpers used by both analysis pipelines."""

import shlex
import subprocess
import sys
from dataclasses import dataclass
from typing import Self, TextIO

import sexpr
from jpamb.utils import Effect


@dataclass(frozen=True)
class AnalysisInfo:
    name: str
    version: str
    group: str
    tags: tuple[str, ...]
    system: str

    @classmethod
    def from_cmd(
        cls,
        cmd: tuple[str, ...],
        *,
        timeout: float,
        eff: Effect,
        context: str = "the program",
    ) -> Self:
        """Probe a program with `info` and parse its metadata."""
        with eff.context(f"Getting info about {context}"):
            try:
                out = eff.run(cmd + ("info",), timeout=timeout)
            except subprocess.CalledProcessError as e:
                eff.error(f"Ran {shlex.join(cmd)} info, and got error:\n{e.stderr}")
                raise
            try:
                return cls.parse(out)
            except ValueError:
                eff.error("Expected info, but got:")
                for o in out.splitlines():
                    eff.error(o)
                raise

    @staticmethod
    def parse(output: str):
        lines = output.splitlines()
        if len(lines) == 5:
            [name, version, group, ltags, lsystem] = lines
        elif len(lines) == 4:
            [name, version, group, ltags] = lines
            lsystem = ""
        else:
            raise ValueError(f"Expected 5 lines, but got {len(output.splitlines())}")

        tags = []
        for t in ltags.split(","):
            tags.append(t.strip())

        system = lsystem.strip()

        return AnalysisInfo(
            name.strip(),
            version.strip(),
            group.strip(),
            tuple(tags),
            system,
        )

    def display(self, *, file=sys.stdout):
        file.write("Analysis:\n")
        file.write(f" Name:         {self.name}\n")
        file.write(f" Version:      {self.version}\n")
        file.write(f" Group:        {self.group}\n")
        file.write(f" Tags:         {self.tags}\n")
        file.write(f" System:       {self.system}\n")

    def __sexpr__(self) -> sexpr.SExpr:
        return sexpr.from_dataclass(self)

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> Self:
        return sexpr.to_dataclass(expr, target=cls)


@dataclass(frozen=True, slots=True)
class Duration(sexpr.AsSExpr):
    absolute: int
    relative: float


def write_report(summary, *, file: TextIO, eff: Effect) -> None:
    """Write a summary report to `file`, reporting whether it succeeded."""
    name = getattr(file, "name", "<report>")
    content = sexpr.pretty(summary.__sexpr__(), indent=2)
    try:
        file.write(content)
        eff.success(f"Successfully wrote report to {name}")
    except OSError:
        eff.error("Failed to write report")
