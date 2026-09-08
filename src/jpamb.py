"""
jpamb

This module provides the basic data model for working with the JPAMB.

"""

import collections
import math
import io
import re
import shlex
import subprocess
import sys
from abc import ABC, abstractmethod
from collections import Counter, OrderedDict, defaultdict
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import NoReturn, Self, TextIO

import runit
from click import File

import jvm
import jvm.state
import sexpr
from jpamb_utils import DockerRunner, Effect


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
    tags: tuple[str, ...]
    system: str

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

    def __sexpr__(self) -> sexpr.SExpr:
        return sexpr.from_dataclass(self)

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> Self:
        return sexpr.dataclass_from_sexpr(expr, target=cls)


class Prediction(ABC):
    @abstractmethod
    def as_wager(self, categories: "dict[str, Wager]") -> "Wager": ...

    @staticmethod
    def parse(string: str) -> "Wager | Category":
        if m := re.match(r"([^%]*)\%", string):
            p = float(m.group(1)) / 100
            return Wager.from_probability(p)
        else:
            try:
                return Wager(float(string))
            except ValueError:
                return Category(string)

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> "Wager | Category":
        errors = []
        try:
            return Wager.from_sexpr(expr)
        except ValueError as e:
            errors.append(e)

        try:
            return Category.from_sexpr(expr)
        except ValueError as e:
            errors.append(e)

        raise sexpr.FromSExprError(
            f"Could not parse Prediction: {''.join('\n{e}' for e in errors)}"
        )


@dataclass(frozen=True, slots=True)
class Wager(Prediction):
    wager: float

    def __post_init__(self):
        if math.isnan(self.wager):
            raise ValueError("wager cannot be nan")

    @classmethod
    def from_probability(cls, p: float) -> Self:
        negate = False
        if p < 0.5:
            p = 1 - p
            negate = True
        if p == 1:
            x = float("inf")
        else:
            x = (1 - 2 * p) / (-1 + p) / 2
        return cls(-x if negate else x)

    def to_probability(self) -> float:
        if self.wager == float("-inf"):
            return 0.0
        if self.wager == float("inf"):
            return 0.0
        w = abs(self.wager) * 2
        r = (w + 1) / (w + 2)
        return r if self.wager > 0 else 1 - r

    def as_wager(self, categories: dict[str, Self]) -> Self:
        return self

    def score(self, happens: bool):
        wager = (-1 if not happens else 1) * self.wager
        if wager > 0:
            if wager == float("inf"):
                return 1
            else:
                return 1 - 1 / (wager + 1)
        else:
            return wager

    def reward(self):
        wager = math.fabs(self.wager)
        if wager == float("inf"):
            return 1
        else:
            return 1 - 1 / (wager + 1)

    def __str__(self):
        return f"{self.wager:+0.2}"

    def __json__(self):
        return self.wager

    def __sexpr__(self) -> sexpr.SExpr:
        return str(self.wager)

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> Self:
        return cls(float(sexpr.str_from_sexpr(expr)))


@dataclass(frozen=True, slots=True)
class Category(Prediction):
    name: str

    def __json__(self):
        return self.name

    def as_wager(self, categories: "dict[Category, Wager]") -> Wager:
        return categories.get(self, Wager(0))

    def __str__(self):
        return self.name

    @classmethod
    def decode(cls, code: str) -> Self:
        return cls(code)

    def encode(self) -> str:
        return self.name

    def __sexpr__(self) -> sexpr.SExpr:
        return self.name

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> Self:
        return cls(sexpr.str_from_sexpr(expr))


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
            prediction = Prediction.parse(pred)
            predictions[query] = prediction
        return Response(predictions), warnings

    def score(self, correct: set[str], categories: dict[Category, Wager] | None = None):
        if categories is None:
            categories = {}

        total = 0
        for q, prd in self.predictions.items():
            total += prd.as_wager(categories).score(q in correct)
        return total

    @classmethod
    def from_json(cls, json):
        return cls({k: Wager(v) for k, v in json.items()})

    def __sexpr__(self) -> sexpr.SExpr:
        return sexpr.from_dataclass(self)

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> Self:
        return sexpr.dataclass_from_sexpr(expr, target=cls)


