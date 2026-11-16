from dataclasses import dataclass
from dynamic import *

@dataclass
class Trace:
    input: jpamb.case.Input
    pcs: list
    outcome: str

def pushed_constants_in_class(suite, eff, classname, type: str) -> list:
    constants = []
    for method in suite.findclass(classname, eff=eff)["methods"]:
        code = method.get("code") or {}
        for op in code.get("bytecode", []):
            if op["opr"] == "push" and op["value"] is not None and op["value"]["type"] == type:
                constants.append(op["value"]["value"])
    return constants

def syntactically_all_ints_in_class(suite, eff, classname) -> list[int]:
    ints = {0}
    for v in pushed_constants_in_class(suite, eff, classname, "integer"):
        ints.update((v - 1, v, v + 1))
    return sorted(ints)

def syntactically_all_strings_in_class(suite, eff, classname) -> list[str]:
    return sorted(set(pushed_constants_in_class(suite, eff, classname, "string")))

def select_trace(bc, methodid, input, max_steps) -> Trace:
    state = initial(bc, methodid, input)

    pcs = []
    for x in range(max_steps):
        pc, state = step(bc, state)
        pcs.append((pc.method, pc.offset))

        if isinstance(state, str):
            return Trace(input=input, pcs=pcs, outcome=state)

    return Trace(input=input, pcs=pcs, outcome="*")

def analyse_traces(traces: list, number_of_params: int) -> dict:
    outcomes_seen = set()
    for trace in traces:
        outcomes_seen.add(trace.outcome)

    saw_all_traces = False
    if number_of_params == 0:
        if "*" not in outcomes_seen:
            saw_all_traces = True

    answers = {}
    for query in jpamb.QUERIES:
        if query in outcomes_seen:
            if query == "*":
                answers[query] = "timeout"
            else:
                answers[query] = "found"
        else:
            if saw_all_traces:
                answers[query] = "no"
            else:
                answers[query] = "not-found"
    return answers