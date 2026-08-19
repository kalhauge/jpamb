import click
from pathlib import Path
import shlex
import shutil
import os
import math
import sys
import json
from inspect import getsourcelines, getsourcefile
from collections import Counter

import runit

import jpamb
import jvm
import logging

import subprocess
import dataclasses
from contextlib import contextmanager
from typing import IO

log = logging.getLogger(__name__)


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


class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: "\033[36m",  # Cyan
        25: "\033[32m",  # Green
        logging.INFO: "",  # Green
        logging.WARNING: "\033[33m",  # Yellow
        logging.ERROR: "\033[31m",  # Red
        logging.CRITICAL: "\033[1;31m",  # Bold red
    }

    RESET = "\033[0m"

    def format(self, record):
        message = super().format(record)
        color = self.COLORS.get(record.levelno, self.RESET)
        return f"{color}{message}{self.RESET}"


def logger_initialize(verbose: int):
    LEVELS = [25, logging.INFO, logging.DEBUG, 0]

    lvl = LEVELS[verbose]

    handler = logging.StreamHandler()
    handler.setFormatter(
        ColorFormatter(
            "{relativeCreated:>8,.0f}ms [{levelname:^5}] {message}", style="{"
        )
    )

    logging.addLevelName(25, "SUCCS")

    log.setLevel(lvl)
    log.addHandler(handler)

    def success(self, msg, *args, **kwargs):
        return self.log(25, msg, *args, **kwargs)

    log.__class__.success = success


def summary64(cmd):
    import base64
    import hashlib

    return base64.b64encode(hashlib.sha256(str(cmd).encode()).digest()).decode()[:8]


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
        runner = runit.Runner(err_callback=self.output)
        with self.context(f"Run {shlex.join(args)}"):
            with self.context("Stderr"):
                out, time = runner.run(args, **kwargs)
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
    default=Path.cwd(),
    show_default=True,
    help="the base of the jpamb folder.",
)
@click.pass_context
def cli(ctx, workdir: Path, verbose):
    """This is the jpamb main entry point."""
    logger_initialize(verbose)
    log.debug(f"Setup suite in {workdir}")
    ctx.obj = jpamb.Suite(workdir)


@cli.command()
@click.pass_obj
def checkhealth(suite):
    """Check that the repository is setup correctly"""
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
    type=click.File(mode="w", encoding="utf-8"),
    help="A file to write the report to. (Good for golden testing)",
)
@click.argument("PROGRAM", nargs=-1)
@click.pass_obj
def test(suite, program, report, filter, fail_fast, with_python, timeout):
    """Test run a PROGRAM."""

    program = resolve_cmd(program, with_python)

    if suite.workfolder != Path.cwd():
        log.warning(f"Changing to {suite.workfolder}")
        os.chdir(suite.workfolder)

    r = Reporter(report)

    if not filter:
        with r.context("Info"):
            out = r.run(program + ("info",), timeout=timeout)
            info = jpamb.AnalysisInfo.parse(out)

            with r.context("Results"):
                for k, v in sorted(dataclasses.asdict(info).items()):
                    r.output(f"- {k}: {v}")

    total = 0
    for methodid, correct in suite.case_methods().items():
        if filter and not filter.search(str(methodid)):
            continue

        with r.context(f"Case {methodid}"):
            try:
                out = r.run(program + (str(methodid),), timeout=timeout)
            except subprocess.CalledProcessError as e:
                r.output(f"Got error {e}")
                continue
            response = jpamb.Response.parse(out)
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
    type=click.File(mode="w", encoding="utf-8"),
    help="A file to write the report to. (Good for golden testing)",
)
@click.argument("PROGRAM", nargs=-1)
@click.pass_obj
def interpret(suite, program, report, filter, with_python, timeout, stepwise):
    """Use PROGRAM as an interpreter."""

    r = Reporter(report)
    program = resolve_cmd(program, with_python)

    if suite.workfolder != Path.cwd():
        log.warning(f"Changing to {suite.workfolder}")
        os.chdir(suite.workfolder)

    last_case = None
    if stepwise:
        try:
            with open(".jpamb-stepwise", encoding="utf-8") as f:
                last_case = jpamb.Case.decode(f.read())
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
                with open(".jpamb-stepwise", "w", encoding="utf-8") as f:
                    f.write(case.encode())
                sys.exit(-1)
            count += 1

    Path(".jpamb-stepwise").unlink(True)

    r.output(f"Total {total}/{count}")


