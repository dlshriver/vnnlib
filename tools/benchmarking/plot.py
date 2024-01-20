#!/usr/bin/env python
import argparse
import dataclasses
import pathlib

import matplotlib.axes
import matplotlib.style
import numpy as np
import pandas as pd


@dataclasses.dataclass
class ParsedArgs:
    old_results: pathlib.Path
    new_results: pathlib.Path
    output_dir: pathlib.Path


def parse_args(args: list[str] | None = None) -> ParsedArgs:
    parser = argparse.ArgumentParser()

    parser.add_argument("old_results", type=pathlib.Path)
    parser.add_argument("new_results", type=pathlib.Path)
    parser.add_argument(
        "-d", "--output_dir", type=pathlib.Path, default=pathlib.Path().resolve()
    )

    return ParsedArgs(**vars(parser.parse_args(args)))


def main(args: list[str] | None = None):
    parsed_args = parse_args(args)

    base_output_dir = parsed_args.output_dir
    output_dir = (
        base_output_dir
        / f"{parsed_args.old_results.stem}--{parsed_args.new_results.stem}"
    )
    output_dir.mkdir(exist_ok=True, parents=True)

    matplotlib.style.use("fivethirtyeight")

    column_names = ("benchmark", "sub_benchmark", "onnx_file", "vnnlib_file", "time")
    old_results_df = pd.read_csv(parsed_args.old_results, names=column_names)
    new_results_df = pd.read_csv(parsed_args.new_results, names=column_names)

    results_df = new_results_df.merge(
        old_results_df, on=column_names[:-1], suffixes=("_new", "_old")
    )
    results_df["speedup"] = results_df["time_old"] / results_df["time_new"]

    results_df["time_old"] = results_df["time_old"] / 1e9
    results_df["time_new"] = results_df["time_new"] / 1e9

    ax = results_df.plot.scatter(x="time_old", y="time_new", figsize=(10, 8))
    lim = max(ax.get_xlim()[1], ax.get_ylim()[1])
    ax.plot([0, lim], [0, lim])
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.figure.savefig(output_dir / "comparison.png")
    ax.figure.clear()

    ax = results_df["speedup"].plot.hist(bins=40, figsize=(10, 8))
    ax.figure.savefig(output_dir / "speedup_hist.png")
    ax.figure.clear()

    num_bins = 10
    time_bins = np.linspace(
        results_df["time_old"].min() - 1e-6,
        results_df["time_old"].max() + 1e-6,
        num_bins + 1,
    )
    results_df["time_old_binned"] = pd.cut(results_df["time_old"], time_bins)
    _df = results_df.pivot(columns="time_old_binned", values="speedup")
    _df = _df.reindex(sorted(_df.columns, key=lambda c: c.left), axis=1)
    ax: matplotlib.axes.Axes = _df.boxplot(figsize=(10, 8))
    ax.set_xticklabels(ax.get_xticklabels(), rotation=22)
    ax.figure.savefig(output_dir / "speedup_box.png", bbox_inches="tight")
    ax.figure.clear()

    num_bins = 10
    time_bins = np.logspace(
        np.log10(results_df["time_old"].min() - 1e-6),
        np.log10(results_df["time_old"].max() + 1e-6),
        num_bins + 1,
    )
    results_df["time_old_binned_log"] = pd.cut(results_df["time_old"], time_bins)
    _df = results_df.pivot(columns="time_old_binned_log", values="speedup")
    sorted_columns = sorted(_df.columns, key=lambda c: c.left)
    _df = _df.reindex(sorted_columns, axis=1)
    ax: matplotlib.axes.Axes = _df.boxplot(figsize=(10, 8))
    ax.set_xticklabels(ax.get_xticklabels(), rotation=22)
    twinx_ax = ax.twinx()
    twinx_ax.bar(
        x=ax.get_xticks(),
        height=results_df["time_old_binned_log"].value_counts(sort=False)[
            sorted_columns
        ],
        alpha=0.2,
    )
    twinx_ax.grid(False)
    ax.figure.savefig(output_dir / "speedup_box_logx.png", bbox_inches="tight")
    ax.figure.clear()


if __name__ == "__main__":
    main()
