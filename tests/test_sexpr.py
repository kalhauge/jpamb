from sexpr import Step, check_step
import sexpr


def test_small_frame():
    parser = sexpr.Parser.from_string(
        "( FRAME ( LOCALS (int 11) ) ( STACK (ref None) ) )"
    )
    token1 = parser.sexpr()

    print(token1)

    assert token1 == ["FRAME", ["LOCALS", ["int", "11"]], ["STACK", ["ref", "None"]]]


def test_larger_frame():
    parser = sexpr.Parser.from_string(
        "( FRAME ( LOCALS (int 11) (ref None) ) ( STACK (ref None) (int 1) (int 10) ) )"
    )

    token1 = parser.sexpr()

    assert token1 == [
        "FRAME",
        ["LOCALS", ["int", "11"], ["ref", "None"]],
        ["STACK", ["ref", "None"], ["int", "1"], ["int", "10"]],
    ]


def test_heap_array():
    parser = sexpr.Parser.from_string(
        "(( Array:I 0 0 ) ( FRAME ( LOCALS ) ( STACK (ref 0) ) ))"
    )

    token1 = parser.sexpr()

    print(token1)

    assert token1 == [
        ["Array:I", "0", "0"],
        ["FRAME", ["LOCALS"], ["STACK", ["ref", "0"]]],
    ]


def test_checker():
    str_test = "( STEP ( ( Array:C 120 ) ( FRAME ( LOCALS (ref 0) ) ) ) ( OPR ( get static jpamb/cases/Arrays.$assertionsDisabled:Z )) ( ( Array:C 120 ) ( FRAME ( LOCALS (ref 0) ) ( STACK (int 0) ) ) ) ) \
    ( STEP ( ( Array:C 120 ) ( FRAME ( LOCALS (ref 0) ) ( STACK (int 0) ) ) ) ( OPR ( ifz ne 31 )) ( ( Array:C 120 ) ( FRAME ( LOCALS (ref 0) ) ) ) )"

    parser = sexpr.Parser.from_string(str_test)

    token1 = parser.sexpr()
    token2 = parser.sexpr()

    states1 = Step(token1[1], token1[2], token1[3])
    states2 = Step(token2[1], token2[2], token2[3])

    assert check_step(states1, states2)


def test_checker_many():
    str_test = "( STEP ( ( Array:C 120 ) ( FRAME ( LOCALS (ref 0) ) ) ) ( OPR ( get static jpamb/cases/Arrays.$assertionsDisabled:Z )) ( ( Array:C 120 ) ( FRAME ( LOCALS (ref 0) ) ( STACK (int 0) ) ) ) ) \
    ( STEP ( ( Array:C 120 ) ( FRAME ( LOCALS (ref 0) ) ( STACK (int 0) ) ) ) ( OPR ( ifz ne 31 )) ( ( Array:C 120 ) ( FRAME ( LOCALS (ref 0) ) ) ) ) \
    ( STEP ( ( Array:C 120 ) ( FRAME ( LOCALS (ref 0) ) ) ) ( OPR ( load:A 0 )) ( ( Array:C 120 ) ( FRAME ( LOCALS (ref 0) ) ( STACK (ref 0) ) ) ) ) \
    ( STEP ( ( Array:C 120 ) ( FRAME ( LOCALS (ref 0) ) ( STACK (ref 0) ) ) ) ( OPR ( push:I 0 )) ( ( Array:C 120 ) ( FRAME ( LOCALS (ref 0) ) ( STACK (ref 0) (int 0) ) ) ) ) \
    ( STEP ( ( Array:C 120 ) ( FRAME ( LOCALS (ref 0) ) ( STACK (ref 0) (int 0) ) ) ) ( OPR ( array_load:C )) ( ( Array:C 120 ) ( FRAME ( LOCALS (ref 0) ) ( STACK (int 120) ) ) ) ) \
    ( STEP ( ( Array:C 120 ) ( FRAME ( LOCALS (ref 0) ) ( STACK (int 120) ) ) ) ( OPR ( push:I 104 )) ( ( Array:C 120 ) ( FRAME ( LOCALS (ref 0) ) ( STACK (int 120) (int 104) ) ) ) ) \
    ( STEP ( ( Array:C 120 ) ( FRAME ( LOCALS (ref 0) ) ( STACK (int 120) (int 104) ) ) ) ( OPR ( if ne 27 )) ( ( Array:C 120 ) ( FRAME ( LOCALS (ref 0) ) ) ) )"

    parser = sexpr.Parser.from_string(str_test)

    steps = []
    current_expr = parser.sexpr()

    while current_expr is not None:
        steps.append(Step(current_expr[1], current_expr[2], current_expr[3]))
        current_expr = parser.sexpr()

    for i in range(len(steps) - 2):
        assert check_step(steps[i], steps[i + 1]), (
            f"{steps[i].next_state} is not equal to {steps[i + 1].state}"
        )
