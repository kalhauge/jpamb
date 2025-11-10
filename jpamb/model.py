"""
jpamb.model

This module provides the basic data model for working with the JPAMB.

"""

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from loguru import logger
import collections
from collections import defaultdict
import re
import os
import shutil
import subprocess

from typing import Iterable

from jpamb import jvm


@dataclass(frozen=True, order=True)
class Input:
    """
    An 'Input' to a 'Case' is a comma seperated list of JVM values
    """

    values: tuple[jvm.Value, ...]

    @staticmethod
    def decode(input: str) -> "Input":
        if input[0] != "(" and input[-1] != ")":
            raise ValueError(f"Expected input to be in parenthesis, but got {input}")
        values = jvm.Value.decode_many(input)
        return Input(tuple(values))

    def encode(self) -> str:
        return "(" + ", ".join(v.encode() for v in self.values) + ")"


CASE_RE = re.compile(r"([^ ]*) +(\([^)]*\)) -> (.*)")


@dataclass(frozen=True, order=True)
class Case:
    """
    A 'Case' is an absolute method id, an input, and the expected result.
    """

    methodid: jvm.Absolute[jvm.MethodID]
    input: Input
    result: str

    @staticmethod
    def match(line) -> re.Match:
        if not (m := CASE_RE.match(line)):
            raise ValueError(f"Unexpected line: {line!r}")
        return m

    @staticmethod
    def decode(line):
        m = Case.match(line)
        return Case(
            jvm.AbsMethodID.decode(m.group(1)),
            Input.decode(m.group(2)),
            m.group(3),
        )

    def __str__(self) -> str:
        return f"{self.methodid.classname}.{self.methodid.extension.name}:{self.input.encode()} -> {self.result}"

    def encode(self) -> str:
        return f"{self.methodid.classname}.{self.methodid.extension.encode()} {self.input.encode()} -> {self.result}"

    @staticmethod
    def by_methodid(
        iterable: Iterable["Case"],
    ) -> list[tuple[jvm.Absolute[jvm.MethodID], list["Case"]]]:
        """Given an interable of cases, group the cases by the methodid"""
        cases_by_id = collections.defaultdict(list)

        for c in iterable:
            cases_by_id[c.methodid].append(c)

        return sorted(cases_by_id.items())


@contextmanager
def _check(reason, failfast=False):
    """Used in the checkhealth command"""
    logger.info(reason)
    try:
        yield
    except AssertionError as e:
        msg = str(e)
        if msg:
            logger.error(f"{reason} FAILED: {e}")
        else:
            logger.error(f"{reason} FAILED")
        if failfast:
            raise AssertionError(f"{reason} {str(e.args)}") from e
    else:
        logger.success(f"{reason} ok")


@dataclass(frozen=True)
class AnalysisInfo:
    name: str
    version: str
    group: str
    tags: tuple[str]
    system: str | None

    @staticmethod
    def parse(output: str):
        try:
            [name, version, group, ltags, lsystem] = output.splitlines()
        except ValueError:
            raise ValueError(f"Expected 5 lines, but got {len(output.splitlines())}")

        tags = list()
        for t in ltags.split(","):
            tags.append(t.strip())

        if lsystem.strip().lower() == "no":
            system = None
        else:
            system = lsystem.strip()

        return AnalysisInfo(name.strip(), version.strip(), group.strip(), tags, system)


@dataclass(frozen=True)
class Prediction:
    wager: float

    @staticmethod
    def parse(string: str) -> "Prediction":
        if m := re.match(r"([^%]*)\%", string):
            p = float(m.group(1)) / 100
            return Prediction.from_probability(p)
        else:
            return Prediction(float(string))

    @staticmethod
    def from_probability(p: float) -> "Prediction":
        negate = False
        if p < 0.5:
            p = 1 - p
            negate = True
        if p == 1:
            x = float("inf")
        else:
            x = (1 - 2 * p) / (-1 + p) / 2
        return Prediction(-x if negate else x)

    def to_probability(self) -> float:
        if self.wager == float("-inf"):
            return 0
        if self.wager == float("inf"):
            return 0
        w = abs(self.wager) * 2
        r = (w + 1) / (w + 2)
        return r if self.wager > 0 else 1 - r

    def score(self, happens: bool):
        wager = (-1 if not happens else 1) * self.wager
        if wager > 0:
            if wager == float("inf"):
                return 1
            else:
                return 1 - 1 / (wager + 1)
        else:
            return wager

    def __str__(self):
        return f"{self.to_probability():0.2%}"


