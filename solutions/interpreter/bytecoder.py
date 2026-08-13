#!/usr/bin/env python3
"""A very stupid syntatic bytecode analysis, that only checks for assertion errors."""

import sys
import logging

import jpamb

methodid = jpamb.getmethodid(
    "bytecoder",
    "1.0",
    "The Rice Theorem Cookers",
    ["syntatic", "python"],
    for_science=True,
)

log = logging
log.basicConfig(level=logging.DEBUG)

log.debug("check assertion")
log.debug("read the method name")

log.debug("looking up method")
m = jpamb.Suite().findmethod(methodid)

log.debug("trying to find an assertion error being created")
for inst in m["code"]["bytecode"]:
    if (
        inst["opr"] == "invoke"
        and inst["method"]["ref"]["name"] == "java/lang/AssertionError"
    ):
        break
else:
    # I'm pretty sure the answer is no
    log.debug("did not find it")
    print("assertion error;20%")
    sys.exit(0)

log.debug("Found it")
# I'm kind of sure the answer is yes.
print("assertion error;80%")
