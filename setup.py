import sys
from setuptools import setup
from mypyc.build import mypycify

setup(
    name="vnnlib",
    packages=["vnnlib"],
    ext_modules=mypycify(
        [
            "vnnlib/tokenizer.py",
            "vnnlib/parser.py",
        ]
    )
    if sys.implementation.name == "cpython"
    else [],
)
