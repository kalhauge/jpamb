from jpamb import jvm
from jpamb.model import Suite, Input

from typing import NoReturn, Any

from pathlib import Path


def getmethodid(
    name: str,
    version: str,
    group: str,
    tags: list[str],
    for_science: bool,
) -> jvm.AbsMethodID:
    """Get the method id from the program arguments, or output the info."""

    import sys

    mid = sys.argv[1]
    if mid == "info":
        printinfo(name, version, group, tags, for_science)

    return parse_methodid(mid)


def getcase() -> tuple[jvm.AbsMethodID, Input]:
    """Get the case from the program arguments."""
    import sys

    mid = sys.argv[1]
    i = sys.argv[2]

    return parse_methodid(mid), parse_input(i)


def printinfo(
    name: str,
    version: str,
    group: str,
    tags: list[str],
    for_science: bool,
) -> NoReturn:
    print(name)
    print(version)
    print(group)
    print(",".join(tags))
    if for_science:
        import platform

        print(platform.platform())

    import sys

    sys.exit(0)


def sourcefile(lookup: jvm.Absolute[Any] | jvm.ClassName) -> Path:
    return Suite().sourcefile(lookup.classname)


def classfile(lookup: jvm.Absolute[Any] | jvm.ClassName) -> Path:
    return Suite().classfile(lookup.classname)


def parse_methodid(mid) -> jvm.AbsMethodID:
    return jvm.AbsMethodID.decode(mid)


def parse_input(i) -> Input:
    return Input.decode(i)
