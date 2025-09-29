import click
from pathlib import Path
import shlex
import enum
import math
import sys
import json
from inspect import getsourcelines, getsourcefile
from collections import Counter
import matplotlib.pyplot as plt
import matplotlib.colors as colors

from jpamb import model, logger, jvm
from jpamb.logger import log

import subprocess
import dataclasses
from contextlib import contextmanager
from typing import IO


class JpambScore:
    score: float
    time: float
    rel_time: float

    def __init__(self, score, time, rel_time):
        self.score = score
        self.time = time
        self.rel_time = rel_time


def re_parser(ctx_, parms_, expr):
    import re

    if expr:
        return re.compile(expr)


def run(cmd: list[str], /, timeout=2.0, logout=None, logerr=None, **kwargs):
    import threading
    from time import monotonic, perf_counter_ns

    if not logerr:

        def logerr(a):
            pass

    if not logout:

        def logout(a):
            pass

    cp = None
    stdout = []
    stderr = []
    tout = None
    try:
        start = monotonic()
        start_ns = perf_counter_ns()

        if timeout:
            end = start + timeout
        else:
            end = None

        cp = subprocess.Popen(
            cmd,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            **kwargs,
        )
        assert cp and cp.stdout and cp.stderr

        def log_lines(cp):
            assert cp.stderr
            with cp.stderr:
                for line in iter(cp.stderr.readline, ""):
                    stderr.append(line)
                    logerr(line[:-1])

        def save_result(cp):
            assert cp.stdout
            with cp.stdout:
                for line in iter(cp.stdout.readline, ""):
                    stdout.append(line)
                    logout(line[:-1])

        terr = threading.Thread(
            target=log_lines,
            args=(cp,),
            daemon=True,
        )
        terr.start()
        tout = threading.Thread(
            target=save_result,
            args=(cp,),
            daemon=True,
        )
        tout.start()

        terr.join(end and end - monotonic())
        tout.join(end and end - monotonic())
        exitcode = cp.wait(end and end - monotonic())
        end_ns = perf_counter_ns()

        if exitcode != 0:
            raise subprocess.CalledProcessError(
                cmd=cmd,
                returncode=exitcode,
                stderr="".join(stderr),
                output="".join(stdout),
            )

        return ("".join(stdout), end_ns - start_ns)
    except subprocess.CalledProcessError as e:
        if tout:
            tout.join()
        e.stderr = "".join(stderr)
        e.stdout = "".join(stdout)
        raise e
    except subprocess.TimeoutExpired:
        if cp:
            cp.terminate()
            if cp.stdout:
                cp.stdout.close()
            if cp.stderr:
                cp.stderr.close()
        raise


@dataclasses.dataclass
class Reporter:
    report: IO
    prefix: str = ""

    @contextmanager
    def context(self, title):
        old = self.prefix
        print(f"{self.prefix[:-1]}┌ {title}", file=self.report)
        self.prefix = f"{self.prefix[:-1]}│ "
        try:
            yield
        finally:
            self.prefix = old
            print(f"{self.prefix[:-1]}└ {title}", file=self.report)

    def output(self, msgs):
        if not isinstance(msgs, str):
            msgs = str(msgs)

        for msg in msgs.splitlines():
            print(f"{self.prefix}{msg}", file=self.report)

    def run(self, args, **kwargs):
        with self.context(f"Run {shlex.join(args)}"):
            with self.context("Stderr"):
                out, time = run(args, logerr=self.output, **kwargs)
            with self.context("Stdout"):
                self.output(out)
            return out


def resolve_cmd(program, with_python=None):
    if with_python is None:
        if str(program[0]).lower().endswith(".py"):
            log.warning(
                "Automatically prepending the current python interpreter to the command. To disable this warning add the '--with-python' flag or prepend intented python interpreter to the command."
            )
            with_python = True
        else:
            with_python = False

    if with_python:
        try:
            executable = str(Path(sys.executable).relative_to(Path.cwd()))
        except ValueError:
            log.warning(
                "Python executable outside of current directory, might be a misconfiguration. "
                "Run the tool with `uv run jpamb ...`."
            )
            executable = sys.executable

        program = (executable,) + program

    return program


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
@click.pass_obj
def checkhealth(suite):
    """Check that the repostiory is setup correctly"""
    suite.checkhealth()


