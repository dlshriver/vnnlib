#!/usr/bin/env python
import argparse
import csv
import dataclasses
import os
import pathlib
import shlex
import subprocess as sp
import sys
import tempfile
import time

BENCHMARK_URLS = {
    "vnncomp2022": "https://github.com/ChristopherBrix/vnncomp2022_benchmarks",
    "vnncomp2023": "https://github.com/ChristopherBrix/vnncomp2023_benchmarks",
}


@dataclasses.dataclass
class ParsedArgs:
    benchmark: list[str]
    output: pathlib.Path | None
    command: list[str]


def parse_args(args: list[str] | None = None) -> ParsedArgs:
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--benchmark", action="append", default=[])
    parser.add_argument("-o", "--output", type=pathlib.Path)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    return ParsedArgs(**vars(parser.parse_args(args)))


def prepare_benchmark(benchmark_name: str) -> None:
    benchmark_origin = BENCHMARK_URLS.get(benchmark_name, benchmark_name)
    print(f"cloning {benchmark_origin}...", file=sys.stderr)
    clone_proc = sp.run(
        shlex.split(f"git clone {benchmark_origin} {benchmark_name}"),
        stderr=sp.PIPE,
        encoding="utf8",
    )
    clone_returncode = clone_proc.returncode
    if clone_returncode != 0:
        raise RuntimeError(
            f"Downloading {benchmark_name} failed with exit code {clone_returncode}."
            f"\n{clone_proc.stderr.strip()}"
        )
    print("decompressing vnnlib files...", file=sys.stderr)
    for gzipped_vnnlib_file in pathlib.Path(benchmark_name).glob(
        "benchmarks/*/vnnlib/*.gz"
    ):
        gunzip_proc = sp.run(shlex.split(f"gunzip -k {str(gzipped_vnnlib_file)!r}"))
        if gunzip_proc.returncode != 0:
            raise RuntimeError("gunzip failed")
    print("decompressing onnx files...", file=sys.stderr)
    for gzipped_onnx_file in pathlib.Path(benchmark_name).glob(
        "benchmarks/*/onnx/*.gz"
    ):
        gunzip_proc = sp.run(shlex.split(f"gunzip -k {str(gzipped_onnx_file)!r}"))
        if gunzip_proc.returncode != 0:
            raise RuntimeError("gunzip failed")


def run_benchmark(
    benchmark: str, command: list[str]
) -> list[tuple[str, str, str, str, int]]:
    benchmarks_dir = pathlib.Path(benchmark) / "benchmarks"
    results = []
    for sub_benchmark in benchmarks_dir.iterdir():
        if not (sub_benchmark / "instances.csv").exists():
            continue
        with open(sub_benchmark / "instances.csv", newline="") as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                formatted_command = [
                    arg.format(
                        onnx_file=sub_benchmark / row[0],
                        vnnlib_file=sub_benchmark / row[1],
                    )
                    for arg in command
                ]
                print(" ".join(formatted_command), file=sys.stderr)
                start_t = time.perf_counter_ns()
                proc = sp.run(formatted_command, stdout=sp.PIPE, stderr=sp.STDOUT)
                end_t = time.perf_counter_ns()
                if proc.returncode != 0:
                    print(proc.stdout.decode(), file=sys.stderr)
                    raise RuntimeError("Process failed.")
                results.append(
                    (
                        benchmark,
                        sub_benchmark.name,
                        (sub_benchmark / row[0]).name,
                        (sub_benchmark / row[1]).name,
                        end_t - start_t,
                    )
                )
    return results


def main(args: list[str] | None = None):
    parsed_args = parse_args(args)

    output_path = parsed_args.output.resolve() if parsed_args.output else None

    with tempfile.TemporaryDirectory() as working_dir:
        os.chdir(working_dir)

        results = []
        for benchmark in parsed_args.benchmark:
            prepare_benchmark(benchmark)
            results.extend(run_benchmark(benchmark, parsed_args.command))

        if output_path:
            with open(output_path, "w") as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerows(results)
        else:
            for result in results:
                print(",".join(map(str, result)))


if __name__ == "__main__":
    main()
