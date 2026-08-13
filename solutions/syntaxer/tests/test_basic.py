import subprocess


def test_regex():
    subprocess.run(
        "jpamb --workdir ../.. test --fail-fast syntaxer-regex > tests/expected-regex",
        shell=True,
        check=True,
    )


def test_treesitter():
    subprocess.run(
        "jpamb --workdir ../.. test --fail-fast syntaxer-treesitter > tests/expected-treesitter",
        shell=True,
        check=True,
    )
