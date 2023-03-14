import pytest

from vnnlib.errors import ParserError
from vnnlib.parser import parse_file


def test_unknown_string_1(tmp_path):
    vnnlib_path = tmp_path / "test.vnnlib"
    with open(vnnlib_path, "w+") as f:
        f.write("|applesauce")

    with pytest.raises(ParserError, match="Unknown string:"):
        _ = parse_file(vnnlib_path)


def test_unknown_string_2(tmp_path):
    vnnlib_path = tmp_path / "test.vnnlib"
    with open(vnnlib_path, "w+") as f:
        f.write("|")

    with pytest.raises(ParserError, match="Unknown string:"):
        _ = parse_file(vnnlib_path)


def test_unknown_command(tmp_path):
    vnnlib_path = tmp_path / "test.vnnlib"
    with open(vnnlib_path, "w+") as f:
        f.write('(applesauce"')

    with pytest.raises(ParserError, match="Unknown command:"):
        _ = parse_file(vnnlib_path)


def test_undeclared_sort(tmp_path):
    vnnlib_path = tmp_path / "test.vnnlib"
    with open(vnnlib_path, "w+") as f:
        f.write("(declare-const x_0 FLOAT)\n")

    with pytest.raises(ParserError, match="Undeclared sort:"):
        _ = parse_file(vnnlib_path)


def test_undeclared_identifier(tmp_path):
    vnnlib_path = tmp_path / "test.vnnlib"
    with open(vnnlib_path, "w+") as f:
        f.write(
            "(declare-const x_0 Real)\n"
            "(assert (>= x_0 0))\n"
            "(assert (>= x_0 x_1))\n"
        )

    with pytest.raises(ParserError, match="Undeclared identifier:"):
        _ = parse_file(vnnlib_path)


def test_undeclared_identifier_strict_exponential(tmp_path):
    vnnlib_path = tmp_path / "test.vnnlib"
    with open(vnnlib_path, "w+") as f:
        f.write(
            "(declare-const x_0 Real)\n"
            "(assert (>= x_0 0.0e0))\n"
            "(assert (>= x_0 x_1))\n"
        )

    with pytest.raises(ParserError, match="Undeclared identifier:"):
        _ = parse_file(vnnlib_path)


def test_unexpected_token_1(tmp_path):
    vnnlib_path = tmp_path / "test.vnnlib"
    with open(vnnlib_path, "w+") as f:
        f.write("(declare-const x_0 Real)\n(assert )\n")

    with pytest.raises(ParserError, match="Unexpected token:"):
        _ = parse_file(vnnlib_path)


def test_unexpected_token_2(tmp_path):
    vnnlib_path = tmp_path / "test.vnnlib"
    with open(vnnlib_path, "w+") as f:
        f.write("(declare-const x_0 Real)\nassert )\n")

    with pytest.raises(ParserError, match="Unexpected token:"):
        _ = parse_file(vnnlib_path)


def test_unexpected_token_3(tmp_path):
    vnnlib_path = tmp_path / "test.vnnlib"
    with open(vnnlib_path, "w+") as f:
        f.write("(declare-const 0 Real)\n")

    with pytest.raises(ParserError, match="Unexpected token:"):
        _ = parse_file(vnnlib_path)
