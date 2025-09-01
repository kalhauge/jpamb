import click
from pathlib import Path
import sys 
import math

from jpamb import model, logger
from jpamb.logger import log

import subprocess
import dataclasses
from contextlib import contextmanager


@click.group()
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="sets the verbosity of the program, more means more information",
)
@click.option(
    "--workdir",
    type=click.Path(
        exists=True,
        file_okay=False,
        path_type=Path,
        resolve_path=True,
    ),
    default=".",
    help="the base of the jpamb folder.",
)
@click.pass_context
def cli(ctx, workdir: Path, verbose):
    """This is the jpamb main entry point."""
    logger.initialize(verbose)
    log.debug(f"Setup suite in {workdir}")
    ctx.obj = model.Suite(workdir)


@cli.command()
@click.pass_context
def checkhealth(ctx):
    """Check that the repostiory is setup correctly"""
    ctx.obj.checkhealth()


def re_parser(ctx_, parms_, expr):
    import re

    if expr:
        return re.compile(expr)


@cli.command()
@click.pass_context
@click.option(
    "--fail-fast/--no-fail-fast",
    help="if we should stop after the first error.",
)
@click.option(
    "--filter",
    "-f",
    help="A regular expression which filter the methods to run on.",
    callback=re_parser,
)
@click.option(
    "--report",
    "-r",
    default="-",
    type=click.File(mode="w"),
    help="A file to write the report to. (Good for golden testing)",
)
@click.argument("PROGRAM", nargs=-1)
def test(ctx, program, report, filter, fail_fast):
    """Test run a PROGRAM."""

    prefix = ""

    @contextmanager
    def context(title):
        nonlocal prefix
        old = prefix
        print(f"{prefix}┌ {title}", file=report)
        prefix = f"{prefix}│ "
        yield
        prefix = old
        print(f"{prefix}└ {title}", file=report)

    def output(msgs):
        if not isinstance(msgs, str):
            msgs = str(msgs)

        for msg in msgs.splitlines():
            print(f"{prefix}{msg}", file=report)

    def run(arg):
        args = list(program + (arg,))
        if args and str(args[0]).lower().endswith(".py"):
            args = [sys.executable] + args
        output(f"Run {args}")
        report.flush()

        out = subprocess.run(
            args,
            # stderr=report,
            stdout=subprocess.PIPE,
            check=fail_fast,
            text=True,
        )
        output("Out")
        output(out.stdout)
        output(f"Done {out.returncode}")
        return out.stdout

    with context("Info"):
        info = model.AnalysisInfo.parse(run("info"))
        for k, v in sorted(dataclasses.asdict(info).items()):
            output(f"- {k}: {v}")

    total = 0
    for methodid, correct in ctx.obj.case_methods():
        if filter and not filter.search(str(methodid)):
            continue

        with context(f"Case {methodid}"):
            # out = run(methodid.encode())
            out = run(str(methodid))
            response = model.Response.parse(out)
            for k, v in sorted(response.predictions.items()):
                output(f"- {k}: {v} {v.wager:0.2f}")
            score = response.score(correct)
            output(f"Score {score:0.2f}")
            total += score

    output(f"Total {total:0.2f}")


def calibrate(log_calibration):
    from time import perf_counter_ns
    from jpamb import timer

    calibrators = [100_000, 100_000]
    calibration = 0
    for count in calibrators:
        start = perf_counter_ns()
        timer.sieve(count)
        end = perf_counter_ns()
        diff = end - start
        calibration += diff
        log_calibration(count=count, time=diff)

    calibration /= len(calibrators)
    return calibration


@cli.command()
@click.pass_context
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
    default=2.0,
    help="timeout in seconds.",
)
@click.option(
    "--report",
    "-r",
    default="-",
    type=click.File(mode="w"),
    help="A file to write the report to",
)
@click.argument("PROGRAM", nargs=-1)
def evaluate(ctx, program, report, timeout, iterations):
    """Evaluate the PROGRAM."""

    def calibrate(count=100_000):
        from time import perf_counter_ns
        from jpamb import timer

        start = perf_counter_ns()
        timer.sieve(count)
        end = perf_counter_ns()
        return end - start

    (out, _) = logger.run_cmd(
        program + ("info",),
        logger=log,
        timeout=timeout,
    )
    info = model.AnalysisInfo.parse(out)

    total_score = 0
    total_time = 0
    total_relative = 0
    total_methods = 0
    bymethod = {}

    for methodid, correct in ctx.obj.case_methods():
        log.success(f"Running on {methodid}")
        results = []

        _score = 0
        _time = 0
        _relative = 0
        for i in range(iterations):
            log.info(f"Running on {methodid}, iter {i}")
            r1 = calibrate()
            out, time = logger.run_cmd(
                program + (methodid.encode(),), logger=log, timeout=timeout
            )
            r2 = calibrate()
            response = model.Response.parse(out)
            score = response.score(correct)
            relative = math.log10(time / (r1 + r2) * 2)

            result = {k: v.wager for k, v in response.predictions.items()}

            results.append(
                {
                    "iteration": i,
                    "response": result,
                    "score": score,
                    "time": time,
                    "relative": relative,
                    "calibrates": [r1, r2],
                }
            )

            _score += score
            _relative += relative
            _time += time

        bymethod[str(methodid)] = {
            "score": _score / iterations,
            "time": _time / iterations,
            "relative": _relative / iterations,
            "iterations": results,
        }

        total_score += _score / iterations
        total_time += _time / iterations
        total_relative += _relative / iterations

        total_methods += 1
    import json

    json.dump(
        {
            "info": dataclasses.asdict(info),
            "bymethod": bymethod,
            "score": total_score,
            "time": total_time / total_methods,
            "relative": total_relative / total_methods,
        },
        report,
        indent=2,
    )
