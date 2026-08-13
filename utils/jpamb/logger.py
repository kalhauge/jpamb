"""jpamb.logger

This module contains modules to handle consitent logging across
the different tools.
"""

import sys
from loguru import logger
import subprocess


log = logger


def initialize(verbose: int):
    LEVELS = ["SUCCESS", "INFO", "DEBUG", "TRACE"]

    lvl = LEVELS[verbose]

    if verbose >= 2:
        log.remove()
        log.add(
            sys.stderr,
            format="<green>{elapsed}</green> | <level>{level: <8}</level> | <red>{extra[process]:<8}</red> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=lvl,
        )
    else:
        log.remove()
        log.add(
            sys.stderr,
            format="<red>{extra[process]:<8}</red>: <level>{message}</level>",
            level=lvl,
        )

    log.configure(extra={"process": "main"})


def summary64(cmd):
    import base64
    import hashlib

    return base64.b64encode(hashlib.sha256(str(cmd).encode()).digest()).decode()[:8]


def run_cmd(cmd: list[str], /, timeout, logger, **kwargs):
    import shlex
    import threading
    from time import monotonic, perf_counter_ns

    logger = logger.bind(process=summary64(cmd))
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

        logger.debug(f"starting: {shlex.join(map(str, cmd))}")

        cp = subprocess.Popen(
            cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, **kwargs
        )
        assert cp and cp.stdout and cp.stderr

        def log_lines(cp):
            assert cp.stderr
            with cp.stderr:
                for line in iter(cp.stderr.readline, ""):
                    stderr.append(line)
                    logger.debug(line[:-1])

        def save_result(cp):
            assert cp.stdout
            with cp.stdout:
                stdout.append(cp.stdout.read())

        terr = threading.Thread(target=log_lines, args=(cp,), daemon=True)
        terr.start()
        tout = threading.Thread(target=save_result, args=(cp,), daemon=True)
        tout.start()

        terr.join(end and end - monotonic())
        tout.join(end and end - monotonic())
        exitcode = cp.wait(end and end - monotonic())
        end_ns = perf_counter_ns()

        if exitcode != 0:
            raise subprocess.CalledProcessError(
                cmd=cmd,
                returncode=exitcode,
                stderr="\n".join(stderr),
                output=stdout[0].strip(),
            )

        logger.debug("done")
        return (stdout[0].strip(), end_ns - start_ns)
    except subprocess.CalledProcessError as e:
        if tout:
            tout.join()
        e.stdout = stdout[0].strip()
        raise e
    except subprocess.TimeoutExpired:
        logger.debug("process timed out, terminating")
        if cp:
            cp.terminate()
            if cp.stdout:
                cp.stdout.close()
            if cp.stderr:
                cp.stderr.close()
        raise
