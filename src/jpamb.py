"""
jpamb

This module provides the basic data model for working with the JPAMB.

"""

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
import collections
from collections import defaultdict
import re
import os
import subprocess
from collections import Counter

from jpamb_utils import Effect, DockerRunner
import runit

from typing import Iterable, NoReturn

import sexpr
import jvm


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
class Classification:
    name: str

    def __json__(self):
        return self.name

    def score(self, happens: bool, categories):
        return Prediction.from_probability(categories[self.name]).score(
            happens, categories
        )


@dataclass(frozen=True)
class Prediction:
    wager: float

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

    def score(self, happens: bool, categories: dict[str, float] | None = None):
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

    def __json__(self):
        return self.wager


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
    predictions: dict[str, Prediction | Classification]

    @staticmethod
    def parse_prediction(string: str) -> Prediction | Classification:
        if m := re.match(r"([^%]*)\%", string):
            p = float(m.group(1)) / 100
            return Prediction.from_probability(p)
        else:
            try:
                return Prediction(float(string))
            except ValueError:
                return Classification(string)

    @staticmethod
    def parse(out):
        predictions = {}
        warnings = []
        for line in out.splitlines():
            try:
                query, pred = line.split(";")
            except ValueError:
                warnings.append(f"bad line: {line}")
                continue
            if query not in QUERIES:
                warnings.append(f"{query!r} not a known query")
                continue
            prediction = Response.parse_prediction(pred)
            predictions[query] = prediction
        return Response(predictions), warnings

    def score(self, correct: set[str], categories: dict[str, float] | None = None):
        if categories is None:
            categories = dict()

        total = 0
        for q, prd in self.predictions.items():
            total += prd.score(q in correct, categories)
        return total

    @classmethod
    def from_json(cls, json):
        return cls(
            {
                k: Prediction(v) if isinstance(v, float) else Classification(v)
                for k, v in json.items()
            }
        )


@dataclass(frozen=True)
class Step:
    before: sexpr.SExpr
    opr: jvm.Opcode
    after: sexpr.SExpr

    @classmethod
    def parse_many(cls, code: str) -> "list[Step]":
        return [Step(b, opr, a) for [b, opr, a] in sexpr.from_string(code)]


