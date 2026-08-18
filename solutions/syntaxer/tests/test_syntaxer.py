import subprocess


def test_regex():
    subprocess.run(
        "jpamb --workdir ../.. test -f Simple --fail-fast syntaxer-regex > tests/expected/regex",
        shell=True,
        check=True,
    )


def test_treesitter():
    subprocess.run(
        "jpamb --workdir ../.. test -f Simple --fail-fast syntaxer-treesitter > tests/expected/treesitter",
        shell=True,
        check=True,
    )


def test_bytecode():
    subprocess.run(
        "jpamb --workdir ../.. test -f Simple --fail-fast syntaxer-bytecode > tests/expected/bytecode",
        shell=True,
        check=True,
    )
