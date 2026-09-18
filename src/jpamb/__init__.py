"""
jpamb

This module provides the basic data model for working with the JPAMB.

"""

import json
import subprocess
import sys
from collections import Counter, defaultdict
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import NoReturn

import runit

import jvm
import jvm.state
import sexpr
from jpamb.analyse import (
    QUERIES as QUERIES,
)
from jpamb.analyse import (
    AnalysisInfo as AnalysisInfo,
)
from jpamb.analyse import (
    Category as Category,
)
from jpamb.analyse import (
    Duration as Duration,
)
from jpamb.analyse import (
    Prediction as Prediction,
)
from jpamb.analyse import (
    Tracker as Tracker,
)
from jpamb.analyse import (
    Wager as Wager,
)
from jpamb.case import Case, Input
from jpamb.utils import DockerRunner, Effect, HealthChecker, HealthIssue


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

        checker = HealthChecker(eff=eff, failfast=failfast)
        check = checker.check

        if docker is not None:
            with check("docker"):
                docker.run(["java", "--version"], eff=eff)

        with check("The timer"):
            x = runit.timer.sieve(1000)
            if x != 7919:
                checker.raise_issue("should find correct prime.")

        with check(f"The source folder [{self.sourcefiles_folder}]"):
            if not self.sourcefiles_folder.exists():
                checker.raise_issue("should exists")
            if not self.sourcefiles_folder.is_dir():
                checker.raise_issue("should be a folder")
            files = list(self.sourcefiles())
            if not len(files) > 0:
                checker.raise_issue("should contain source files")
            eff.info(f"Found {len(files)} files")

        with check(f"The classfiles folder [{self.classfiles_folder}]"):
            if not self.classfiles_folder.exists():
                checker.raise_issue("should exists")
            if not self.classfiles_folder.is_dir():
                checker.raise_issue("should be a folder")
            files = list(self.classfiles(eff=eff))
            if not len(files) > 0:
                checker.raise_issue("should contain class files")
            eff.info(f"Found {len(files)} files")

        with check(f"The decompiled folder [{self.decompiled_folder}]"):
            if not self.decompiled_folder.exists():
                checker.raise_issue("should exists")
            if not self.decompiled_folder.is_dir():
                checker.raise_issue("should be a folder")
            files = list(self.decompiledfiles())
            if not len(files) > 0:
                checker.raise_issue("should contain decompiled class files")
            eff.info(f"Found {len(files)} files")

            for cn in self.classes(eff=eff):
                x = self.findclass(cn, eff=eff)
                eff.info(f"Checking if {cn.dotted()} is decompiled.")
                if x["name"] != cn.slashed():
                    checker.raise_issue(f"could not decompile {cn.dotted()}")

        with check(f"The case file [{self.case_file}]"):
            if not self.case_file.exists():
                checker.raise_issue("should exist")
            if not len(self.cases) > 0:
                checker.raise_issue("cases should be parsable and at least one")
            eff.info(f"Found {len(self.cases)} cases")

        with check("Opcodes"):
            for method in self.case_methods():
                eff.info(f"Checking if the opcodes from {method} are handeled")
                try:
                    for opr in self.method_opcodes(method, eff=eff):
                        str(opr)
                        str(opr.real())
                except NotImplementedError as e:
                    raise HealthIssue(f"All operations should be supported: {e}") from e

        checker.done()

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


def getcase(
    name: str,
    version: str,
    group: str,
    tags: list[str],
    for_science: bool,
) -> tuple[jvm.AbsMethodID, Input | None, int]:
    """Get the case from the program arguments."""

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

    sys.exit(0)


def parse_methodid(mid) -> jvm.AbsMethodID:
    return jvm.AbsMethodID.decode(mid)


def parse_input(i) -> Input | None:
    if i == "ALL":
        return None
    return Input.decode(i)


def emit_init(state: jvm.state.State) -> sexpr.SExpr:
    import jpamb.interpret

    expr = sexpr.sexpr(state)
    out = sexpr.pretty(sexpr.sexpr(jpamb.interpret.Init(expr)), indent=2)
    print(sexpr.pretty(expr, indent=2), file=sys.stderr)
    print(out)
    return expr


def emit_step(
    before: sexpr.SExpr,
    pc: jvm.state.PC,
    after: jvm.state.State,
) -> sexpr.SExpr:
    import jpamb.interpret

    assert sexpr.issexpr(before), "Input the output of emit_step or emit_init"
    assert isinstance(pc, jvm.state.PC), f"Expected PC but got {pc!r}"

    expr = sexpr.sexpr(after)
    diff = sexpr.diff(before, expr)
    out = sexpr.pretty(sexpr.sexpr(jpamb.interpret.Step(pc, tuple(diff))), indent=2)
    print(sexpr.pretty(expr, indent=2), file=sys.stderr)
    print(out)
    return expr
