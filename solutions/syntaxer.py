#!/usr/bin/env python3
"""A very stupid syntatic analysis, that only checks for assertion errors."""

import warnings
import logging
import tree_sitter
import tree_sitter_java
import jpamb
import sys

warnings.filterwarnings("ignore", category=DeprecationWarning) 


methodid = jpamb.getmethodid(
    "syntaxer",
    "1.0",
    "The Rice Theorem Cookers",
    ["syntatic", "python"],
    for_science=True,
)


JAVA_LANGUAGE = tree_sitter.Language(tree_sitter_java.language())
parser = tree_sitter.Parser(JAVA_LANGUAGE)

log = logging
log.basicConfig(level=logging.DEBUG)


srcfile = jpamb.sourcefile(methodid)

with open(srcfile, "rb") as f:
    log.debug("parse sourcefile %s", srcfile)
    tree = parser.parse(f.read())

simple_classname = str(methodid.classname.name)

log.debug(f"{simple_classname}")

# To figure out how to write these you can consult the
# https://tree-sitter.github.io/tree-sitter/playground
class_q = JAVA_LANGUAGE.query(
    f"""
    (class_declaration 
        name: ((identifier) @class-name 
               (#eq? @class-name "{simple_classname}"))) @class
"""
)

for node in tree_sitter.QueryCursor(class_q).captures(tree.root_node)["class"]:
    break
else:
    log.error(f"could not find a class of name {simple_classname} in {srcfile}")

    sys.exit(-1)

# log.debug("Found class %s", node.range)

method_name = methodid.extension.name

method_q = JAVA_LANGUAGE.query(
    f"""
    (method_declaration name: 
      ((identifier) @method-name (#eq? @method-name "{method_name}"))
    ) @method
"""
)

for node in tree_sitter.QueryCursor(method_q).captures(node)["method"]:

    if not (p := node.child_by_field_name("parameters")):
        log.debug(f"Could not find parameteres of {method_name}")
        continue

    params = [c for c in p.children if c.type == "formal_parameter"]

    if len(params) != len(methodid.extension.params):
        continue

    # log.debug(methodid.extension.params)
    # log.debug(params)

    for tn, t in zip(methodid.extension.params, params):
        if (tp := t.child_by_field_name("type")) is None:
            break

        if tp.text is None:
            break

        # todo check for type.
    else:
        break
else:
    log.warning(f"could not find a method of name {method_name} in {simple_classname}")
    sys.exit(-1)

# log.debug("Found method %s %s", method_name, node.range)

body = node.child_by_field_name("body")
assert body and body.text
for t in body.text.splitlines():
    log.debug("line: %s", t.decode())

assert_q = JAVA_LANGUAGE.query(f"""(assert_statement) @assert""")

div_by_0_q = JAVA_LANGUAGE.query(f""" (binary_expression
  operator: "/"
) @expr""")


assert_found = any(
    capture_name == "assert"
    for capture_name, _ in tree_sitter.QueryCursor(assert_q).captures(body).items()
)

division_found = any(
    capture_name == "expr"
    for capture_name, _ in tree_sitter.QueryCursor(div_by_0_q).captures(body).items()
)

if assert_found or division_found:
    log.debug("Found assertion or division expression")
    print("assertion error;80%")
else:
    log.debug("No assertion or division found")
    print("assertion error;20%")

sys.exit(0)
