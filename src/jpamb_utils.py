import logging
import shlex
import shutil
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO

import runit


@dataclass
class Effect:
    """A trivial effect system. Pass to methods which need to do things with
    the environment"""

    report: IO | None
    prefix: str = ""
    level: int = 30
    levels: dict[int, tuple[str, str]] = field(
        default_factory=lambda: {
            10: ("DEBUG", "\033[36m"),
            20: ("INFO", "\033[34m"),
            25: ("SUCCESS", "\033[32m"),
            30: ("WARNING", "\033[33m"),
            40: ("ERROR", "\033[31m"),
        }
    )

    @contextmanager
    def context(self, title):
        old = self.prefix
        if self.report:
            print(f"{self.prefix[:-1]}┌ {title}", file=self.report)
        self.prefix = f"{self.prefix[:-1]}│ "
        try:
            yield
        finally:
            self.prefix = old
            if self.report:
                print(f"{self.prefix[:-1]}└ {title}", file=self.report)

    def output(self, msgs):
        if self.report is None:
            return

        if not isinstance(msgs, str):
            msgs = str(msgs)

        for msg in msgs.splitlines():
            print(f"{self.prefix}{msg}", file=self.report)

    def log(self, level, msg):
        if level >= self.level:
            lvl = self.levels[level]
            self.output(f"{lvl[1]}{lvl[0]}\033[0m {msg}")

    def info(self, msg):
        self.log(logging.INFO, msg)

    def debug(self, msg):
        self.log(logging.DEBUG, msg)

    def error(self, msg):
        self.log(logging.ERROR, msg)

    def warning(self, msg):
        self.log(logging.WARNING, msg)

    def success(self, msg):
        self.log(25, msg)

    def run(self, *args, **kwargs):
        if self.level <= 10:
            runner = runit.Runner(err_callback=self.output)
            with self.context(f"Run {shlex.join(args[0])}"):
                with self.context("Stderr"):
                    out, _time = runner.run(*args, **kwargs)
                with self.context("Stdout"):
                    self.output(out)
        else:
            runner = runit.Runner()
            out, _time = runner.run(*args, **kwargs)
            self.success(f"Ran {shlex.join(args[0])}")

        return out

    def experiment(self, *args, **kwargs):
        with self.context(f"Run experiment {shlex.join(args[0])}"):
            if self.level <= 10:
                runner = runit.Runner(err_callback=self.output)
                with self.context("Stderr"):
                    experiment = runner.experiment(*args, **kwargs)
                with self.context("Stdout"):
                    self.output(experiment.output)
            else:
                runner = runit.Runner()
                experiment = runner.experiment(*args, **kwargs)
            self.info(f"Time       : {experiment.time_ns / 10**9:0.2f}s")
            self.info(f"Time (rel) : {experiment.time_relative:0.3f} Db")
            return experiment


@dataclass
class DockerRunner:
    """Encapsulates Docker/Podman execution with platform-specific handling."""

    docker_cmd: tuple[
        str, ...
    ]  # The base docker command (e.g., ["docker"] or ["wsl", ...])
    image: str  # Docker image to use
    workfolder: str  # Path to mount (already WSL-converted if needed)

    @classmethod
    def create(cls, workfolder: Path, image: str, eff: Effect):
        """Factory method that handles platform detection and path conversion."""
        import os

        # Get docker command
        if os.environ.get("USE_WSL_DOCKER") == "1":
            eff.info("Using Docker in WSL (Ubuntu)")
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
                raise RuntimeError("No docker or podman on PATH")
            eff.info(f"Using docker: {dockerbin}")
            docker_cmd = [dockerbin]
            workfolder_str = str(workfolder)

        return cls(tuple(docker_cmd), image, workfolder_str)

    def run(self, *args, eff: Effect, **kwargs):
        """
        Run a command inside the Docker container.

        Args:
            command: The command to run (e.g., ["javac", "-d", "target/classes", ...])
            **kwargs: Additional arguments passed to the run() function
                     (timeout, logerr, logout, etc.)

        Returns:
            The result from run() function
        """
        full_cmd = list(self.docker_cmd)
        full_cmd += [
            "run",
            "--rm",
            "-v",
            f"{self.workfolder}:/workspace",
            self.image,
        ]
        full_cmd += args[0]
        return eff.run(full_cmd, *args[1:], **kwargs)