@dataclass(frozen=True)
class Suite:
    """The suite!"""

    workdir: Path
    cases: tuple[Case, ...]

    @classmethod
    def from_workdir(cls, workdir: Path, *, eff: Effect):
        cases = []

        case_file = workdir / "target" / "stats" / "cases.txt"
        with (
            eff.context(f"Reading cases from {case_file}"),
            open(case_file, encoding="utf-8") as f,
        ):
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

    def cache_folder(self, *, eff: Effect) -> Path:
        cache = self.workdir / ".cache" / "jpamb"
        cache.mkdir(parents=True, exist_ok=True)

        cache_gitignore = cache / ".gitignore"
        if not cache_gitignore.exists():
            (cache / ".gitignore").write_text("**/*\n")

        return cache

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
    ) -> Iterator[jvm.Opcode]:
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
    def stats_file(self) -> Path:
        return self.stats_folder / "stats.json"

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

    def case_opcodes(self, eff: Effect) -> Iterator[jvm.Opcode]:
        for m in self.case_methods():
            yield from self.method_opcodes(m, eff=eff)

    def checkhealth(self, docker, *, eff: Effect, failfast=False):
        """Checks the health of the repository through a sequence of tests"""

        def check(msg):
            return _check(msg, failfast=failfast, eff=eff)

        if docker is not None:
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
            for method in self.case_methods():
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
                        eff.success("Correct")
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
                eff.context("Writing OPCODES.md"),
                open("OPCODES.md", "w", encoding="utf-8") as document,
            ):
                from inspect import getsourcefile, getsourcelines

                document.write("#Bytecode instructions\n")
                document.write("| Mnemonic | Opcode Name |  Exists in |  Count |\n")
                document.write("| :---- | :---- | :----- | -----: |\n")

                for op, count in opcode_counts.most_common():
                    eff.debug(f"Handeling {op} {count}")
                    (mnemonic, url, opcode) = opcode_urls[op]
                    in_classes = ""

                    for classname, opcodes in class_opcodes.items():
                        if op in opcodes:
                            in_classes += " " + classname
                    file = getsourcefile(opcode.__class__)
                    assert file is not None
                    source = Path(file)
                    rel = Path("utils") / source.relative_to(source.parent.parent)
                    giturl = f"{rel.as_posix()}?plain=1#L{getsourcelines(opcode.__class__)[1]}"

                    document.write(
                        f"| [{mnemonic}]({url}) | [{opcode.__class__.__name__}]({giturl})"
                        f" | {in_classes} | {count} |\n"
                    )


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
                raise AssertionError(f"{reason} {e.args!s}") from e
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


@dataclass(frozen=True, slots=True)
class Duration:
    absolute: int
    relative: float

    def __sexpr__(self) -> sexpr.SExpr:
        return sexpr.from_dataclass(self)

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> Self:
        return sexpr.dataclass_from_sexpr(expr, target=cls)


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    response: Response
    duration: Duration
    calibrates: tuple[int, ...]

    def __post_init__(self):
        if not isinstance(self.calibrates, tuple):
            raise TypeError(f"Expected tuple, but got {self.calibrates}")

    def __sexpr__(self) -> sexpr.SExpr:
        return sexpr.from_dataclass(self)

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> Self:
        return sexpr.dataclass_from_sexpr(expr, target=cls)


@dataclass
class Tracker:
    hits: int = 0
    counts: int = 0

    @property
    def misses(self) -> int:
        return self.counts - self.hits

    def approximate(self) -> Wager:
        return Wager.from_probability((self.hits + 1) / (self.counts + 2))

    def wager(self) -> Wager:
        return Wager.from_probability(self.hits / self.counts)

    def __sexpr__(self) -> sexpr.SExpr:
        return sexpr.from_dataclass(self)

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> Self:
        return sexpr.dataclass_from_sexpr(expr, target=cls)


