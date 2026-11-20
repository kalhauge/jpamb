import json
import subprocess
from collections import Counter, OrderedDict
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path

import runit

import jvm
import jvm.state
import sexpr
from jpamb import interpret
from jpamb.case import Benchmark, Case, Control, Coverage, Experiment
from jpamb.utils import DockerRunner, Effect, HealthChecker, HealthIssue
from jpamb.version import __version__


@dataclass(frozen=True)
class Suite:
    """The suite!"""

    workdir: Path

    @classmethod
    def from_workdir(cls, workdir: Path):
        return cls(workdir)

    def __post_init__(self):
        assert self.workdir.is_absolute(), f"Assuming that {self.workdir} is absolute."

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

    def sourcefiles(self, *, eff: Effect) -> Iterable[Path]:
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

    def cases(self, *, eff: Effect) -> Iterable[Case]:
        for case in self.case_file.read_text().splitlines():
            yield Case.decode(case)

    def experiments(self, *, eff: Effect) -> Iterable[Experiment]:
        entries = set()
        for case in self.cases(eff=eff):
            if not case.experiment.entry in entries:
                entries.add(case.experiment.entry)
                yield Experiment(case.experiment.entry, None)

            yield case.experiment

    @property
    def benchmark_file(self) -> Path:
        return self.stats_folder / "benchmark.sexp"

    def benchmark(self, *, eff: Effect) -> Benchmark:
        code = self.benchmark_file.read_text()
        benchmark_cc = sexpr.from_string(code)[0]
        return Benchmark.from_sexpr(benchmark_cc)

    @property
    def version(self) -> str:
        return __version__

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
            files = list(self.sourcefiles(eff=eff))
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

        cases = []
        entries = set()

        with check(f"The case file [{self.case_file}]"):
            if not self.case_file.exists():
                checker.raise_issue("should exist")

            cases = list(self.cases(eff=eff))
            if not len(cases) > 0:
                checker.raise_issue("cases should be parsable and at least one")
            eff.info(f"Found {len(cases)} cases")

            for case in cases:
                entries.add(case.methodid)

            eff.info(f"Found {len(entries)} entries")

        with check(f"The benchmark file [{self.benchmark_file}]"):
            if not self.benchmark_file.exists():
                checker.raise_issue("should exist")

            benchmark = self.benchmark(eff=eff)

            for case in cases:
                with check(f"{case}"):
                    try:
                        control = benchmark.experiments[case.experiment]
                    except KeyError:
                        checker.raise_issue(
                            f"Could not find {case.experiment} in experiments"
                        )

                    if case.results != control.results:
                        checker.raise_issue(
                            f"Expected {case.results} = {control.results} "
                        )

                    try:
                        all_experiment = Experiment(case.methodid, None)
                        all_control = benchmark.experiments[all_experiment]
                    except KeyError:
                        checker.raise_issue(
                            f"Could not find {all_experiment} in experiments"
                        )

                    if not case.result in all_control.results:
                        checker.raise_issue(
                            f"Expected {case.result} in {all_control.results} experiments"
                        )

        with check("Opcodes"):
            for entry in entries:
                eff.info(f"Checking if the opcodes from {entry} are handeled")
                try:
                    for opr in self.method_opcodes(entry, eff=eff):
                        str(opr)
                        str(opr.real())
                except NotImplementedError as e:
                    raise HealthIssue(f"All operations should be supported: {e}") from e

        checker.done()

    def build(self, *, docker: DockerRunner, eff: Effect):
        with eff.context("Compiling"):
            docker.run(
                ["javac", "-g", "-d", "target/classes"]
                + [
                    a.relative_to(self.workdir).as_posix()
                    for a in self.sourcefiles(eff=eff)
                ],
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
                    timeout=30,
                    eff=eff,
                )
                file = self.decompiledfile(cl)
                file.parent.mkdir(exist_ok=True, parents=True)
                with open(file, "w", encoding="utf-8") as f:
                    json.dump(json.loads(res), f, indent=2, sort_keys=True)

    def test(self, *, docker: DockerRunner, eff: Effect):
        with eff.context("Testing"):
            for case in self.cases(eff=eff):
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

    def run_benchmark(self, dynamic: interpret.Config, *, eff: Effect):
        with eff.context("Benchmark"):
            benchmark = Benchmark(OrderedDict())

            for case in self.cases(eff=eff):
                with eff.context(case):
                    reachable = set()
                    result = dynamic.run_experiment(
                        case.experiment,
                        workdir=self.workdir,
                        eff=eff,
                    )
                    if result.response is None:
                        eff.error(f"No response for {case.experiment}")
                        continue
                    for step in result.response.steps:
                        reachable.add(step.pc)

                    methods = sorted({pc.method for pc in reachable})

                    coverage = OrderedDict()
                    for m in methods:
                        offsets = {pc.offset for pc in reachable if pc.method == m}
                        coverage[m] = Coverage(
                            reachable=offsets,
                        )

                    control = Control(coverage=coverage, results={case.result})
                    benchmark[case.experiment] = control
                    eff.info(f"Found {sexpr.pretty(sexpr.sexpr(control), indent=2)}")

        self.benchmark_file.write_text(sexpr.pretty(sexpr.sexpr(benchmark), indent=2))

    def document(self, *, eff: Effect):
        with eff.context("Documenting"):
            opcode_counts = Counter()
            opcode_urls = {}
            class_opcodes = {}
            for experiment in self.experiments(eff=eff):
                name = str(experiment.entry.classname).split(".")[-1]
                class_opcodes.setdefault(name, set())
                list_ops = []
                for opcode in self.method_opcodes(experiment.entry, eff=eff):
                    index = opcode.mnemonic()  # opcode.real().split()[0]
                    list_ops.append(index)

                    opcode_urls[index] = (
                        opcode.mnemonic(),
                        opcode.url(),
                        opcode,
                    )

                    opcode_counts[index] += 1

                for o in list_ops:
                    class_opcodes[name].add(o)

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
                    rel = Path("src") / source.relative_to(source.parent.parent)
                    giturl = f"{rel.as_posix()}?plain=1#L{getsourcelines(opcode.__class__)[1]}"

                    document.write(
                        f"| [{mnemonic}]({url}) | [{opcode.__class__.__name__}]({giturl})"
                        f" | {in_classes} | {count} |\n"
                    )
