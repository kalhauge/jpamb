import subprocess


def test_regex():
    subprocess.run(
        "jpamb --workdir ../.. test -f Simple --fail-fast syntatic-regex > tests/expected/regex",
        shell=True,
        check=True,
    )


def test_treesitter():
    subprocess.run(
        "jpamb --workdir ../.. test -f Simple --fail-fast syntatic-treesitter > tests/expected/treesitter",
        shell=True,
        check=True,
    )


def test_bytecode():
    subprocess.run(
        "jpamb --workdir ../.. test -f Simple --fail-fast syntatic-bytecode > tests/expected/bytecode",
        shell=True,
        check=True,
    )