@dataclass(frozen=True, slots=True)
class AnalysisConfig:
    cmd: tuple[str, ...]
    analysis: AnalysisInfo
    experiments: OrderedDict[jvm.AbsMethodID, set[str]]
    iterations: int
    timeout: float

    def __post_init__(self):
        assert isinstance(self.experiments, OrderedDict), (
            f"Expected orederd dict but got {self.experiments}"
        )

    def display(self, *, file=sys.stdout):
        file.write(f"Cmd:           {shlex.join(self.cmd)}\n")
        file.write("Analysis:\n")
        file.write(f" Name:         {self.analysis.name}\n")
        file.write(f" Version:      {self.analysis.version}\n")
        file.write(f" Group:        {self.analysis.group}\n")
        file.write(f" Tags:         {self.analysis.tags}\n")
        file.write(f" System:       {self.analysis.system}\n")
        file.write(f"Experiments:   {len(self.experiments)}\n")
        file.write(f"Iterations:    {self.iterations}\n")
        file.write(f"Timeout:       {self.timeout}\n")

    def __sexpr__(self) -> sexpr.SExpr:
        return sexpr.from_dataclass(self)

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> Self:
        return sexpr.dataclass_from_sexpr(expr, target=cls)

    @classmethod
    def from_cmd(
        cls,
        cmd: tuple[str],
        experiments: Iterable[tuple[jvm.AbsMethodID, set[str]]],
        *,
        timeout: float,
        iterations: int,
        eff: Effect,
    ) -> "Self | None":
        with eff.context("Getting info about analysis"):
            try:
                out = eff.run(
                    cmd + ("info",),
                    timeout=timeout,
                )
                info = AnalysisInfo.parse(out)
            except subprocess.CalledProcessError as e:
                eff.error(f"Ran {shlex.join(cmd)} info, and got error:\n{e.stderr}")
                return None
            except ValueError:
                eff.error("Expected info, but got:")
                for o in out.splitlines():
                    eff.error(o)
                return None

        return cls(
            cmd,
            info,
            experiments=OrderedDict(experiments),
            timeout=timeout,
            iterations=iterations,
        )

    def run_experiment(
        self, methodid, *, pedantic: bool = True, eff: Effect
    ) -> AnalysisResult | None:
        try:
            experiment = eff.experiment(
                self.cmd + (methodid.encode(),),
                timeout=self.timeout,
            )
        except subprocess.CalledProcessError as e:
            eff.warning(f"Ran {shlex.join(self.cmd)} info, and got error:\n{e.stderr}")
            return None
        except subprocess.TimeoutExpired as e:
            eff.warning(
                f"Ran {shlex.join(self.cmd)} info, and timed out after {e.timeout} seconds"
            )
            return None

        response, warns = Response.parse(experiment.output)

        if warns:
            for warn in warns:
                eff.warning(warn)
            if pedantic:
                return None

        return AnalysisResult(
            response,
            Duration(experiment.time_ns, experiment.time_relative),
            tuple(experiment.calibrations_ns),
        )


@dataclass
class ResultRow:
    methodname: jvm.AbsMethodID
    score: float
    rel_time: float
    abs_time: float

    def as_row(self) -> list[str]:
        return [
            str(self.methodname),
            f"{self.score:>7.2f}",
            f"{self.rel_time:>7.2f} Db",
            f"{self.abs_time / 10**9:>7.3f} s",
        ]


