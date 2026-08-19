#!/usr/bin/env python3
"""A very stupid syntatic analysis, that only checks for assertion errors."""

import logging
import jpamb
import sys
from pathlib import Path

import re


def main():
    absmethodid = jpamb.getmethodid(
        "syntaxer",
        "1.0",
        "The Rice Theorem Cookers",
        ["syntatic", "python"],
        for_science=True,
    )

    log = logging
    log.basicConfig(level=logging.DEBUG)
    log.debug(Path.cwd())

    suite = jpamb.Suite.from_cwd()

    srcfile = suite.sourcefile(absmethodid.classname).relative_to(Path.cwd())

    with open(srcfile, "r") as f:
        log.debug("parse sourcefile %s", srcfile)
        content = f.read()

    res = re.search(rf".* {absmethodid.methodid.name}\(.*\)", content)

    if not res:
        log.error("Could not find method")
        sys.exit(1)

    log.debug(f"found {res}")
    rest = content[res.end(0) : -1]

    assert_or_end = re.search(r"assert|(^\s*})", rest, re.MULTILINE)

    if not assert_or_end:
        log.error("Could not end of method or assert")
        log.error(rest)
        sys.exit(1)

    log.debug(f"found {assert_or_end}")
    assert_found = assert_or_end.group(0) == "assert"

    if assert_found:
        log.debug("Found assertion")
        print("assertion error;80%")
    else:
        log.debug("No assertion")
        print("assertion error;20%")
