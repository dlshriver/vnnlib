import pytest

from vnnlib.errors import TokenizerError
from vnnlib.parser import parse_file


def test_unknown_string_1(tmp_path):
    vnnlib_path = tmp_path / "test.vnnlib"
    with open(vnnlib_path, "w+") as f:
        f.write("|applesauce")

    with pytest.raises(TokenizerError, match="unexpected end of file"):
        _ = parse_file(vnnlib_path)


def test_unknown_string_2(tmp_path):
    vnnlib_path = tmp_path / "test.vnnlib"
    with open(vnnlib_path, "w+") as f:
        f.write("|")

    with pytest.raises(TokenizerError, match="unexpected end of file"):
        _ = parse_file(vnnlib_path)


def test_undeclared_identifier_strict_exponential(tmp_path):
    vnnlib_path = tmp_path / "test.vnnlib"
    with open(vnnlib_path, "w+") as f:
        f.write(
            "(declare-const x_0 Real)\n"
            "(assert (>= x_0 0.0e0))\n"
            "(assert (>= x_0 x_1))\n"
        )

    with pytest.raises(TokenizerError, match="invalid decimal in strict mode: 0.0e"):
        _ = parse_file(vnnlib_path)


def test_strict_exponential(tmp_path):
    vnnlib_path = tmp_path / "test.vnnlib"
    with open(vnnlib_path, "w+") as f:
        f.write("(declare-const x_0 Real)\n" "(assert (>= x_0 5e1))\n")

    with pytest.raises(TokenizerError, match="invalid decimal in strict mode: 5e"):
        _ = parse_file(vnnlib_path)


def test_invalid_number_prefix(tmp_path):
    vnnlib_path = tmp_path / "test.vnnlib"
    with open(vnnlib_path, "w+") as f:
        f.write("(declare-const x_0 Real)\n" "(assert (>= x_0 #o555))\n")

    with pytest.raises(TokenizerError, match="invalid number prefix: #o"):
        _ = parse_file(vnnlib_path)


def test_invalid_character(tmp_path):
    vnnlib_path = tmp_path / "test.vnnlib"
    with open(vnnlib_path, "w+") as f:
        f.write("'")

    with pytest.raises(TokenizerError, match="unexpected character: '"):
        _ = parse_file(vnnlib_path)
