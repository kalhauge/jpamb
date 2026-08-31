#!/usr/bin/env python3
"""A very stupid syntactic bytecode analysis, that only checks for assertion errors."""

import logging

import jpamb


def main():
    methodid = jpamb.getmethodid(
        "bytecoder",
        "1.0",
        "The Rice Theorem Cookers",
        ["syntactic", "python"],
        for_science=True,
    )

    log = logging
    log.basicConfig(level=logging.DEBUG)

    suite, eff = jpamb.setup()

    log.debug("looking up method")
    m = suite.findmethod(methodid, eff=eff)

    log.debug("trying to find an assertion error being created")
    assert_found = False
    for inst in m["code"]["bytecode"]:
        if (
            inst["opr"] == "invoke"
            and inst["method"]["ref"]["name"] == "java/lang/AssertionError"
        ):
            assert_found = True
            break

    if assert_found:
        log.debug("Found assertion")
        print("assertion error;found")
    else:
        log.debug("No assertion")
        print("assertion error;not-found")

    for q in jpamb.QUERIES:
        if q != "assertion error":
            print(f"{q};skip")