QUERIES = (
    "*",
    "assertion error",
    "divide by zero",
    "null pointer",
    "ok",
    "out of bounds",
)


@dataclass(frozen=True)
class Response:
    predictions: dict[str, Prediction]

    @staticmethod
    def parse(out):
        predictions = {}
        for line in out.splitlines():
            try:
                query, pred = line.split(";")
                logger.debug(f"response: {line}")
            except ValueError:
                logger.warning(line)
                continue
            if query not in QUERIES:
                logger.warning(f"{query!r} not a known query")
                continue
            prediction = Prediction.parse(pred)
            predictions[query] = prediction
        return Response(predictions)

    def score(self, correct):
        total = 0
        for q, prd in self.predictions.items():
            total += prd.score(q in correct)
        return total


class Suite:
    """The suite!

    Note that only one instance per abstract path exist to be able to cache
    information about the suite on read.

    """

    _instances = dict()

    def __new__(cls, workfolder: Path | None = None):
        workfolder = workfolder or Path.cwd()
        if workfolder not in cls._instances:
            cls._instances[workfolder] = super().__new__(cls)
        return cls._instances[workfolder]

    def __init__(self, workfolder: Path | None = None):
        workfolder = workfolder or Path.cwd()
        assert workfolder.is_absolute(), f"Assuming that {workfolder} is absolute."
        self.workfolder = workfolder
        self.invalidate_cache()

    def invalidate_cache(self):
        """Invalidate the case, and require a recomputation of the cached values."""
        self._cases = None

    @property
    def stats_folder(self) -> Path:
        """The folder to place the statistics about the repository"""
        return self.workfolder / "target" / "stats"

    @property
    def classfiles_folder(self) -> Path:
        """The folder containing the class files"""
        return self.workfolder / "target" / "classes"

    def classfiles(self) -> Iterable[Path]:
        yield from self.classfiles_folder.glob("**/*.class")

    def classfile(self, cn: jvm.ClassName) -> Path:
        return (self.classfiles_folder / Path(*cn.packages) / cn.name).with_suffix(
            ".class"
        )

    @property
    def sourcefiles_folder(self) -> Path:
        """The folder containing the class files"""
        return self.workfolder / "src" / "main" / "java"

    def sourcefiles(self) -> Iterable[Path]:
        yield from self.sourcefiles_folder.glob("**/*.java")

    def sourcefile(self, cn: jvm.ClassName) -> Path:
        return (
            self.sourcefiles_folder / Path(*cn.packages) / cn.name.split("$")[0]
        ).with_suffix(".java")

    @property
    def decompiled_folder(self) -> Path:
        return self.workfolder / "target" / "decompiled"

    def decompiledfiles(self) -> Iterable[Path]:
        yield from self.decompiled_folder.glob("**/*.json")

    def decompiledfile(self, cn: jvm.ClassName) -> Path:
        return (self.decompiled_folder / Path(*cn.packages) / cn.name).with_suffix(
            ".json"
        )

    def findclass(self, cn: jvm.ClassName) -> dict:
        import json

        with open(self.decompiledfile(cn)) as fp:
            return json.load(fp)

    def findmethod(self, methodid: jvm.Absolute[jvm.MethodID]) -> jvm:
        methods = self.findclass(methodid.classname)["methods"]
        for method in methods:
            if method["name"] != methodid.extension.name:
                continue
            params = jvm.ParameterType.from_json(method["params"], annotated=True)

            assert params == methodid.extension.params, (
                f"Mulitple methods with same name {method['name']!r}, "
                f"but different params {params} from {method['params']} and {methodid.extension.params}"
            )
            break
        else:
            raise IndexError(f"Could not find {methodid}")
        return method

    def method_opcodes(self, method: jvm.Absolute[jvm.MethodID]) -> list[jvm.Opcode]:
        for op in self.findmethod(method)["code"]["bytecode"]:
            yield jvm.Opcode.from_json(op)

    def classes(self) -> Iterable[jvm.ClassName]:
        for file in self.classfiles():
            yield jvm.ClassName.from_parts(
                *file.relative_to(self.classfiles_folder).with_suffix("").parts
            )

    @property
    def case_file(self) -> Path:
        return self.stats_folder / "cases.txt"

    @property
    def version(self):
        with open(self.workfolder / "CITATION.cff") as f:
            import yaml

            return yaml.safe_load(f)["version"]

    @property
    def cases(self) -> tuple[Case, ...]:
        if self._cases is None:
            with open(self.case_file) as f:
                self._cases = tuple(Case.decode(line) for line in f)
        return self._cases

    def case_methods(self) -> Iterable[tuple[jvm.Absolute[jvm.MethodID], set[str]]]:
        methods = defaultdict(set)

        for case in self.cases:
            methods[case.methodid].add(case.result)

        return methods.items()

    def case_opcodes(self) -> list[jvm.Opcode]:
        for m, _ in self.case_methods():
            yield from self.method_opcodes(m)

    def checkhealth(self, failfast=False):
        """Checks the health of the repository through a sequence of tests"""
        from jpamb import timer

        def check(msg):
            return _check(msg, failfast)

        with check("The path"):
            with check("docker"):
                dockerbin = shutil.which("podman") or shutil.which("docker")
                assert dockerbin is not None, "java not on path"
                res = subprocess.run(
                    [dockerbin, "--version"],
                    check=True,
                    stdout=subprocess.PIPE,
                    text=True,
                )
                logger.debug(f"{dockerbin} --version\n{res}")
                assert res.returncode == 0, "dockerbin --version failed"

        with check("The timer"):
            x = timer.sieve(1000)
            assert x == 7919, "should find correct prime."

        with check(f"The source folder [{self.sourcefiles_folder}]"):
            assert self.sourcefiles_folder.exists(), "should exists"
            assert self.sourcefiles_folder.is_dir(), "should be a folder"
            files = list(self.sourcefiles())
            assert len(files) > 0, "should contain source files"
            logger.info(f"Found {len(files)} files")

        with check(f"The classfiles folder [{self.classfiles_folder}]"):
            assert self.classfiles_folder.exists(), "should exists"
            assert self.classfiles_folder.is_dir(), "should be a folder"
            files = list(self.classfiles())
            assert len(files) > 0, "should contain class files"
            logger.info(f"Found {len(files)} files")

        with check(f"The decompiled folder [{self.decompiled_folder}]"):
            assert self.decompiled_folder.exists(), "should exists"
            assert self.decompiled_folder.is_dir(), "should be a folder"
            files = list(self.decompiledfiles())
            assert len(files) > 0, "should contain decompiled class files"
            logger.info(f"Found {len(files)} files")

            for cn in self.classes():
                x = self.findclass(cn)
                logger.info(f"Checking if {cn.dotted()} is decompiled.")
                assert x["name"] == cn.slashed(), f"could not decompile {cn.dotted()}"

        with check(f"The case file [{self.case_file}]"):
            assert self.case_file.exists(), "should exist"
            assert len(self.cases) > 0, "cases should be parsable and at least one"
            logger.info(f"Found {len(self.cases)} cases")

        for method, _ in self.case_methods():
            with check(f"The method: [{method}]"):
                try:
                    for opr in self.method_opcodes(method):
                        str(opr)
                        str(opr.real())
                except NotImplementedError as e:
                    raise AssertionError("All operations should be supported") from e
