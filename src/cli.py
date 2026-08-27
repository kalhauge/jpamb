import click
from pathlib import Path
import shlex
import shutil
import os
import math
import sys
import json
from collections import Counter

from jpamb_utils import Effect, DockerRunner

import runit

import jpamb
import jvm
import sexpr

import subprocess
import dataclasses
from contextlib import contextmanager


class JpambScore:
    score: float
    time: float
    rel_time: float

    def __init__(self, score, time, rel_time):
        self.score = score
        self.time = time
        self.rel_time = rel_time


@dataclasses.dataclass
class Context:
    eff: Effect
    docker_image: str
    suite: jpamb.Suite


def re_parser(ctx_, parms_, expr):
    import re

    if expr:
        return re.compile(expr)


@click.group()
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="sets the verbosity of the program, more means more information",
)
@click.option(
    "-D",
    "--docker-image",
    help="the docker container to build with.",
    default="ghcr.io/kalhauge/jvm2json:jdk-latest",
)
@click.option(
    "--workdir",
    type=click.Path(
        exists=True,
        file_okay=False,
        path_type=Path,
        resolve_path=True,
    ),
    default=Path.cwd(),
    show_default=True,
    help="the base of the jpamb folder.",
)
@click.pass_context
def cli(ctx, workdir: Path, verbose, docker_image):
    """This is the jpamb main entry point."""
    eff = Effect(sys.stderr)
    eff.level = 25 - verbose * 10
    suite = jpamb.Suite.from_workdir(workdir, eff=eff)
    ctx.obj = Context(
        eff=eff,
        docker_image=docker_image,
        suite=suite,
    )
    ctx.obj.eff.info(f"Setup suite in {workdir}")


@cli.command()
@click.pass_obj
def checkhealth(ctx):
    """Check that the repository is setup correctly"""

    docker = DockerRunner.create(ctx.suite.workdir, ctx.docker_image, eff=ctx.eff)

    ctx.suite.checkhealth(docker=docker, eff=ctx.eff)


@cli.command()
@click.option(
    "--max-steps",
    show_default=True,
    default=100,
    help="how many steps to execute",
)
@click.option(
    "--fail-fast / --no-fail-fast",
    show_default=True,
    default=False,
    help="stop at first failure",
)
@click.option(
    "--timeout",
    show_default=True,
    default=2.0,
    help="timeout in seconds.",
)
@click.option(
    "--filter",
    "-f",
    help="A regular expression which filter the methods to run on.",
    callback=re_parser,
)
@click.argument("PROGRAM", nargs=-1)
@click.pass_obj
def interpret(ctx, program, filter, timeout, max_steps, fail_fast):
    """Use PROGRAM as an interpreter."""

    eff = ctx.eff

    if ctx.suite.workdir != Path.cwd():
        eff.warning(f"Changing to {ctx.suite.workdir}")
        os.chdir(ctx.suite.workdir)

    total = 0
    count = 0
    for case in ctx.suite.cases:
        if filter and not filter.search(str(case)):
            continue

        with eff.context(f"Case {case}"):
            try:
                out = eff.run(
                    program
                    + (case.methodid.encode(), case.input.encode(), str(max_steps)),
                    timeout=timeout,
                )
            except subprocess.TimeoutExpired:
                eff.error("timed out")
                behaviors = set("timed out")
                if fail_fast:
                    return
            except subprocess.CalledProcessError as e:
                eff.error(e)
                behaviors = set("failure")
                if fail_fast:
                    return

            else:
                steps = sexpr.from_string(out)

                no_steps = 0
                behaviors = set()
                for step in steps:
                    (k, args, kwargs) = sexpr.undata(step)
                    if k == "step":
                        no_steps += 1

                        after = kwargs["after"]
                        if isinstance(after, str):
                            behaviors.add(after)

                eff.info(
                    f"Ran {no_steps} steps and terminated with behaviors: {', '.join(behaviors)}"
                )

                if case.result not in behaviors:
                    if no_steps == max_steps:
                        eff.warning(
                            f"Terminated before finding behaviour: {case.result}"
                        )
                    else:
                        eff.error(f"Did not find behaviour: {case.result}")
                        if fail_fast:
                            return
                else:
                    eff.success(f"Did find behaviour: {case.result}")
                    count += 1

            total += 1
    eff.info(f"Total: {count}/{total}")