@dataclass(frozen=True)
class Suite:
    """The suite!"""

    workdir: Path
    cases: tuple[Case]

    @classmethod
    def from_cwd(cls):
        return cls(Path.cwd())

    @classmethod
    def from_env(cls):
        return cls(Path(os.environ.get("JPAMB_WORKDIR")).absolute())

    @classmethod
    def from_workdir(cls, workdir: Path, *, eff: Effect):
        cases = []

        case_file = workdir / "target" / "stats" / "cases.txt"
        with eff.context(f"Reading cases from {case_file}"):
            with open(case_file, encoding="utf-8") as f:
                cases = tuple(Case.decode(line) for line in f)

        return cls(workdir, cases)

    def __post_init__(self):
        assert self.workdir.is_absolute(), f"Assuming that {self.workdir} is absolute."
        assert self.cases, "Expected cases"

        for case in self.cases:
            assert isinstance(case, Case), f"Expected Case but got {case!r}"

    @property
    def stats_folder(self) -> Path:
        """The folder to place the statistics about the repository"""
        return self.workdir / "target" / "stats"

    @property
    def classfiles_folder(self) -> Path:
        """The folder containing the class files"""
        return self.workdir / "target" / "classes"

    def classfiles(self, *, eff: Effect) -> Iterable[Path]:
        yield from self.classfiles_folder.glob("**/*.class")

    def classfile(self, cn: jvm.ClassName) -> Path:
        return (self.classfiles_folder / Path(*cn.packages) / cn.name).with_suffix(
            ".class"
        )

    @property
    def sourcefiles_folder(self) -> Path:
        """The folder containing the class files"""
        return self.workdir / "cases"

    def sourcefiles(self) -> Iterable[Path]:
        yield from self.sourcefiles_folder.glob("**/*.java")

    def sourcefile(self, cn: jvm.ClassName) -> Path:
        return (
            self.sourcefiles_folder / Path(*cn.packages) / cn.name.split("$")[0]
        ).with_suffix(".java")

    @property
    def decompiled_folder(self) -> Path:
        return self.workdir / "target" / "decompiled"

    def decompiledfiles(self) -> Iterable[Path]:
        yield from self.decompiled_folder.glob("**/*.json")

    def decompiledfile(self, cn: jvm.ClassName) -> Path:
        return (self.decompiled_folder / Path(*cn.packages) / cn.name).with_suffix(
            ".json"
        )

    def findclass(self, cn: jvm.ClassName, *, eff: Effect) -> dict:
        import json

        with open(self.decompiledfile(cn), encoding="utf-8") as fp:
            return json.load(fp)

    def findmethod(self, methodid: jvm.Absolute[jvm.MethodID], *, eff: Effect) -> dict:
        methods = self.findclass(methodid.classname, eff=eff)["methods"]
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

    def getmethod(self, methodid: jvm.AbsMethodID, *, eff: Effect) -> jvm.Method:
        """Get the json for a method and covert it to a Method"""
        return jvm.Method.from_json(methodid, self.findmethod(methodid, eff=eff))

    def method_opcodes(
        self, method: jvm.Absolute[jvm.MethodID], *, eff: Effect
    ) -> list[jvm.Opcode]:
        for op in self.findmethod(method, eff=eff)["code"]["bytecode"]:
            yield jvm.Opcode.from_json(op)

    def method_max_locals(
        self, method: jvm.Absolute[jvm.MethodID], *, eff: Effect
    ) -> int:
        return self.findmethod(method, eff=eff)["code"]["max_locals"]

    def classes(self, *, eff: Effect) -> Iterable[jvm.ClassName]:
        for file in self.classfiles(eff=eff):
            yield jvm.ClassName.from_parts(
                *file.relative_to(self.classfiles_folder).with_suffix("").parts
            )

    @property
    def case_file(self) -> Path:
        return self.stats_folder / "cases.txt"

    @property
    def version(self):
        with open(self.workdir / "CITATION.cff", encoding="utf-8") as f:
            import yaml

            return yaml.safe_load(f)["version"]

    def case_methods(self) -> dict[jvm.Absolute[jvm.MethodID], set[str]]:
        methods = defaultdict(set)

        for case in self.cases:
            methods[case.methodid].add(case.result)

        return methods

    def case_opcodes(self, eff: Effect) -> list[jvm.Opcode]:
        for m in self.case_methods().keys():
            yield from self.method_opcodes(m, eff=eff)

    def checkhealth(self, docker, *, eff: Effect, failfast=False):
        """Checks the health of the repository through a sequence of tests"""

        def check(msg):
            return _check(msg, failfast=failfast, eff=eff)

        with check("docker"):
            docker.run(["java", "--version"], eff=eff)

        with check("The timer"):
            x = runit.timer.sieve(1000)
            assert x == 7919, "should find correct prime."

        with check(f"The source folder [{self.sourcefiles_folder}]"):
            assert self.sourcefiles_folder.exists(), "should exists"
            assert self.sourcefiles_folder.is_dir(), "should be a folder"
            files = list(self.sourcefiles())
            assert len(files) > 0, "should contain source files"
            eff.info(f"Found {len(files)} files")

        with check(f"The classfiles folder [{self.classfiles_folder}]"):
            assert self.classfiles_folder.exists(), "should exists"
            assert self.classfiles_folder.is_dir(), "should be a folder"
            files = list(self.classfiles(eff=eff))
            assert len(files) > 0, "should contain class files"
            eff.info(f"Found {len(files)} files")

        with check(f"The decompiled folder [{self.decompiled_folder}]"):
            assert self.decompiled_folder.exists(), "should exists"
            assert self.decompiled_folder.is_dir(), "should be a folder"
            files = list(self.decompiledfiles())
            assert len(files) > 0, "should contain decompiled class files"
            eff.info(f"Found {len(files)} files")

            for cn in self.classes(eff=eff):
                x = self.findclass(cn, eff=eff)
                eff.info(f"Checking if {cn.dotted()} is decompiled.")
                assert x["name"] == cn.slashed(), f"could not decompile {cn.dotted()}"

        with check(f"The case file [{self.case_file}]"):
            assert self.case_file.exists(), "should exist"
            assert len(self.cases) > 0, "cases should be parsable and at least one"
            eff.info(f"Found {len(self.cases)} cases")

        with check("Opcodes"):
            for method in self.case_methods().keys():
                eff.info(f"Checking if the opcodes from {method} are handeled")
                try:
                    for opr in self.method_opcodes(method, eff=eff):
                        str(opr)
                        str(opr.real())
                except NotImplementedError as e:
                    raise AssertionError(
                        f"All operations should be supported: {e}"
                    ) from e

    def build(self, *, docker: DockerRunner, eff: Effect):
        with eff.context("Compiling"):
            docker.run(
                ["javac", "-g", "-d", "target/classes"]
                + [a.relative_to(self.workdir).as_posix() for a in self.sourcefiles()],
                timeout=600,
                eff=eff,
            )

        with eff.context("Building Stats"):
            res = docker.run(
                ["java", "-cp", "target/classes", "jpamb.Runtime"], timeout=60, eff=eff
            )
            self.case_file.parent.mkdir(exist_ok=True, parents=True)
            self.case_file.write_text("\n".join(sorted(res.splitlines())))

        with eff.context("Decompiling"):
            import json

            for cl in self.classes(eff=eff):
                eff.info(f"Decompiling {cl}")
                res = docker.run(
                    [
                        "jvm2json",
                        "-s",
                        self.classfile(cl).relative_to(self.workdir).as_posix(),
                    ],
                    eff=eff,
                )
                file = self.decompiledfile(cl)
                file.parent.mkdir(exist_ok=True, parents=True)
                with open(file, "w", encoding="utf-8") as f:
                    json.dump(json.loads(res), f, indent=2, sort_keys=True)

    def test(self, *, docker: DockerRunner, eff: Effect):
        with eff.context("Testing"):
            for case in self.cases:
                with eff.context(f"{case}"):
                    folder = self.classfiles_folder

                    try:
                        res = docker.run(
                            [
                                "java",
                                "-cp",
                                folder.relative_to(self.workdir).as_posix(),
                                "-ea",
                                "jpamb.Runtime",
                                case.methodid.encode(),
                                case.input.encode(),
                            ],
                            timeout=5,
                            eff=eff,
                        )
                    except subprocess.TimeoutExpired:
                        res = "*"

                    if case.result == res.strip():
                        eff.success(f"Correct")
                    else:
                        eff.error(f"Incorrect (got {res.strip()}) expected {case}")

    def document(self, *, eff: Effect):
        with eff.context("Documenting"):
            opcode_counts = Counter()
            opcode_urls = {}
            class_opcodes = {}
            for case in self.cases:
                class_opcodes[str(case.methodid.classname).split(".")[-1]] = set()
                list_ops = []
                for opcode in self.method_opcodes(case.methodid, eff=eff):
                    index = opcode.mnemonic()  # opcode.real().split()[0]
                    list_ops.append(index)

                    opcode_urls[index] = (
                        opcode.mnemonic(),
                        opcode.url(),
                        opcode,
                    )

                    opcode_counts[index] += 1

                for o in list_ops:
                    class_opcodes[str(case.methodid.classname).split(".")[-1]].add(o)

            with (
                eff.context(f"Writing OPCODES.md"),
                open("OPCODES.md", "w", encoding="utf-8") as document,
            ):
                from inspect import getsourcelines, getsourcefile

                document.write("#Bytecode instructions\n")
                document.write("| Mnemonic | Opcode Name |  Exists in |  Count |\n")
                document.write("| :---- | :---- | :----- | -----: |\n")

                for op, count in opcode_counts.most_common():
                    eff.debug(f"Handeling {op} {count}")
                    (mnemonic, url, opcode) = opcode_urls[op]
                    in_classes = ""

                    for classname in class_opcodes:
                        if op in class_opcodes[classname]:
                            in_classes += " " + classname

                    source = Path(getsourcefile(opcode.__class__))
                    rel = Path("utils") / source.relative_to(source.parent.parent)
                    giturl = f"{rel.as_posix()}?plain=1#L{getsourcelines(opcode.__class__)[1]}"

                    document.write(
                        f"| [{mnemonic}]({url}) | [{opcode.__class__.__name__}]({giturl})"
                        f" | {in_classes} | {count} |\n"
                    )


