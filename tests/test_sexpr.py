import sexpr


def test_simple():
    parser = sexpr.Parser.from_string("(step |()| (hello !32) world) (hello)")
    token1 = parser.sexpr()
    token2 = parser.sexpr()

    print(token1, token2)

    assert token1 == []
