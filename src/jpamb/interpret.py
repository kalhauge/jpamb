import shlex
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Self, TextIO

import jvm
import jvm.state
import sexpr
from jpamb.analyse import AnalysisInfo
from jpamb.case import Benchmark, Control, Experiment
from jpamb.utils import Duration, Effect, dump_table


@dataclass(frozen=True, slots=True)
class Init:
    state: sexpr.SExpr

    def __sexpr__(self) -> sexpr.SExpr:
        return sexpr.from_dataclass(self)

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> Self:
        return sexpr.to_dataclass(expr, target=cls)


@dataclass(frozen=True, slots=True)
class Step:
    pc: jvm.state.PC
    edits: tuple[sexpr.TreeEdit, ...]

    def __sexpr__(self) -> sexpr.SExpr:
        return [
            sexpr.item("step"),
            sexpr.Option("pc", sexpr.sexpr(self.pc)),
        ] + sexpr.items(enumerate(self.edits), keyfmt=lambda a: "edit")

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> Self:
        pc = None
        items = []
        _name, pc, *rest = sexpr.to_options(expr)
        pc = jvm.state.PC.from_sexpr(pc.value)
        for option in rest:
            items.append(sexpr.TreeEdit.from_sexpr(option.value))

        return cls(pc, tuple(items))


@dataclass(frozen=True)
class Response:
    init: Init
    steps: list[Step]

    def __post_init__(self):
        assert isinstance(self.init, Init)

    @staticmethod
    def parse(out) -> tuple[Self, list[str]] | None:
        warnings = []
        steps = []
        exprs = sexpr.from_string(out)

        if not exprs:
            warnings.append("Expected an initial state, but got nothing")
            return None, warnings

        try:
            init = Init.from_sexpr(exprs[0])
        except sexpr.FromSExprError as e:
            warnings.append(
                f"Could not interpret expr {sexpr.pretty(exprs[0])!r} as initial state: {e}"
            )
            return None, warnings

        try:
            for s in exprs[1:]:
                try:
                    steps.append(Step.from_sexpr(s))
                except sexpr.FromSExprError as e:
                    warnings.append(
                        f"Could not interpret expr {sexpr.pretty(s)!r} as a step: {e}"
                    )
        except sexpr.ParseError as e:
            warnings.append(f"Could not parse output: {e}")

        return Response(init, steps), warnings

    def __sexpr__(self) -> sexpr.SExpr:
        return sexpr.from_dataclass(self)

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> Self:
        return sexpr.to_dataclass(expr, target=cls)

    def invalidate(self, *, control: Control, max_steps: int) -> str | None:
        if not self.steps:
            return "No steps where emitted"

        cursor = sexpr.cursor(self.init.state)

        pcs = set()
        found = set()
        for i, step in enumerate(self.steps):
            if i >= max_steps:
                return f"Exceeded {max_steps}"

            pcs.add(step.pc)

            prev_state = cursor.value
            try:
                sexpr.iapply(cursor, step.edits)
            except ValueError as e:
                return f"Could not apply step {i}:\n{e}"

            if isinstance(cursor.value, str):
                found.add(cursor.value)
                cursor.value = prev_state

        uncover = control.reachable() - pcs
        if len(uncover) > 0:
            return f"Did not cover all reachable program points: {''.join(f'\n{pc}' for pc in uncover)}"

        if i + 1 != max_steps and len(control.results - found) > 0:
            return f"The results {control.results - found!r} was not found in the final states reported {found!r}"


@dataclass(frozen=True, slots=True)
class Result:
    __sexprtag__ = "interpret-result"

    experiment: Experiment
    response: Response | None
    duration: Duration
    calibrates: tuple[int, ...]

    def __post_init__(self):
        if not isinstance(self.calibrates, tuple):
            raise TypeError(f"Expected tuple, but got {self.calibrates}")

    def __sexpr__(self) -> sexpr.SExpr:
        return sexpr.from_dataclass(self)

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> Self:
        return sexpr.to_dataclass(expr, target=cls)

    def invalidate(self, *, benchmark: Benchmark, config: "Config") -> str | None:
        if self.response is None:
            return "No reponse created"

        if self.experiment not in benchmark.experiments:
            return f"Experiment {self.experiment} not in benchmarks."

        return self.response.invalidate(
            control=benchmark.experiments[self.experiment],
            max_steps=config.max_steps,
        )