def setup() -> tuple[Suite, Effect]:
    """Get a suite in the current working directory"""
    import sys

    eff = Effect(None)
    return (Suite.from_workdir(Path.cwd(), eff=eff), eff)


@contextmanager
def _check(reason, *, eff: Effect, failfast=False):
    """Used in the checkhealth command"""
    with eff.context(reason):
        try:
            yield
        except AssertionError as e:
            msg = str(e)
            if msg:
                eff.error(f"FAILED: {e}")
            else:
                eff.error("FAILED")
            if failfast:
                raise AssertionError(f"{reason} {str(e.args)}") from e
        else:
            eff.success("ok")


def getmethodid(
    name: str,
    version: str,
    group: str,
    tags: list[str],
    for_science: bool,
) -> jvm.AbsMethodID:
    """Get the method id from the program arguments, or output the info."""

    import sys

    if len(sys.argv) == 2 and sys.argv[1] == "info":
        printinfo(name, version, group, tags, for_science)

    assert len(sys.argv) == 2, f"expected only one argument but got {sys.argv[1:]}"

    mid = sys.argv[1]
    return parse_methodid(mid)


def getcase(
    name: str,
    version: str,
    group: str,
    tags: list[str],
    for_science: bool,
) -> tuple[jvm.AbsMethodID, Input, int]:
    """Get the case from the program arguments."""
    import sys

    if len(sys.argv) == 2 and sys.argv[1] == "info":
        printinfo(name, version, group, tags, for_science)

    assert len(sys.argv) == 4, (
        f"expected exactly three arguments but got {sys.argv[1:]}"
    )

    mid = parse_methodid(sys.argv[1])
    i = parse_input(sys.argv[2])
    max_iter = int(sys.argv[3])

    return mid, i, max_iter


def printinfo(
    name: str,
    version: str,
    group: str,
    tags: list[str],
    for_science: bool,
) -> NoReturn:
    print(name)
    print(version)
    print(group)
    print(",".join(tags))
    if for_science:
        import platform

        print(platform.platform())

    import sys

    sys.exit(0)


def parse_methodid(mid) -> jvm.AbsMethodID:
    return jvm.AbsMethodID.decode(mid)


def parse_input(i) -> Input:
    return Input.decode(i)
