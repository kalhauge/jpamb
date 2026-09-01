from dataclasses import dataclass
from click.decorators import _AnyCallable
import dataclasses
import json
import math
import csv
import os
import shlex
import subprocess
import sys
from collections import Counter
from pathlib import Path

import click

import jpamb
import jvm
import sexpr
from jpamb_utils import DockerRunner, Effect


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
@click.option(
    "--docker / --no-docker",
    show_default=True,
    default=False,
    help="test docker container as well",
)
@click.pass_obj
def checkhealth(ctx, docker):
    """Check that the repository is setup correctly"""

    if docker:
        docker = DockerRunner.create(ctx.suite.workdir, ctx.docker_image, eff=ctx.eff)
    else:
        docker = None

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
                    if not isinstance(step, list):
                        raise TypeError(f"expected list, not {step}")
                    (k, _, kwargs) = sexpr.undata(step)
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
    "--score-limit",
    "-l",
    type=float,
    default=None,
    help="stop if score is below limit",
)
@click.option(
    "--filter",
    "-f",
    default=".*",
    help="A regular expression which filter the methods to run on.",
    callback=re_parser,
)
@click.option(
    "--step-wise / --no-step-wise",
    default=False,
    help="in case of crash, restart from where we left off",
)
@click.option(
    "--report",
    type=click.File("w"),
    help="write the report here (disables filter)",
)
@click.option(
    "--format",
    default="table",
    type=click.Choice(["table", "json"]),
    show_default=True,
    help="timeout in seconds.",
)
@click.argument("PROGRAM", nargs=-1)
def analyse(
    ctx,
    program,
    timeout,
    format,
    iterations,
    score_limit,
    filter,
    step_wise,
    report,
):
    """Evaluate the PROGRAM as an analysis."""

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

    # TODO Load State from file if step-wise.

    all_case_methods = list(sorted(ctx.suite.case_methods()))
    experiments = []

    eff.info(f"Found {len(all_case_methods)} case methods")

    for methodid in all_case_methods:
        if not filter.search(str(methodid)):
            eff.info(f"Skipping {methodid}, excluded by filter")
            continue

        experiments.append(methodid)

    experiments = experiments * iterations

    state = jpamb.AnalysisState(program, experiments, timeout=timeout)

    while state.experiments:
        cont = state.step(
            score_limit=score_limit,
            suite=ctx.suite,
            eff=eff,
        )
        if step_wise and not cont:
            eff.error("Stopping early")
            # TODO Save state to file if step-wise.
            return

    # TODO Report summary
    # summary = state.summary()
    # summary.report()


def make_cache(workdir: Path, *, eff: Effect) -> Path:
    cache = Path.cwd() / ".cache" / "jpamb"
    cache.mkdir(parents=True, exist_ok=True)

    cache_gitignore = cache / ".gitignore"
    if not cache_gitignore.exists():
        (cache / ".gitignore").write_text("**/*\n")

    return cache


def dump_json(result):
    json.dump(result, sys.stdout, indent=2)


def mean(results):
    res = [r for r in results if not math.isnan(r)]
    return sum(res) / len(res)


def dump_table(result):
    bymethod = result.scorebymethod

    classes = {}
    for m in bymethod:
        classes.setdefault(m.classname, set()).add(m)

    rows = []

    rows.append(
        [
            "Method",
            "Score",
            "Rel. (Db)",
            "Abs. (ms)",
        ]
    )

    for classname in sorted(classes):
        class_methods = classes[classname]
        rows.append(["", "", "", ""])
        rows.append([str(classname), "", "", ""])
        for methodid in sorted(class_methods):
            output = bymethod[methodid]
            rows.append(
                [
                    " " + str(methodid.extension),
                    f"{output.score:.2f}",
                    f"{output.relative:.3f}",
                    f"{output.time / 10**9:.3f}",
                ]
            )

    rows.append(
        [
            "Method",
            "Score",
            "Rel. (Db)",
            "Abs. (ms)",
        ]
    )
    rows.append(["", "", "", ""])
    rows.append(
        [
            "Total",
            f"{sum(o.score for o in bymethod.values()):.2f}",
            f"{mean(o.relative for o in bymethod.values()):.3f}",
            f"{mean(o.time for o in bymethod.values()) / 10**9:.3f}",
        ]
    )
    print(rows[-1])

    sizes = [max(map(len, col)) for col in zip(*rows)]

    align = "<>>>"

    for row in rows:
        print("  ".join(f"{r:{a}{s}}" for r, a, s in zip(row, align, sizes)))

    print()
    if not result.category:
        print("No categories used")
    else:
        print("Categories:")
        maxcat = max(map(len, result.category))
        for category, value in result.category.items():
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
