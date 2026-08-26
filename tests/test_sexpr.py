from sexpr import Step, check_step
import sexpr
from hypothesis import given, note, strategies as st


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

    steps = [Step(e[1], e[2], e[3]) for e in sexpr.from_string(str_test)]

    for i in range(len(steps) - 1):
        assert check_step(steps[i], steps[i + 1]), (
            f"{steps[i].next_state} is not equal to {steps[i + 1].state}"
        )


def test_pretty():
    assert sexpr.pretty("ref 0") == "|ref 0|"
    assert sexpr.pretty("hello") == "hello"
    assert sexpr.pretty([[], ["hello", "world"]]) == "(() (hello world))"


def st_sexpr():
    return st.recursive(st.text(), extend=lambda xs: st.lists(xs))


@given(st_sexpr())
def test_tripping(expr):
    string = sexpr.pretty(expr)
    note(string)
    items = sexpr.from_string(string)
    assert len(items) == 1
    assert items[0] == expr
