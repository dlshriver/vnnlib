Some tools to benchmark vnnlib on existing problems in order to help identify performance regressions.

The following command will run the version of vnnlib at git commit `COMMIT_ID` on all benchmarks from vnncomp2023 and save the timing results to `COMMIT_ID.csv` in the current directory.

```bash
./run_commit.sh COMMIT_ID -b vnncomp2023
```

The `run_commit.sh` script sets up an environment with the specified version of vnnlib and calls out to `run.py`.
The `run.py` script can also be run by itself as:

```bash
./run.py [-b BENCHMARK] [-o OUTPUT] [COMMAND ...]
```

This will run the command `COMMAND` on benchmark `BENCHMARK` and output the results as a csv file at location `OUTPUT`.
`BENCHMARK` can be either `vnncomp2022` or `vnncomp2023` or point to a local directory with the VNN-COMP benchmark structure.
`COMMAND` is the command that will be run for benchmarking, but any instance of `{onnx_file}` or `{vnnlib_file}` will be replaced by the ONNX or VNNLIB files of benchmark instances. For example, the following will run the `vnnlib` module on all instances in the vnncomp2023 benchmark and save the results to `results.csv`:

```bash
./run.py -b vnncomp2023 -o results.csv python -I -W ignore -m vnnlib {vnnlib_file} --compat --no-strict
```