@dataclass(frozen=True)
class ResultSummary:
    config: AnalysisConfig
    results: list[tuple[str, list[ResultRow]]]
    categories: list[tuple[Category, Tracker]]
    total_score: float
    mean_rel_time: float
    total_abs_time: float

    def autolab_json(self):
        student_eval = {
            "scores": {},
        }

        student_eval["scores"]["Total"] = self.total_score
        student_eval["scores"]["Time"] = 100 / max(1, self.mean_rel_time)
        student_eval["scores"]["Categories"] = 100 / len(self.categories)

        return student_eval

    def display(self, file=sys.stdout):
        self.config.display(file=file)

        groups = [
            [
                "Method",
                "Score",
                "Time (rel)",
                "Time (abs)",
            ],
        ]

        groups += [(n, [r.as_row() for r in res]) for n, res in self.results]

        groups += [
            (
                "Totals",
                [
                    [
                        "",
                        "Score",
                        "Time (rel)",
                        "Time (abs)",
                    ],
                    [
                        "Total",
                        f"{self.total_score:>7.2f}",
                        f"{self.mean_rel_time:>7.2f} Db",
                        f"{self.total_abs_time / 10**9:>7.3f} s",
                    ],
                ],
            )
        ]
        dump_table(groups, align="<>>>", file=file)

        file.write("\n--- Categories ---\n\n")
        file.write(
            "The following are the categories you identified, including\n"
            "how often they were found versus missed. From this, we\n"
            "calculate the optimal wager and the corresponding reward.\n"
            "Finally, the score represents the proportion of the total\n"
            "score attributed to this category.\n\n"
        )

        categories = [
            ["Category", "Found", "Missed", "Percentage", "Wager", "Reward", "Score"]
        ]

        categories += [
            [
                c.name,
                f"{v.hits / self.config.iterations:.1f}",
                f"{v.misses / self.config.iterations:.1f}",
                f"{v.wager().to_probability():0.2%}",
                f"{v.wager()}",
                f"{v.wager().reward():0.2}",
                f"{(v.wager().score(False) * v.misses + v.wager().score(True) * v.hits) / self.config.iterations:.2f}",
            ]
            for c, v in self.categories.items()
        ]

        dump_table(categories, align="<>>>>>>", file=file)


@dataclass(frozen=True)
class AnalysisSummary:
    config: AnalysisConfig
    results: dict[jvm.AbsMethodID, list[AnalysisResult]]

    def __sexpr__(self) -> sexpr.SExpr:
        return sexpr.from_dataclass(self)

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> Self:
        return sexpr.dataclass_from_sexpr(expr, target=cls)

    def calculate_categories(self) -> dict[Category, Tracker]:
        experiments = dict(self.config.experiments)

        categories = defaultdict(Tracker)

        for method, results in self.results.items():
            expected = experiments[method]

            for result in results:
                for key, pred in result.response.predictions.items():
                    if isinstance(pred, Category):
                        tracker = categories[pred]
                        tracker.counts += 1
                        if key in expected:
                            tracker.hits += 1

        return dict(categories)

    def score_results(self) -> ResultSummary:
        byclasses = {}
        for method in self.results:
            byclasses.setdefault(method.classname, set()).add(method)

        total_score = total_abs_time = total_rel_time = 0

        experiments = dict(self.config.experiments)
        groups = []

        tracker_categories = self.calculate_categories()

        categories = {k: v.wager() for k, v in tracker_categories.items()}

        hits = 0
        for clz, methods in sorted(byclasses.items()):
            rows = []
            for method in sorted(methods):
                results = self.results[method]
                expected = experiments[method]
                score = mean(
                    result.response.score(expected, categories) for result in results
                )
                rel_time = mean(result.duration.relative for result in results)
                abs_time = mean(result.duration.absolute for result in results)

                rows += [ResultRow(method.extension, score, rel_time, abs_time)]

                total_score += score
                total_rel_time += rel_time
                total_abs_time += abs_time
                hits += 1

            groups += [(str(clz), rows)]

        return ResultSummary(
            self.config,
            groups,
            tracker_categories,
            total_score,
            total_rel_time / hits,
            total_abs_time,
        )

    def report(cls, *, file: TextIO, eff: Effect) -> None:
        content = sexpr.pretty(cls.__sexpr__(), indent=2)
        try:
            file.write(content)
            eff.success(f"Succesfully wrote report to {file.name}")
        except OSError:
            eff.error("Failed to write report")


