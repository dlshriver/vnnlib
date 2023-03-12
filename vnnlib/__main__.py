from __future__ import annotations

import argparse
import pickle
from pathlib import Path

from .compat import CompatTransformer
from .parser import parse_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        "vnnlib",
        description="",
    )
    parser.add_argument("file", type=Path)
    parser.add_argument(
        "--compat", action="store_true", help="Use the VNN-COMP-1 output format"
    )
    parser.add_argument(
        "--strict",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Whether or not to strictly follow VNN-LIB (default: True)",
    )
    parser.add_argument(
        "-o", "--output", type=str, help="The path to save the compiled output"
    )
    return parser.parse_args()


def __main__() -> None:
    args = parse_args()
    file: Path = args.file
    print(f"parsing file: {args.file}")

    if args.compat:
        if ".vnnlib" in file.suffixes:
            ast_node = parse_file(file, strict=args.strict)
            result = CompatTransformer("X", "Y").transform(ast_node)
            if args.output:
                with open(args.output, "wb+") as f:
                    pickle.dump(result, f)
        else:
            raise RuntimeError(f"Unsupported file type: {file.suffix}")
    else:
        raise NotImplementedError(
            "Currently only the VNN-COMP-1 output format is supported"
        )


if __name__ == "__main__":
    __main__()
