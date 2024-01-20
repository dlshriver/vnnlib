from __future__ import annotations

import argparse
import pickle
import sys
from pathlib import Path
from typing import Optional, Sequence

from .__version__ import __version__
from .compat import CompatTransformer
from .errors import VnnLibError
from .parser import parse_file


def parse_args(args: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        "vnnlib",
        description="",
    )
    parser.add_argument("-V", "--version", action="version", version=__version__)

    parser.add_argument("file", type=Path)
    parser.add_argument(
        "--compat", action="store_true", help="Use the VNN-COMP-1 output format"
    )
    if sys.version_info >= (3, 9, 0):
        parser.add_argument(
            "--strict",
            action=argparse.BooleanOptionalAction,
            default=True,
            help="Whether or not to strictly follow VNN-LIB (default: True)",
        )
    else:
        parser.add_argument(
            "--strict",
            action="store_true",
            default=True,
            help="Whether or not to strictly follow VNN-LIB (default: True)",
        )
        parser.add_argument(
            "--no-strict",
            action="store_false",
            help="Whether or not to strictly follow VNN-LIB",
            dest="strict",
        )
    parser.add_argument(
        "-o", "--output", type=str, help="The path to save the compiled output"
    )
    return parser.parse_args(args)


def main(args: Optional[Sequence[str]] = None) -> None:
    parsed_args = parse_args(args)
    file: Path = parsed_args.file
    print(f"parsing file: {parsed_args.file}")
    print(parsed_args)

    if parsed_args.compat:
        if ".vnnlib" in file.suffixes:
            ast_node = parse_file(file, strict=parsed_args.strict)
            result = CompatTransformer("X", "Y").transform(ast_node)
            if parsed_args.output:
                with open(parsed_args.output, "wb+") as f:
                    pickle.dump(result, f)
        else:
            raise VnnLibError(f"Unsupported file type: {file.suffix}")
    else:
        raise NotImplementedError(
            "Currently only the VNN-COMP-1 output format is supported"
        )