def run_analysis(
    analysis: tuple[str],
    methodid: jvm.AbsMethodID,
    iterations: int,
    timeout: float,
    eff: Effect,
):
    results = []

    _time = 0
    _relative = 0
    _iterations = 0
    for i in range(iterations):
        with eff.context(f"Iteration {i}"):
            try:
                experiment = eff.experiment(
                    analysis + (methodid.encode(),), timeout=timeout
                )
            except subprocess.CalledProcessError as e:
                eff.warning(
                    f"Ran {shlex.join(analysis)} info, and got error:\n{e.stderr}"
                )
                continue
            except subprocess.TimeoutExpired as e:
                eff.warning(
                    f"Ran {shlex.join(analysis)} info, and timed out after {e.timeout} seconds"
                )
                continue

        response, warns = jpamb.Response.parse(experiment.output)
        for warn in warns:
            eff.warning(warn)

        result = {k: v.__json__() for k, v in response.predictions.items()}

        results.append(
            {
                "iteration": i,
                "response": result,
                "time": experiment.time_ns,
                "relative": experiment.time_relative,
                "calibrates": experiment.calibrations_ns,
            }
        )

        _relative += experiment.time_relative
        _time += experiment.time_ns
        _iterations += 1

    return {
        # "score": _score / iterations,
        "time": _time / _iterations if _iterations else float("NaN"),
        "relative": _relative / _iterations if _iterations else float("NaN"),
        "iterations": results,
    }


@cli.command()
@click.pass_obj
@click.option(
    "--iterations",
    "-N",
    show_default=True,
    default=3,
    help="number of iterations.",
)
@click.option(
    "--timeout",
    show_default=True,
    default=5.0,
    help="timeout in seconds.",
)
@click.option(
    "--format",
    default="table",
    type=click.Choice(["table", "json"]),
    show_default=True,
    help="timeout in seconds.",
)
@click.argument("PROGRAM", nargs=-1)
def evaluate(ctx, program, timeout, format, iterations):
    """Evaluate the PROGRAM."""

    eff = ctx.eff

    if ctx.suite.workdir != Path.cwd():
        eff.warning(f"Changing to {ctx.suite.workdir}")
        os.chdir(ctx.suite.workdir)

    with eff.context("Getting info about analysis"):
        try:
            out = eff.run(
                program + ("info",),
                timeout=timeout,
            )
            info = jpamb.AnalysisInfo.parse(out)
        except subprocess.CalledProcessError as e:
            eff.error(f"Ran {shlex.join(program)} info, and got error:\n{e.stderr}")
            sys.exit(1)
        except ValueError:
            eff.error("Expected info, but got:")
            for o in out.splitlines():
                eff.error(o)

    bymethod = {}

    category_success = Counter()
    category_count = Counter()

    case_methods = ctx.suite.case_methods()

    for methodid, correct in sorted(case_methods.items()):
        with eff.context(f"Running on {methodid}"):
            output = run_analysis(
                program,
                methodid,
                timeout=timeout,
                iterations=iterations,
                eff=eff,
            )

            bymethod[methodid] = output

            for it in output["iterations"]:
                for key, value in it["response"].items():
                    if isinstance(value, str):
                        category_count.update([value])
                        if key in correct:
                            category_success.update([value])

    category = {k: category_success[k] / v for k, v in category_count.items()}

    with eff.context(f"Scoring"):
        for methodid, correct in sorted(case_methods.items()):
            output = bymethod[methodid]
            _score = 0

            if not output["iterations"]:
                eff.warning(f"{methodid}: no iterations")
            else:
                for it in output["iterations"]:
                    resp = jpamb.Response.from_json(it["response"])
                    it["score"] = resp.score(correct, category)
                    _score += it["score"]

                _score /= len(output["iterations"])

            eff.output(f"{methodid}: {_score}")

            output["score"] = _score

    total_methods = len(bymethod)
    total_time = sum(v["time"] for v in bymethod.values())
    total_relative = sum(v["relative"] for v in bymethod.values())
    total_score = sum(v["score"] for v in bymethod.values())

    result = {
        "info": dataclasses.asdict(info),
        "bymethod": bymethod,
        "category": category,
        "time": total_time / total_methods,
        "score": total_score,
        "relative": total_relative / total_methods,
    }

    match format:
        case "table":
            dump_table(result)
        case "json":
            dump_json(result)


