import click
from datetime import datetime
import math
import numpy as np
from pathlib import Path
import json
import pandas as pd

from . import suite


def get_maxpoints():
    import csv

    with open("stats/distribution.csv", encoding="utf-8") as fp:
        reader = list(csv.DictReader(fp))
        return (len(reader) - 1) * (len(reader[0]) - 1)


def get_kind(technologies):
    is_syntactic = "syntactic" in technologies
    is_static = "static" in technologies
    is_dynamic = "dynamic" in technologies
    is_cheater = "cheater" in technologies

    kind = None

    if is_static:
        kind = "static"

    if is_dynamic:
        kind = "dynamic"

    if is_syntactic:
        kind = "syntactic"

    if is_static and is_dynamic:
        kind = "hybrid"

    if is_cheater:
        kind = "cheater"

    if kind is None:
        kind = "adhoc"

    return kind


def analyse(experiment, logger):
    tools = []
    all_results = []
    version = (datetime.fromtimestamp(experiment["timestamp"] / 1000),)
    group = experiment["group_name"]
    for tool, ctx in experiment["tools"].items():
        results = []
        for r in ctx["results"]:
            fid = f"{group}/{tool}/{r['method']}"
            if r["time"] == "NaN":
                logger.warning(f"Found NaN in time, skipping {fid}")
                continue
            absolute = r["time"] / 1_000_000
            relative = math.log10(r["relative"])
            score = r["score"]
            if r["score"] > 6:
                logger.debug(r)
                logger.warning(
                    f"Found score {r['score']} is higher than 6, skipping {fid}"
                )
                continue
            results.append(
                {
                    "group": group,
                    "tool": tool,
                    "version": version,
                    "method": r["method"],
                    "score": max(score, 1),
                    "kind": get_kind(ctx["technologies"]),
                    "absolute": absolute,
                    "relative": relative,
                }
            )

        df = pd.DataFrame(results)
        all_results.extend(results)
        # todo pick best here?
        first = df.groupby(["method"]).first()

        tools.append(
            {
                "group": group,
                "tool": tool,
                "version": version,
                "kind": get_kind(ctx["technologies"]),
                "technologies": ctx["technologies"],
                "score": first.score.sum(),
                "absolute": first.absolute.mean(),
                "relative": np.pow(10, first.relative.mean()),
            }
        )

    return (tools, all_results)


@click.command()
@click.option("-v", "--verbose", count=True)
@click.option("-o", "--report", type=click.Path(path_type=Path), default="report")
@click.argument(
    "FILES", nargs=-1, type=click.Path(exists=True, readable=True, path_type=Path)
)
def stats(files, report, verbose):
    """A program for calculating and presenting the stats of
    a collection of experiments.
    """

    logger = suite.setup_logger(verbose)

    results = []
    tools = []

    def handle_result(result):
        try:
            _tools, tool_results = analyse(result, logger)
            results.extend(tool_results)
            tools.extend(_tools)
        except KeyError as e:
            logger.debug(sorted(result))
            logger.warning(f"Key error {e}, skipping.")

    for file in files:
        logger.info(f"Analysing {file!r}")

        if file.suffix == ".zip":
            import zipfile

            with zipfile.ZipFile(file) as zf:
                for entry in zf.infolist():
                    if not entry.filename.endswith(".json"):
                        logger.trace(f"Ignoreing {entry.filename!r}")
                        continue
                    logger.info(f"Unpacking {entry.filename!r}")
                    content = zf.read(entry)
                    try:
                        txt = content.decode("utf-8-sig")
                    except UnicodeDecodeError:
                        txt = content.decode("utf-16")
                    handle_result(json.loads(txt))
            continue

        try:
            with open(file, encoding="utf-8-sig") as fp:
                handle_result(json.load(fp))
        except UnicodeDecodeError:
            with open(file, encoding="utf-16") as fp:
                handle_result(json.load(fp))

    logger.success(f"Analysed {len(files)} file")

    report.mkdir(exist_ok=True)

    results_df = pd.DataFrame(results)
    score_per_method = (
        results_df[results_df["score"] > 0]
        .groupby("method")[["score"]]
        .sum()["score"]
        .sort_values()
    )

    tools_df = pd.DataFrame(tools)

    import plotly.graph_objects as go

    colors = {
        "cheater": "red",
        "hybrid": "blue",
        "static": "green",
        "dynamic": "yellow",
        "syntactic": "teal",
        "adhoc": "brown",
    }

    symbols = {
        "cheater": 0,
        "hybrid": 1,
        "static": 2,
        "dynamic": 3,
        "syntactic": 4,
        "adhoc": 5,
    }

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=tools_df["relative"],
            y=tools_df["score"],
            name="?",
            mode="markers",
            marker=dict(
                color=[colors[k] for k in tools_df["kind"]],
                symbol=[symbols[k] for k in tools_df["kind"]],
            ),
            text=[
                f"{tools_df.iloc[i].group}/{tools_df.iloc[i].tool}<br>{tools_df.iloc[i].technologies}"
                for i in tools_df.index
            ],
        )
    )
    fig.update_xaxes(type="log")

    fig.update_layout(
        title="Progress by Tool",
        template="seaborn",
        yaxis=dict(range=[-20, get_maxpoints()]),
    )
    fig.update_traces(marker_size=10)
    fig.write_html(report / "progress.html")

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=score_per_method.index,
            x=score_per_method,
            orientation="h",
        )
    )
    fig.update_layout(
        title="Score per Method",
        template="seaborn",
    )
    fig.write_html(report / "score-per-method.html")

    print(
        tools_df.set_index(["group", "tool", "version"])[["kind", "score", "relative"]]
    )