@dataclass(frozen=True, slots=True)
class Config:
    __sexprtag__ = "interpret-config"

    cmd: tuple[str, ...]
    analysis: AnalysisInfo
    experiments: list[Experiment]
    timeout: float
    max_steps: int
    abstract: bool

    def __post_init__(self):
        assert isinstance(self.experiments, list), (
            f"Expected list but got {self.experiments}"
        )

    def display(self, *, file=sys.stdout):
        file.write(f"Cmd:           {shlex.join(self.cmd)}\n")
        self.analysis.display(file=file)
        file.write(f"Experiments:   {len(self.experiments)}\n")
        file.write(f"Max Steps:     {self.max_steps}\n")
        file.write(f"Timeout:       {self.timeout}\n")
        file.write(f"Abstract:      {self.abstract}\n")

    def __sexpr__(self) -> sexpr.SExpr:
        return sexpr.from_dataclass(self)

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> Self:
        return sexpr.to_dataclass(expr, target=cls)

    @classmethod
    def from_cmd(
        cls,
        cmd: tuple[str],
        experiments: Iterable[Experiment],
        *,
        max_steps: int,
        timeout: float,
        eff: Effect,
        abstract: bool,
    ) -> "Self | None":
        with eff.context("Getting info about interpreter"):
            try:
                out = eff.run(
                    cmd + ("info",),
                    timeout=timeout,
                )
                info = AnalysisInfo.parse(out)
            except subprocess.CalledProcessError as e:
                eff.error(f"Ran {shlex.join(cmd)} info, and got error:\n{e.stderr}")
                raise
            except ValueError:
                eff.error("Expected info, but got:")
                for o in out.splitlines():
                    eff.error(o)
                raise

        return cls(
            cmd,
            info,
            experiments=list(experiments),
            timeout=timeout,
            max_steps=max_steps,
            abstract=abstract,
        )

    def run_experiment(
        self,
        experiment: Experiment,
        *,
        pedantic: bool = True,
        eff: Effect,
    ) -> Result:
        cmd = experiment.as_test(self.cmd, self.max_steps)
        duration = Duration(0, 0)
        calibrations_ns = ()
        try:
            result = eff.experiment(
                cmd,
                timeout=self.timeout,
            )
        except subprocess.CalledProcessError as e:
            eff.warning(f"Ran {shlex.join(cmd)}, and got error:\n{e.stderr}")
            response = None
        except subprocess.TimeoutExpired as e:
            eff.warning(
                f"Ran {shlex.join(cmd)}, and timed out after {e.timeout} seconds"
            )
            response = None
        else:
            duration = Duration(result.time_ns, result.time_relative)
            calibrations_ns = tuple(result.calibrations_ns)
            response, warns = Response.parse(result.output)

            if warns:
                for warn in warns:
                    eff.warning(warn)
                if pedantic:
                    response = None

        return Result(
            experiment,
            response,
            duration,
            calibrations_ns,
        )


@dataclass(frozen=True)
class ExperimentScore:
    error: str | None
    steps: int


