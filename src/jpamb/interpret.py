import shlex
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Self, TextIO

import jvm
import jvm.state
import sexpr
from jpamb.analyse import AnalysisInfo, Category, Duration, Tracker
from jpamb.case import Case
from jpamb.utils import Effect, dump_table


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
    before: sexpr.SExpr
    pc: jvm.state.PC
    after: sexpr.SExpr

    def __sexpr__(self) -> sexpr.SExpr:
        return sexpr.from_dataclass(self)

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> Self:
        return sexpr.to_dataclass(expr, target=cls)


@dataclass(frozen=True)
class Response:
    init: Init
    steps: list[Step]

    def __post_init__(self):
        assert isinstance(self.init, Init)

    @staticmethod
    def parse(out) -> Self | None:
        warnings = []
        steps = []
        exprs = sexpr.from_string(out)

        if not exprs:
            warnings.append("Expected an initial state, but got nothing")
            return None

        try:
            init = Init.from_sexpr(exprs[0])
        except sexpr.FromSExprError as e:
            warnings.append(
                f"Could not interpret expr {sexpr.pretty(exprs[0])!r} as initial state: {e}"
            )
            return None

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

    def invalidate(self, *, result: str, max_steps: int) -> str | None:
        current = self.init.state
        results = set()
        for i, step in enumerate(self.steps):
            if i >= max_steps:
                return f"Exceeded {max_steps}"

            if step.before != current:
                return f"At step {i}: previous state does not match current:\n{sexpr.pretty(current, indent=2)}"

            # TODO check conformance

            if isinstance(step.after, str):
                results.add(step.after)

            current = step.after

        if i + 1 != max_steps and not result in results:
            return f"The result {result!r} was not found in the final states reported {results!r}"


@dataclass(frozen=True, slots=True)
class Result:
    __sexprtag__ = "interpret-result"

    case: Case
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

    def invalidate(self, *, config) -> str | None:
        if self.response is None:
            return "No reponse created"

        return self.response.invalidate(
            result=self.case.result,
            max_steps=config.max_steps,
        )


@dataclass(frozen=True, slots=True)
class Config:
    __sexprtag__ = "interpret-config"

    cmd: tuple[str, ...]
    analysis: AnalysisInfo
    experiments: list[Case]
    timeout: float
    max_steps: int

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

    def __sexpr__(self) -> sexpr.SExpr:
        return sexpr.from_dataclass(self)

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> Self:
        return sexpr.to_dataclass(expr, target=cls)

    @classmethod
    def from_cmd(
        cls,
        cmd: tuple[str],
        experiments: Iterable[Case],
        *,
        max_steps: int,
        timeout: float,
        eff: Effect,
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
        )

    def run_experiment(
        self,
        case: Case,
        *,
        pedantic: bool = True,
        eff: Effect,
    ) -> Result:
        cmd = self.cmd + (
            case.methodid.encode(),
            case.input.encode(),
            str(self.max_steps),
        )
        duration = Duration(0, 0)
        calibrations_ns = ()
        try:
            experiment = eff.experiment(
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
            duration = Duration(experiment.time_ns, experiment.time_relative)
            calibrations_ns = tuple(experiment.calibrations_ns)
            response, warns = Response.parse(experiment.output)

            if warns:
                for warn in warns:
                    eff.warning(warn)
                if pedantic:
                    response = None

        return Result(
            case,
            response,
            duration,
            calibrations_ns,
        )


@dataclass(frozen=True)
class CaseScore:
    error: str | None
    steps: int


@dataclass(frozen=True)
class ResultSummary:
    config: Config
    results: list[Result]
    scores: dict[Case, CaseScore]
    total_steps: int

    def display_autolab(self, file=sys.stdout):
        import json

        invalid = self.invalidate()

        student_eval = {}

        student_eval["scores"] = {}
        student_eval["scores"]["Total"] = len(self.results) if invalid is None else 0

        json.dump(student_eval, fp=file)
        file.write("\n")

    def display(self, file=sys.stdout):
        self.config.display(file=file)

        file.write("\n")
        table = [["Case", "Steps", "Valid"]]
        category_name = None
        category = []

        total = 0
        good = 0

        for case, score in sorted(self.scores.items()):
            total += 1

            if case.methodid.classname != category_name:
                table.append((f"{category_name}", category))
                category_name = None
                category = []

            if category_name is None:
                category_name = case.methodid.classname

            if not score.error:
                good += 1

            category.append(
                [
                    f"{case.methodid.extension.name}:{case.input.encode()}",
                    f"{score.steps}",
                    f"{score.error or 'ok'}",
                ]
            )

        if category_name is not None:
            table.append((f"{category_name}", category))
            category_name = case.methodid

        table.append(["Total", f"{self.total_steps}", f"{good}/{total}"])

        dump_table(table, align="<><", file=file)

    def invalidate(self) -> str | None:
        if self.config.analysis.group == "The Rice Theorem Cookers":
            return "You must pick a group name which is different from 'The Rice Theorem Cookers'"

        if self.config.max_steps != 100:
            return f"You must the intepreter exactly 100 steps, was {self.config.max_steps}"

        for result in self.results:
            return result.invalidate(config=self.config)

        return None


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

    def score_results(self):
        cases = {}
        total_steps = 0
        for r in self.results:
            score = CaseScore(
                error=r.invalidate(config=self.config),
                steps=len(r.response.steps) if r.response else 0,
            )
            cases[r.case] = score
            total_steps += score.steps

        return ResultSummary(
            self.config,
            self.results,
            total_steps=total_steps,
            scores=cases,
        )


@dataclass
class State:
    config: Config
    progress: int = 0
    results: list[Result] = field(default_factory=list)
    categories: dict[Category, Tracker] = field(default_factory=dict)

    def __sexpr__(self) -> sexpr.SExpr:
        return sexpr.from_dataclass(self)

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> Self:
        return sexpr.to_dataclass(expr, target=cls)

    def rewind(self):
        self.progress -= 1
        self.results.pop(-1)

    def run_next(self, *, score_limit: float | None = None, eff: Effect) -> bool | None:
        no_experiments = len(self.config.experiments)

        if self.progress >= no_experiments:
            return None

        case = self.config.experiments[self.progress % no_experiments]

        with eff.context(
            f"Experiment {self.progress % no_experiments + 1}/{no_experiments} {case}"
        ):
            result = self.config.run_experiment(case, eff=eff)

            self.progress += 1
            self.results.append(result)

            if msg := result.invalidate(config=self.config):
                eff.warning(f"Invalid output: {msg}")

                return False

        return True

    def summary(self) -> Summary:
        return Summary(
            self.config,
            self.results,
        )