@cli.command()
@click.option(
    "--with-python/--no-with-python",
    "-W/-noW",
    help="the analysis is a python script, which should run in the same interpreter as jpamb.",
    default=None,
)
@click.option(
    "--fail-fast/--no-fail-fast",
    help="if we should stop after the first error.",
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
@click.option(
    "--report",
    "-r",
    default="-",
    type=click.File(mode="w"),
    help="A file to write the report to. (Good for golden testing)",
)
@click.argument("PROGRAM", nargs=-1)
@click.pass_obj
def test(suite, program, report, filter, fail_fast, with_python, timeout):
    """Test run a PROGRAM."""

    program = resolve_cmd(program, with_python)

    r = Reporter(report)

    if not filter:
        with r.context("Info"):
            out = r.run(program + ("info",), timeout=timeout)
            info = model.AnalysisInfo.parse(out)

            with r.context("Results"):
                for k, v in sorted(dataclasses.asdict(info).items()):
                    r.output(f"- {k}: {v}")

    total = 0
    for methodid, correct in suite.case_methods():
        if filter and not filter.search(str(methodid)):
            continue

        with r.context(f"Case {methodid}"):
            out = r.run(program + (str(methodid),), timeout=timeout)
            response = model.Response.parse(out)
            with r.context("Results"):
                for k, v in sorted(response.predictions.items()):
                    r.output(f"- {k}: {v} {v.wager:0.2f}")
            score = response.score(correct)
            r.output(f"Score {score:0.2f}")
            total += score

    r.output(f"Total {total:0.2f}")


@cli.command()
@click.option(
    "--with-python/--no-with-python",
    "-W/-noW",
    help="the analysis is a python script, which should run in the same interpreter as jpamb.",
    default=None,
)
@click.option(
    "--stepwise / --no-stepwise",
    help="continue from last failure",
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
@click.option(
    "--report",
    "-r",
    default="-",
    type=click.File(mode="w"),
    help="A file to write the report to. (Good for golden testing)",
)
@click.argument("PROGRAM", nargs=-1)
@click.pass_obj
def interpret(suite, program, report, filter, with_python, timeout, stepwise):
    """Use PROGRAM as an interpreter."""

    r = Reporter(report)
    program = resolve_cmd(program, with_python)

    last_case = None
    if stepwise:
        try:
            with open(".jpamb-stepwise") as f:
                last_case = model.Case.decode(f.read())
        except ValueError as e:
            log.warning(e)
            last_case = None
        except IOError:
            last_case = None

    total = 0
    count = 0
    for case in suite.cases:
        if last_case and last_case != case:
            continue
        last_case = None

        if filter and not filter.search(str(case)):
            continue

        with r.context(f"Case {case}"):
            try:
                out = r.run(
                    program + (case.methodid.encode(), case.input.encode()),
                    timeout=timeout,
                )
                ret = out.splitlines()[-1].strip()
            except subprocess.TimeoutExpired:
                ret = "*"
            except subprocess.CalledProcessError as e:
                log.error(e)
                ret = "failure"
            r.output(f"Expected {case.result!r} and got {ret!r}")
            if case.result == ret:
                total += 1
            elif stepwise:
                with open(".jpamb-stepwise", "w") as f:
                    f.write(case.encode())
                sys.exit(-1)
            count += 1

    Path(".jpamb-stepwise").unlink(True)

    r.output(f"Total {total}/{count}")


@cli.command()
@click.pass_context
@click.option(
    "--with-python/--no-with-python",
    "-W/-noW",
    help="the analysis is a python script, which should run in the same interpreter as jpamb.",
    default=None,
)
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
def evaluate(ctx, program, report, timeout, iterations, with_python):
    """Evaluate the PROGRAM."""

    program = resolve_cmd(program, with_python)

    def calibrate(count=100_000):
        from time import perf_counter_ns
        from jpamb import timer

        start = perf_counter_ns()
        timer.sieve(count)
        end = perf_counter_ns()
        return end - start

    try:
        (out, _) = run(
            program + ("info",),
            logout=log.info,
            logerr=log.debug,
            timeout=timeout,
        )
        info = model.AnalysisInfo.parse(out)
    except ValueError:
        log.error("Expected info, but got:")
        for o in out.splitlines():
            log.error(o)

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
            out, time = run(
                program + (methodid.encode(),), logerr=log.debug, timeout=timeout
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


@cli.command()
@click.option(
    "--compile / --no-compile",
    help="compile the java source files.",
)
@click.option(
    "--decompile / --no-decompile",
    help="decompile the classfiles using jvm2json.",
)
@click.option(
    "--document / --no-document",
    help="decompile the classfiles using jvm2json.",
)
@click.option(
    "--test / --no-test",
    help="test that all cases are correct.",
)
@click.pass_obj
def build(suite, compile, decompile, document, test):
    """Rebuild all benchmarks."""

    if compile:
        run(
            ["mvn", "compile"],
            logerr=log.warning,
            logout=log.info,
            timeout=600,
        )

    if decompile:
        log.info("Decompiling")
        for cl in suite.classes():
            log.info(f"Decompiling {cl}")
            res, t = run(
                [
                    "jvm2json",
                    "-s",
                    suite.classfile(cl),
                ],
                logerr=log.warning,
            )
            with open(suite.decompiledfile(cl), "w") as f:
                json.dump(json.loads(res), f, indent=2, sort_keys=True)
        log.success("Done decompiling")

    if document:
        opcode_counts = Counter()
        opcode_urls = {}
        class_opcodes = {}
        for case in suite.cases:
            class_opcodes[str(case.methodid.classname).split(".")[-1]] = set()
            list_ops = []
            for opcode in suite.method_opcodes(case.methodid):
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

        with open("OPCODES.md", "w") as document:
            document.write("#Bytecode instructions\n")
            document.write("| Mnemonic | Opcode Name |  Exists in |  Count |\n")
            document.write("| :---- | :---- | :----- | -----: |\n")

            for op, count in opcode_counts.most_common():
                (mnemonic, url, opcode) = opcode_urls[op]
                in_classes = ""

                for classname in class_opcodes:
                    if op in class_opcodes[classname]:
                        in_classes += " " + classname

                rel = Path(getsourcefile(opcode.__class__)).relative_to(Path.cwd())
                giturl = f"{rel}?plain=1#L{getsourcelines(opcode.__class__)[1]}"

                document.write(
                    " | ["
                    + mnemonic
                    + "]("
                    + url
                    + ") | "
                    + f"[{opcode.__class__.__name__}]({giturl})"
                    + " | "
                    + in_classes
                    + " | "
                    + str(count)
                    + " |\n"
                )

    if test:
        log.info("Testing")

        for case in suite.cases:
            log.info(f"Testing {case}")

            folder = suite.classfiles_folder

            try:
                res, x = run(
                    [
                        "java",
                        "-cp",
                        folder,
                        "-ea",
                        "jpamb.Runtime",
                        case.methodid.encode(),
                        case.input.encode(),
                    ],
                    logout=log.info,
                    logerr=log.debug,
                    timeout=2,
                )
            except subprocess.TimeoutExpired:
                res = "*"

            if case.result == res.strip():
                log.success(f"Correct {case}")
            else:
                log.error(f"Incorrect (got {res.strip()}) expected {case}")

        log.success("Done testing")


@cli.command()
@click.option(
    "--format",
    type=click.Choice(["pretty", "real", "repr", "json"], case_sensitive=True),
    default="pretty",
    help="The format to print the instruction in.",
)
@click.argument("METHOD")
@click.pass_obj
def inspect(suite, method, format):
    method = jvm.AbsMethodID.decode(method)
    for i, res in enumerate(suite.findmethod(method)["code"]["bytecode"]):
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


@cli.command()
@click.pass_context
@click.option(
    "--directory",
    "-d",
    help="Specifying a directory will create a comparative plot of all reports in the directory",
    type=click.Path(exists=True, file_okay=False, readable=True, path_type=Path),
)
@click.option(
    "--report",
    "-r",
    help="Specifying the path to a report.json file will plot the scores of the report",
    type=click.Path(
        exists=True,
        file_okay=True,
        readable=True,
        path_type=Path,
    ),
)
def plot(ctx, report, directory):
    """Plot results of a report or compare reports in a directory"""
    import numpy as np

    prefix = ""

    @contextmanager
    def context(title):
        nonlocal prefix
        old = prefix
        print(f"{prefix[:-1]}┌ {title}", file=report)
        prefix = f"{prefix[:-1]}│ "
        yield
        prefix = old
        print(f"{prefix[:-1]}└ {title}", file=report)

    def parse_report(report):
        import json

        with open(report, "r") as data:
            try:
                report = json.loads(data.read())

                info = report["info"]
                methods = report["bymethod"]
                total_value = JpambScore(
                    max(report["score"], -100), report["time"], report["relative"]
                )
                method_values = {}

                for methodid, correct in ctx.obj.case_methods():
                    method = methods[str(methodid)]
                    method_values[str(methodid)] = JpambScore(
                        max(method["score"], -100), method["time"], method["relative"]
                    )

                return info, method_values, total_value

            except ValueError:
                raise ValueError(f"Cannot read {report}")

    def compare_reports(directory):
        import os

        scores = []
        times = []
        labels = []

        for report in os.listdir(directory):
            if report.endswith(".json"):
                try:
                    rep_info, _, rep_scores = parse_report(directory.joinpath(report))
                    scores.append(rep_scores.score)
                    times.append(rep_scores.rel_time)
                    labels.append(rep_info["name"] + ": " + ", ".join(rep_info["tags"]))
                except ValueError:
                    print(f"Failed to process {report}")

        return scores, times, labels

    def get_plotcolor(problemclass):
        if "Simple" in problemclass:
            return "seagreen"
        if "Calls" in problemclass:
            return "turquoise"
        if "Loops" in problemclass:
            return "mediumslateblue"
        if "Arrays" in problemclass:
            return "violet"
        if "Tricky" in problemclass:
            return "darkviolet"

        return "red"

    def plot_scores(scores, times, labels, classes):
        import numpy as np
        import matplotlib.patches as mpatches

        class MidpointNormalize(colors.Normalize):
            # Normalise the colorbar so that diverging bars work there way either side from a prescribed midpoint value)
            def __init__(self, vmin=None, vmax=None, midpoint=None, clip=True):
                self.midpoint = midpoint
                colors.Normalize.__init__(self, vmin, vmax, clip)

            def __call__(self, value, clip=None):
                x, y = [self.vmin, self.midpoint, self.vmax], [0, 0.5, 1]
                return np.ma.masked_array(np.interp(value, x, y), np.isnan(value))

        simplec = mpatches.Patch(color=get_plotcolor("Simple"), label="Simple")
        arraysc = mpatches.Patch(color=get_plotcolor("Arrays"), label="Arrays")
        callsc = mpatches.Patch(color=get_plotcolor("Calls"), label="Calls")
        loopsc = mpatches.Patch(color=get_plotcolor("Loops"), label="Loops")
        trickyc = mpatches.Patch(color=get_plotcolor("Tricky"), label="Tricky")

        plt.title("JPAMB Test Scores", pad=15.0)
        plt.legend(handles=[simplec, arraysc, callsc, loopsc, trickyc])

        plt.xticks([])
        plt.yticks([])

        plot_times = np.array(times)
        plot_scores = np.array(scores)

        barcolors = [
            get_plotcolor(pc) if score > -100 else "red"
            for (pc, score) in zip(classes, plot_scores)
        ]

        plt.subplot(2, 1, 1)
        plt.bar(labels, plot_scores, color=barcolors, label=classes)
        plt.ylabel("Test Score")
        plt.xticks([])

        max_y = abs(plot_scores).max() * 1.05
        plt.ylim(-max_y, max_y)

        plt.subplot(2, 1, 2)
        plt.bar(labels, plot_times, color=barcolors, label=classes)
        plt.ylabel("Test Time")

        plt.xticks(rotation=80)
        max_y = abs(plot_times).max() * 1.05
        plt.ylim(0, max_y)

        plt.show()

    def plot_directory(scores, times, labels):
        class MidpointNormalize(colors.Normalize):
            # Normalise the colorbar so that diverging bars work there way either side from a prescribed midpoint value)
            def __init__(self, vmin=None, vmax=None, midpoint=None, clip=True):
                self.midpoint = midpoint
                colors.Normalize.__init__(self, vmin, vmax, clip)

            def __call__(self, value, clip=None):
                x, y = [self.vmin, self.midpoint, self.vmax], [0, 0.5, 1]
                return np.ma.masked_array(np.interp(value, x, y), np.isnan(value))

        plot_times = np.array(times)
        plot_norm_times = (plot_times - plot_times.min()) / (
            plot_times.max() - plot_times.min()
        )
        plot_scores = np.array(scores)

        performance_score = 100 * plot_scores * (1 - (plot_norm_times * 0.5))
        performance_score = [max(100, score) for score in performance_score]

        plt.scatter(
            x=plot_scores,
            y=plot_times,
            s=performance_score,
            c=plot_scores,
            cmap="tab20b",
            clim=(plot_times.min(), plot_scores.max()),
            norm=MidpointNormalize(
                midpoint=0, vmin=plot_scores.min(), vmax=plot_scores.max()
            ),
        )

        for i, name in enumerate(labels):
            plt.annotate(name, (plot_scores[i], plot_times[i]))

        plt.title("JPAMB Test Scores", pad=15.0)
        plt.xlabel("Test Score")
        plt.ylabel("Analyzer Relative Execution Time")
        plt.show()

    if directory:
        scores, times, labels = compare_reports(directory)
        plot_directory(scores, times, labels)

    if report:
        info, method_values, total_values = parse_report(report)

        scores = []
        times = []
        labels = []
        classes = []

        for methodid, correct in ctx.obj.case_methods():
            method = method_values[str(methodid)]
            scores.append(method.score)
            times.append(method.time)
            labels.append(methodid.extension.encode())
            classes.append(str(methodid.classname))

        plot_scores(scores, times, labels, classes)


if __name__ == "__main__":
    cli()