@dataclass(frozen=True)
class ResultSummary:
    config: Config
    results: list[Result]
    scores: dict[Experiment, ExperimentScore]
    invalid: str | None
    total_steps: int

    def display_autolab(self, file=sys.stdout):
        import json

        student_eval = {}

        student_eval["scores"] = {}
        student_eval["scores"]["Total"] = (
            len(self.results) if self.invalid is None else 0
        )

        json.dump(student_eval, fp=file)
        file.write("\n")

    def display(self, file=sys.stdout):
        self.config.display(file=file)

        file.write("\n")
        table = [["Experiment", "Steps", "Valid"]]
        category_name = None
        category = []

        total = 0
        good = 0

        for experiment, score in sorted(self.scores.items(), key=lambda x: str(x[0])):
            total += 1

            if experiment.entry.classname != category_name and category_name is not None:
                table.append((f"{category_name}", category))
                category_name = None
                category = []

            if category_name is None:
                category_name = experiment.entry.classname

            if not score.error:
                good += 1

            category.append(
                [
                    f"{experiment.short()}",
                    f"{score.steps}",
                    f"{(score.error or 'ok').splitlines()[0][:40]}",
                ]
            )

        if category_name is not None:
            table.append((f"{category_name}", category))

        table.append(["Total", f"{self.total_steps}", f"{good}/{total}"])

        dump_table(table, align="<><", file=file)


@dataclass(frozen=True)
class Summary:
    config: Config
    results: list[Result]

    __sexprtag__ = "interpret-summary"

    def __sexpr__(self) -> sexpr.SExpr:
        return sexpr.from_dataclass(self)

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> Self:
        return sexpr.to_dataclass(expr, target=cls)

    def report(cls, *, file: TextIO, eff: Effect) -> None:
        content = sexpr.pretty(cls.__sexpr__(), indent=2)
        try:
            file.write(content)
            eff.success(f"Succesfully wrote report to {file.name}")
        except OSError:
            eff.error("Failed to write report")

    def score_results(self, *, benchmark: Benchmark, eff: Effect):
        experiments = {}
        total_steps = 0
        for r in self.results:
            score = ExperimentScore(
                error=r.invalidate(benchmark=benchmark, config=self.config),
                steps=len(r.response.steps) if r.response else 0,
            )

            if score.error:
                eff.warning(f"At {r.experiment.short()} got error: {score.error}")

            experiments[r.experiment] = score
            total_steps += score.steps

        def invalidate() -> str | None:
            if self.config.analysis.group == "The Rice Theorem Cookers":
                return "You must pick a group name which is different from 'The Rice Theorem Cookers'"

            if self.config.max_steps != 100:
                return f"You must the intepreter exactly 100 steps, was {self.config.max_steps}"

            if self.config.abstract:
                all_experiments = set(benchmark.experiments)
            else:
                all_experiments = {
                    e for e in benchmark.experiments if e.input is not None
                }

            experiments = set()
            for result in self.results:
                experiments.add(result.experiment)
                if invalid := result.invalidate(benchmark=benchmark, config=self.config):
                    return invalid

            unrun = all_experiments - experiments

            if len(unrun) > 0:
                return f"Did not run all experiments, missing: {''.join(f'\n{e}' for e in unrun)}"

            return None

        invalid = invalidate()

        return ResultSummary(
            self.config,
            self.results,
            invalid=invalid,
            total_steps=total_steps,
            scores=experiments,
        )


@dataclass
class State(sexpr.AsSExpr):
    config: Config
    progress: int = 0
    results: list[Result] = field(default_factory=list)

    def rewind(self):
        self.progress -= 1
        self.results.pop(-1)

    def run_next(
        self, *, benchmark: Benchmark, score_limit: float | None = None, eff: Effect
    ) -> bool | None:
        no_experiments = len(self.config.experiments)

        if self.progress >= no_experiments:
            return None

        experiment = self.config.experiments[self.progress % no_experiments]

        with eff.context(
            f"Experiment {self.progress % no_experiments + 1}/{no_experiments} {experiment}"
        ):
            result = self.config.run_experiment(experiment, eff=eff)

            self.progress += 1
            self.results.append(result)

            msg = result.invalidate(benchmark=benchmark, config=self.config)
            if msg is not None:
                eff.warning(f"Invalid output: {msg}")
                return False

        return True

    def summary(self) -> Summary:
        return Summary(
            self.config,
            self.results,
        )