def dump_table(groups, *, align, file):
    rows = []
    for group in groups:
        if isinstance(group, list):
            rows += [group]
        else:
            c, _rows = group
            rows += [[""] * len(align)]
            rows += [[c] + [""] * (len(align) - 1)]
            rows += [["  " + h, *rest] for h, *rest in _rows]

    sizes = [max(map(len, col)) for col in zip(*rows)]

    for row in rows:
        print("  ".join(f"{r:{a}{s}}" for r, a, s in zip(row, align, sizes)), file=file)


def mean(results):
    res = [r for r in results if not math.isnan(r)]
    return sum(res) / len(res)


@dataclass
class AnalysisState:
    config: AnalysisConfig
    progress: int = 0
    results: dict[jvm.AbsMethodID, list[AnalysisResult]] = field(default_factory=dict)
    categories: dict[Category, Tracker] = field(default_factory=dict)

    def __sexpr__(self) -> sexpr.SExpr:
        return sexpr.from_dataclass(self)

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> Self:
        return sexpr.dataclass_from_sexpr(expr, target=cls)

    def run_next(self, *, score_limit: float | None = None, eff: Effect) -> bool | None:
        no_experiments = len(self.config.experiments)
        iteration = self.progress // no_experiments

        if iteration >= self.config.iterations:
            return None

        # TODO fix this
        methodid, expected = list(self.config.experiments.items())[
            self.progress % no_experiments
        ]

        with eff.context(
            f"Iteration {iteration + 1}/{self.config.iterations}, Experiment {self.progress % no_experiments + 1}/{no_experiments} {methodid}"
        ):
            result = self.config.run_experiment(methodid, eff=eff)

            if result is None:
                return False

            if iteration > 0:
                # If we are at our second iteration, use the categories.
                categories = {k: v.wager() for k, v in self.categories.items()}
            else:
                eff.info("Note: Categories are not approximated in the first iteration")
                categories = {}

            total_score = 0
            for key in QUERIES:
                pred = result.response.predictions[key]
                real = pred.as_wager(categories)
                score = real.score(key in expected)
                is_good = "*" if key in expected else " "
                eff.debug(
                    f"[{is_good}] {key!r:<20} | {score:>7.2f}   from {pred!s:>10} (~ {real.wager:>+7.2f})"
                )
                total_score += score
            eff.info(f"Approximate Score:          {total_score:>7.2f}")

            if iteration > 0 and score_limit is not None and total_score <= score_limit:
                eff.error(f"Total {total_score} below limit {score_limit}")
                return False

            for key, pred in result.response.predictions.items():
                if isinstance(pred, Category):
                    tracker = self.categories.setdefault(pred, Tracker())
                    tracker.counts += 1
                    if key in expected:
                        tracker.hits += 1

            self.results.setdefault(methodid, []).append(result)

        self.progress += 1
        return True

    def summary(self) -> AnalysisSummary:
        return AnalysisSummary(
            self.config,
            self.results,
        )


def check_state_equality(s1: AnalysisState, s2: AnalysisState):
    assert s1.results == s2.results, f"Results differ\n{s1.results}\n{s2.results}"
    assert s1.config == s2.config, f"Config differ\n{s1.config}\n\n{s2.config}"
    assert s1.config == s2.config, "Configs differ"
    assert s1.categories == s2.categories, (
        f"Categories differ\n{s1.categories}\n\n{s2.categories}"
    )
    assert s1.progress == s2.progress, (
        f"Progress differ\n{s1.progress}\n\n{s2.progress}"
    )


def verify_summary(summary: AnalysisSummary) -> None:
    result_summary = summary.score_results()
    autolab_table = result_summary.autolab_json()

    autolab_total = round(
        sum([v for k, v in autolab_table["score"].items() if k != "RelativeTime"]), 3
    )

    assert result_summary.total_score == autolab_total, (
        f"Autolab score: {autolab_total} differs from summary score: {result_summary.total_score}"
    )

    return autolab_table
