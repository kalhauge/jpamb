import subprocess


def test_expected():
    subprocess.run(
        "jpamb --workdir ../.. test --fail-fast basic > tests/expected",
        shell=True,
        check=True,
    )
