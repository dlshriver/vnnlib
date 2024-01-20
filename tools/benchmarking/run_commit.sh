#!/bin/sh
set -e

PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd -P)

python=python3.11
commit_hash=$1
shift

rm -rf /tmp/$commit_hash
$python -m venv /tmp/$commit_hash

/tmp/${commit_hash}/bin/python -m pip install --upgrade pip
/tmp/${commit_hash}/bin/python -m pip install git+file://${PROJECT_DIR}@$commit_hash

/tmp/${commit_hash}/bin/python ${PROJECT_DIR}/benchmark/run.py $@ -o ${commit_hash}.csv /tmp/${commit_hash}/bin/python -I -W ignore -m vnnlib {vnnlib_file} --compat --no-strict