@cli.command()
@click.pass_obj
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
    type=click.File(mode="w", encoding="utf-8"),
    help="A file to write the report to",
)
@click.argument("PROGRAM", nargs=-1)
def evaluate(suite, program, report, timeout, iterations, with_python):
    """Evaluate the PROGRAM."""

    program = resolve_cmd(program, with_python)

    if suite.workfolder != Path.cwd():
        log.warning(f"Changing to {suite.workfolder}")
        os.chdir(suite.workfolder)

    runner = runit.Runner(err_callback=log.info, out_callback=log.debug)

    try:
        (out, _) = runner.run(
            program + ("info",),
            timeout=timeout,
        )
        info = jpamb.AnalysisInfo.parse(out)
    except ValueError:
        log.error("Expected info, but got:")
        for o in out.splitlines():
            log.error(o)

    total_score = 0
    total_time = 0
    total_relative = 0
    total_methods = 0
    bymethod = {}

    for methodid, correct in suite.case_methods():
        log.success(f"Running on {methodid}")
        results = []

        _score = 0
        _time = 0
        _relative = 0
        for i in range(iterations):
            log.info(f"Running on {methodid}, iter {i}")
            experiment = runner.experiment(program + (methodid.encode(),))
            response = jpamb.Response.parse(experiment.output)
            score = response.score(correct)

            result = {k: v.wager for k, v in response.predictions.items()}

            results.append(
                {
                    "iteration": i,
                    "response": result,
                    "score": score,
                    "time": experiment.time_ns,
                    "relative": experiment.time_relative,
                    "calibrates": experiment.calibrations_ns,
                }
            )

            _score += score
            _relative += experiment.time_relative
            _time += experiment.time_ns

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


@dataclasses.dataclass
class DockerRunner:
    """Encapsulates Docker/Podman execution with platform-specific handling."""

    docker_cmd: list[str]  # The base docker command (e.g., ["docker"] or ["wsl", ...])
    image: str  # Docker image to use
    workfolder: str  # Path to mount (already WSL-converted if needed)
    runner: runit.Runner = dataclasses.field(default_factory=runit.Runner)

    @classmethod
    def create(cls, workfolder: Path, image: str):
        """Factory method that handles platform detection and path conversion."""
        import os

        # Get docker command
        if os.environ.get("USE_WSL_DOCKER") == "1":
            log.info("Using Docker in WSL (Ubuntu)")
            docker_cmd = ["wsl", "-d", "Ubuntu", "--exec", "sudo", "docker"]
            # Convert path for WSL
            path_str = str(workfolder).replace("\\", "/")
            if len(path_str) >= 2 and path_str[1] == ":":
                drive = path_str[0].lower()
                rest = path_str[2:]
                workfolder_str = f"/mnt/{drive}{rest}"
            else:
                workfolder_str = str(workfolder)
        else:
            dockerbin = shutil.which("podman") or shutil.which("docker")
            if not dockerbin:
                raise click.UsageError("No docker or podman on PATH")
            log.info(f"Using docker: {dockerbin}")
            docker_cmd = [dockerbin]
            workfolder_str = str(workfolder)

        return cls(
            docker_cmd,
            image,
            workfolder_str,
            runner=runit.Runner(out_callback=log.info, err_callback=log.debug),
        )

    def run(self, command: list[str], **kwargs):
        """
        Run a command inside the Docker container.

        Args:
            command: The command to run (e.g., ["javac", "-d", "target/classes", ...])
            **kwargs: Additional arguments passed to the run() function
                     (timeout, logerr, logout, etc.)

        Returns:
            The result from run() function
        """
        full_cmd = (
            self.docker_cmd
            + [
                "run",
                "--rm",
                "-v",
                f"{self.workfolder}:/workspace",
                self.image,
            ]
            + command
        )
        return self.runner.run(full_cmd, **kwargs)


