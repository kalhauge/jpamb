"""Compare a Git baseline with this checkout across all seven configurations.

Run with the project virtual environment from any directory. Raw reports/logs
are retained under reports/branch-refinement by default; failures stop the run.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import jpamb
import sexpr
from jpamb.analyse import Summary
from jpamb.case import Experiment

CONFIGS = [
    "sign",
    "interval",
    "string",
    "sign,interval",
    "sign,string",
    "interval,string",
    "sign,interval,string",
]
BASELINE = "19f0e76af98a7c0f5a80d7955e2683c26973c680"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", default=BASELINE)
    parser.add_argument(
        "--output", type=Path, default=Path("reports/branch-refinement")
    )
    options = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    os.chdir(root)
    output = options.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    baseline = subprocess.check_output(
        ["git", "rev-parse", "--verify", options.baseline + "^{commit}"], text=True
    ).strip()
    source = output / ("baseline-src-" + baseline[:12])
    source.mkdir(exist_ok=True)
    names = subprocess.check_output(
        ["git", "ls-tree", "--name-only", baseline + ":solutions/static/src"], text=True
    ).splitlines()
    for name in names:
        if name.endswith(".py"):
            (source / name).write_bytes(
                subprocess.check_output(
                    ["git", "show", baseline + ":solutions/static/src/" + name]
                )
            )
    for version in ("baseline", "refined"):
        module_dir = source if version == "baseline" else root / "solutions/static/src"
        env = dict(
            os.environ, PYTHONPATH=os.pathsep.join([str(module_dir), str(root / "src")])
        )
        for config in CONFIGS:
            stem = version + "-" + config.replace(",", "-")
            command = [
                str(Path(sys.executable).parent / "jpamb"),
                "analyse",
                "--report",
                str(output / (stem + ".sexp")),
                "--",
                sys.executable,
                "-c",
                "import static; static.analyse()",
                "--abstractions",
                config,
            ]
            with (output / (stem + ".log")).open("w") as log:
                subprocess.run(
                    command, env=env, stdout=log, stderr=subprocess.STDOUT, check=True
                )
            print(stem + " finished", flush=True)
    suite, effect = jpamb.setup()
    benchmark = suite.benchmark(eff=effect)
    rows = []
    for config in CONFIGS:
        stem = config.replace(",", "-")
        summaries = [
            Summary.from_sexpr(
                sexpr.from_string(
                    (output / (version + "-" + stem + ".sexp")).read_text()
                )[0]
            )
            for version in ("baseline", "refined")
        ]
        scores = [
            summary.score_results(benchmark=benchmark, eff=effect)
            for summary in summaries
        ]
        if any(score.invalid is not None for score in scores):
            raise RuntimeError("Invalid analysis report for " + config)
        changes = []
        for method, results in summaries[1].results.items():
            before = summaries[0].results[method][0].response.predictions
            after = results[0].response.predictions
            if any(r.response.predictions != after for r in results):
                raise RuntimeError("Non-deterministic predictions for " + str(method))
            expected = benchmark.experiments[Experiment(method, None)].results
            for outcome, prediction in after.items():
                if str(prediction) == "no" and outcome in expected:
                    raise RuntimeError(
                        "Excluded expected outcome: " + str(method) + " " + outcome
                    )
            difference = {
                key: [str(before[key]), str(after[key])]
                for key in after
                if before[key] != after[key]
            }
            if difference:
                changes.append({"method": str(method), "predictions": difference})
        row = {
            "configuration": config,
            "baseline": baseline,
            "methods": len(summaries[1].results),
            "before": scores[0].total_score,
            "after": scores[1].total_score,
            "changes": changes,
        }
        rows.append(row)
        print(f"{config:24} {row['before']:.2f} -> {row['after']:.2f}", flush=True)
    (output / "comparison.json").write_text(json.dumps(rows, indent=2) + "\n")


if __name__ == "__main__":
    main()
