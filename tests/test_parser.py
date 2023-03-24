from vnnlib.parser import (
    Assert,
    Constant,
    DeclareConst,
    FunctionApplication,
    Script,
    parse_file,
)


def test_parse_string_path(tmp_path):
    vnnlib_path = tmp_path / "test.vnnlib"
    with open(vnnlib_path, "w+"):
        pass

    result = parse_file(str(vnnlib_path))
    assert isinstance(result, Script)
    assert len(result.commands) == 0


def test_empty(tmp_path):
    vnnlib_path = tmp_path / "test.vnnlib"
    with open(vnnlib_path, "w+"):
        pass

    result = parse_file(vnnlib_path)
    assert isinstance(result, Script)
    assert len(result.commands) == 0


def test_string_literal(tmp_path):
    vnnlib_path = tmp_path / "test.vnnlib"
    with open(vnnlib_path, "w+") as f:
        f.write('(declare-const X_0 Real)\n(assert (>= X_0 "test"))\n')

    result = parse_file(vnnlib_path)
    assert isinstance(result, Script)
    assert len(result.commands) == 2
    assert isinstance(result.commands[0], DeclareConst)
    assert isinstance(result.commands[1], Assert)
    assert isinstance(result.commands[1].term, FunctionApplication)
    assert len(result.commands[1].term.terms) == 2
    assert isinstance(result.commands[1].term.terms[1], Constant)
    assert result.commands[1].term.terms[1].value == "test"


def test_binary_literal(tmp_path):
    vnnlib_path = tmp_path / "test.vnnlib"
    with open(vnnlib_path, "w+") as f:
        f.write("(declare-const X_0 Real)\n(assert (>= X_0 #b101))\n")

    result = parse_file(vnnlib_path)
    assert isinstance(result, Script)
    assert len(result.commands) == 2
    assert isinstance(result.commands[0], DeclareConst)
    assert isinstance(result.commands[1], Assert)
    assert isinstance(result.commands[1].term, FunctionApplication)
    assert len(result.commands[1].term.terms) == 2
    assert isinstance(result.commands[1].term.terms[1], Constant)
    assert result.commands[1].term.terms[1].value == 0b101


def test_hex_literal(tmp_path):
    vnnlib_path = tmp_path / "test.vnnlib"
    with open(vnnlib_path, "w+") as f:
        f.write("(declare-const X_0 Real)\n(assert (>= X_0 #xbeef))\n")

    result = parse_file(vnnlib_path)
    assert isinstance(result, Script)
    assert len(result.commands) == 2
    assert isinstance(result.commands[0], DeclareConst)
    assert isinstance(result.commands[1], Assert)
    assert isinstance(result.commands[1].term, FunctionApplication)
    assert len(result.commands[1].term.terms) == 2
    assert isinstance(result.commands[1].term.terms[1], Constant)
    assert result.commands[1].term.terms[1].value == 0xBEEF