@cli.command()
@click.option(
    "-D",
    "--docker",
    help="the docker container to build with.",
    default="ghcr.io/kalhauge/jvm2json:jdk-latest",
)
@click.option(
    "--compile / --no-compile",
    help="compile the java source files.",
    default=None,
)
@click.option(
    "--decompile / --no-decompile",
    help="decompile the classfiles using jvm2json.",
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
def build(suite, compile, decompile, document, test, docker):
    """Rebuild all benchmarks."""

    if not any(s for s in [compile, decompile, document, test]):
        compile = compile is None
        decompile = decompile is None
        document = document is None
        test = test is None

    docker_runner = DockerRunner.create(suite.workfolder, docker)

    if compile:
        log.info("Compiling")
        docker_runner.run(
            ["javac", "-g", "-d", "target/classes"]
            + [a.relative_to(suite.workfolder).as_posix() for a in suite.sourcefiles()],
            timeout=600,
        )

        log.info("Building Stats")

        res, x = docker_runner.run(
            ["java", "-cp", "target/classes", "jpamb.Runtime"],
            timeout=60,
        )
        suite.case_file.parent.mkdir(exist_ok=True, parents=True)
        suite.case_file.write_text("\n".join(sorted(res.splitlines())))

        # TODO: Compute distribution.csv

    if decompile:
        log.info("Decompiling")
        for cl in suite.classes():
            log.info(f"Decompiling {cl}")
            res, t = docker_runner.run(
                [
                    "jvm2json",
                    "-s",
                    suite.classfile(cl).relative_to(suite.workfolder).as_posix(),
                ],
            )
            file = suite.decompiledfile(cl)
            file.parent.mkdir(exist_ok=True, parents=True)
            with open(file, "w", encoding="utf-8") as f:
                json.dump(json.loads(res), f, indent=2, sort_keys=True)
        log.success("Done decompiling")

    if document:
        log.info("Documenting")
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

        with open("OPCODES.md", "w", encoding="utf-8") as document:
            log.info(f"Writing OPCODES.md")
            document.write("#Bytecode instructions\n")
            document.write("| Mnemonic | Opcode Name |  Exists in |  Count |\n")
            document.write("| :---- | :---- | :----- | -----: |\n")

            for op, count in opcode_counts.most_common():
                log.debug(f"Handeling {op} {count}")
                (mnemonic, url, opcode) = opcode_urls[op]
                in_classes = ""

                for classname in class_opcodes:
                    if op in class_opcodes[classname]:
                        in_classes += " " + classname

                source = Path(getsourcefile(opcode.__class__))
                rel = Path("utils") / source.relative_to(source.parent.parent)
                giturl = (
                    f"{rel.as_posix()}?plain=1#L{getsourcelines(opcode.__class__)[1]}"
                )

                document.write(
                    f"| [{mnemonic}]({url}) | [{opcode.__class__.__name__}]({giturl})"
                    f" | {in_classes} | {count} |\n"
                )

    if test:
        log.info("Testing")

        for case in suite.cases:
            log.info(f"Testing {case}")

            folder = suite.classfiles_folder

            try:
                res, x = docker_runner.run(
                    [
                        "java",
                        "-cp",
                        folder.relative_to(suite.workfolder).as_posix(),
                        "-ea",
                        "jpamb.Runtime",
                        case.methodid.encode(),
                        case.input.encode(),
                    ],
                    timeout=5,
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


if __name__ == "__main__":
    cli()
