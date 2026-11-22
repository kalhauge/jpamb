from hypothesis.strategies import none
import sys
import re
import logging
from pathlib import Path

import tree_sitter_java as tsjava
from tree_sitter import Language, Node, Parser

import jpamb
from jpamb import jvm

def getDictFromMethodId(absmethodid: jvm.AbsMethodID) -> list[int]:
    log = logging
    log.basicConfig(level=logging.DEBUG)

    suite, _ = jpamb.setup()

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

    intConstants = getDictFromSrc(rest)

    if not intConstants:
        log.error("Could not find end of block")
        log.error(rest)
        sys.exit(1)

    return intConstants
    
def getDictFromSrc(methodeCodeToEoF: str) -> list[int] | None:
    # ok when closing bracket hits, i am basically forced to end... solved by treesitter (later)
    
    blockClose = methodeCodeToEoF.find("}")
    if blockClose == -1:
        return None

    block = methodeCodeToEoF[:blockClose]
    INT_RE = re.compile(r"(?<![\w.])-?\d+(?![\w.])")
    constants = [int(x) for x in INT_RE.findall(block)] 

    return constants


# Tree sitter version:

JAVA = Language(tsjava.language())
PARSER = Parser(JAVA)


def _walk(node: Node):
    """Depth-first, document order."""
    yield node
    for child in node.children:
        yield from _walk(child)


def _parse_decimal(node: Node) -> int:
    """Turn a decimal_integer_literal node into an int, including a leading unary minus."""
    text = node.text.decode().replace("_", "").rstrip("lL")
    value = int(text)
    parent = node.parent
    # In tree-sitter-java, "-1" is unary_expression("-", decimal_integer_literal("1"))
    if (
        parent is not None
        and parent.type == "unary_expression"
        and parent.children[0].type == "-"
    ):
        value = -value
    return value


def getIntsFromSrcTS(src: bytes, methodName: str) -> set[int] | None:
    """All decimal int literals inside the first method_declaration called methodName.
    Returns None if the method does not exist."""
    tree = PARSER.parse(src)

    method = next(
        (
            n
            for n in _walk(tree.root_node)
            if n.type == "method_declaration"
            and n.child_by_field_name("name").text.decode() == methodName
        ),
        None,
    )
    if method is None:
        return None

    # method.start_byte/end_byte is the exact span of the declaration,
    # so we cannot overshoot into the next method or stop at an inner '}'.
    return set([
        _parse_decimal(n)
        for n in _walk(method)
        if n.type == "decimal_integer_literal"
    ])

#return value should be a set instead probably
def getDictFromMethodIdTS(absmethodid: jvm.AbsMethodID) -> set[int]:
    log = logging
    log.basicConfig(level=logging.DEBUG)

    suite, _ = jpamb.setup()
    srcfile = suite.sourcefile(absmethodid.classname).relative_to(Path.cwd())

    log.debug("parse sourcefile %s", srcfile)
    with open(srcfile, "rb") as f:  # bytes, tree-sitter works on bytes
        src = f.read()

    intConstants = getIntsFromSrcTS(src, absmethodid.methodid.name)

    if intConstants is None:
        log.error("Could not find method %s", absmethodid.methodid.name)
        sys.exit(1)

    return intConstants

INT_MIN, INT_MAX = -2**31, 2**31 - 1
def augmentWithBoundryValues(constants: set[int]) -> set[int]:
    base = set(constants) | {INT_MIN, INT_MAX, -1, 0, 1}
    result = base | {x + d for x in base for d in (-1, 1)}
    return {v for v in result if INT_MIN <= v <= INT_MAX}