def dump_json(result):
    json.dump(result, sys.stdout, indent=2)


def mean(results):
    res = [r for r in results if not math.isnan(r)]
    return sum(res) / len(res)


def dump_table(result):
    bymethod = result["bymethod"]

    classes = dict()
    for m in bymethod:
        classes.setdefault(m.classname, set()).add(m)

    rows = []
    for classname in sorted(classes):
        class_methods = classes[classname]
        rows.append(["", "", "", ""])
        rows.append([str(classname), "", "", ""])
        for methodid in sorted(class_methods):
            output = bymethod[methodid]
            rows.append(
                [
                    " " + str(methodid.extension),
                    f"{output['score']:.2f}",
                    f"{output['relative']:.3f}",
                    f"{output['time'] / 10**9:.3f}",
                ]
            )

    rows.append(["", "", "", ""])
    rows.append(
        [
            "Total",
            f"{sum(o['score'] for o in bymethod.values()):.2f}",
            f"{mean(o['relative'] for o in bymethod.values()):.3f}",
            f"{mean(o['time'] for o in bymethod.values()) / 10**9:.3f}",
        ]
    )
    print(rows[-1])

    sizes = [max(map(len, col)) for col in zip(*rows)]

    align = "<>>>"

    for row in rows:
        print("  ".join(f"{r:{a}{s}}" for r, a, s in zip(row, align, sizes)))

    print()
    if not result["category"]:
        print("No categories used")
    else:
        print("Categories:")
        maxcat = max(map(len, result["category"]))
        for category, value in result["category"].items():
            print(
                f" {category:<{maxcat}}  {value:7.2%}"
                f"  wager: {jpamb.Prediction.from_probability(value).wager:7.2}"
            )


@cli.command()
@click.option(
    "--compile / --no-compile",
    help="compile and decompile the java source files.",
    default=None,
)
@click.option(
    "--document / --no-document",
    help="docmument the files",
    default=None,
)
@click.option(
    "--test / --no-test",
    help="test that all cases are correct.",
    default=None,
)
@click.pass_obj
def build(ctx, compile, document, test):
    """Rebuild all benchmarks."""

    if not any(s for s in [compile, document, test]):
        compile = compile is None
        document = document is None
        test = test is None

    docker = DockerRunner.create(ctx.suite.workdir, ctx.docker_image, eff=ctx.eff)

    if compile:
        ctx.suite.build(docker=docker, eff=ctx.eff)

    if document:
        ctx.suite.document(eff=ctx.eff)

    if test:
        ctx.suite.test(docker=docker, eff=ctx.eff)


@cli.command()
@click.option(
    "--format",
    type=click.Choice(["pretty", "real", "repr", "json"], case_sensitive=True),
    default="pretty",
    help="The format to print the instruction in.",
)
@click.argument("METHOD")
@click.pass_obj
def inspect(ctx, method, format):
    method = jvm.AbsMethodID.decode(method)
    for i, res in enumerate(ctx.suite.findmethod(method)["code"]["bytecode"]):
        op = jvm.Opcode.from_json(res)
        match format:
            case "pretty":
                res = str(op)
            case "real":
                res = op.real()
            case "repr":
                res = repr(op)
            case "json":
                res = json.dumps(res)
        print(f"{i:03d} | {res}")


if __name__ == "__main__":
    cli()
