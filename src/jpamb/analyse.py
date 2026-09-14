import math
import re
import shlex
import subprocess
import sys
from abc import ABC, abstractmethod
from collections import OrderedDict, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Self, TextIO

import jvm
import jvm.state
import sexpr
from jpamb.utils import Effect, dump_table


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


QUERIES = (
    "*",
    "assertion error",
    "divide by zero",
    "null pointer",
    "ok",
    "out of bounds",
)


@dataclass(frozen=True, slots=True)
class Duration:
    absolute: int
    relative: float

    def __sexpr__(self) -> sexpr.SExpr:
        return sexpr.from_dataclass(self)

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> Self:
        return sexpr.to_dataclass(expr, target=cls)


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

    def score(self, happens: bool) -> float:
        wager = (-1 if not happens else 1) * self.wager
        if wager > 0:
            if wager == float("inf"):
                return 1.0
            else:
                return 1.0 - 1 / (wager + 1)
        else:
            return wager

    def reward(self) -> float:
        wager = math.fabs(self.wager)
        if wager == float("inf"):
            return 1.0
        else:
            return 1.0 - 1 / (wager + 1)

    def __str__(self):
        return f"{self.wager:+0.2}"

    def __json__(self):
        return self.wager

    def __sexpr__(self) -> sexpr.SExpr:
        return str(self.wager)

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> Self:
        return cls(float(sexpr.to_str(expr)))


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
        return cls(sexpr.to_str(expr))


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
        return sexpr.to_dataclass(expr, target=cls)


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
        return sexpr.to_dataclass(expr, target=cls)


@dataclass(frozen=True, slots=True)
class Result:
    __sexprtag__ = "analysis-result"

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
        return sexpr.to_dataclass(expr, target=cls)


@dataclass(frozen=True, slots=True)
class Config:
    __sexprtag__ = "analysis-config"

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
        self.analysis.display(file=file)
        file.write(f"Experiments:   {len(self.experiments)}\n")
        file.write(f"Iterations:    {self.iterations}\n")
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
        experiments: Iterable[tuple[jvm.AbsMethodID, set[str]]],
        *,
        timeout: float,
        iterations: int,
        eff: Effect,
    ) -> "Self":
        with eff.context("Getting info about analysis"):
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
            experiments=OrderedDict(experiments),
            timeout=timeout,
            iterations=iterations,
        )

    def run_experiment(
        self, methodid, *, pedantic: bool = True, eff: Effect
    ) -> Result | None:
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

        return Result(
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
    config: Config
    results: list[tuple[str, list[ResultRow]]]
    categories: list[tuple[Category, Tracker]]
    total_score: float
    mean_rel_time: float
    total_abs_time: float

    def display_autolab(self, file=sys.stdout):
        import json

        invalid = self.invalidate()

        json.dump(
            {
                "_presentation": "semantic",
                "stages": ["Info", "Metrics", "Grade"],
                "Info": {
                    "Name": self.config.analysis.name,
                    "Group": self.config.analysis.group,
                },
                "Metrics": {
                    "Total Score": round(self.total_score, 2),
                    "Relative Mean Time (Db)": round(self.mean_rel_time, 2),
                    "Total Time (s)": round(self.total_abs_time / 10**9, 3),
                },
                "Grade": {
                    "Valid": {
                        "passed": invalid is None,
                        "hint": "" if invalid is None else invalid,
                    },
                    "Pass": {
                        "passed": invalid is None and self.total_score > 100,
                        "hint": (
                            "Report must be valid"
                            if invalid is not None
                            else "Total score needs to be above 100"
                        ),
                    },
                },
            },
            fp=file,
        )
        file.write("\n")

        student_eval = {
            "scores": {},
        }

        student_eval["scores"]["Total"] = self.total_score if invalid is None else 0
        student_eval["scores"]["Time"] = 100 / max(1, self.mean_rel_time)
        student_eval["scores"]["Categories"] = 100 / len(self.categories)

        json.dump(student_eval, fp=file)
        file.write("\n")

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
                f"{v.wager().reward():0.2f}",
                f"{(v.wager().score(False) * v.misses + v.wager().score(True) * v.hits) / self.config.iterations:.2f}",
            ]
            for c, v in self.categories.items()
        ]

        dump_table(categories, align="<>>>>>>", file=file)

    def invalidate(self) -> str | None:
        if self.config.analysis.group == "The Rice Theorem Cookers":
            return "You must pick a group name which is different from 'The Rice Theorem Cookers'"

        if (iters := self.config.iterations) != 3:
            return f"Analysis report should be based on 3 iterations, found {iters}"

        found_methods = []
        for _, rs in self.results:
            for r in rs:
                if not (r.score <= 6.0):
                    return f"Invalid score {r.score} found for {r.methodname}"
                if r.abs_time <= 0:
                    return f"Found negative time value {r.abs_time}"
                if r.methodname in found_methods:
                    return f"Found duplicate method {r.methodname}"
            found_methods.append(r.methodname)

        return None


@dataclass(frozen=True)
class Summary:
    config: Config
    results: dict[jvm.AbsMethodID, list[Result]]

    __sexprtag__ = "analysis-summary"

    def __sexpr__(self) -> sexpr.SExpr:
        return sexpr.from_dataclass(self)

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> Self:
        return sexpr.to_dataclass(expr, target=cls)

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


def mean(results):
    res = [r for r in results if not math.isnan(r)]
    return sum(res) / len(res)


@dataclass
class State:
    config: Config
    progress: int = 0
    results: dict[jvm.AbsMethodID, list[Result]] = field(default_factory=dict)
    categories: dict[Category, Tracker] = field(default_factory=dict)

    def __sexpr__(self) -> sexpr.SExpr:
        return sexpr.from_dataclass(self)

    @classmethod
    def from_sexpr(cls, expr: sexpr.SExpr) -> Self:
        return sexpr.to_dataclass(expr, target=cls)

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
            self.progress += 1

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

        return True

    def summary(self) -> Summary:
        return Summary(
            self.config,
            self.results,
        )
