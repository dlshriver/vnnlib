from vnnlib.tokenizer import EOF, tokenize


def test_comment():
    vnnlib_script = "; test comment\n"
    tokens = list(tokenize(vnnlib_script))
    assert len(tokens) == 1
    assert tokens[0] == EOF

    vnnlib_script = "; another test comment without a new line"
    tokens = list(tokenize(vnnlib_script))
    assert len(tokens) == 1
    assert tokens[0] == EOF


def test_numeral():
    vnnlib_script = "0"
    tokens = list(tokenize(vnnlib_script))
    assert len(tokens) == 2
    assert tokens[0][0] == "NUMERAL"
    assert tokens[0][1] == "0"
    assert tokens[-1] == EOF

    vnnlib_script = "931870"
    tokens = list(tokenize(vnnlib_script))
    assert len(tokens) == 2
    assert tokens[0][0] == "NUMERAL"
    assert tokens[0][1] == "931870"
    assert tokens[-1] == EOF


def test_decimal_strict():
    vnnlib_script = "0.123"
    tokens = list(tokenize(vnnlib_script))
    assert len(tokens) == 2
    assert tokens[0][0] == "DECIMAL"
    assert tokens[0][1] == "0.123"
    assert tokens[-1] == EOF

    vnnlib_script = "931870.651"
    tokens = list(tokenize(vnnlib_script))
    assert len(tokens) == 2
    assert tokens[0][0] == "DECIMAL"
    assert tokens[0][1] == "931870.651"
    assert tokens[-1] == EOF


def test_decimal_non_strict():
    vnnlib_script = "513e-3"
    tokens = list(tokenize(vnnlib_script, strict=False))
    assert len(tokens) == 2
    assert tokens[0][0] == "DECIMAL"
    assert tokens[0][1] == "513e-3"
    assert tokens[-1] == EOF

    vnnlib_script = "0.123e5"
    tokens = list(tokenize(vnnlib_script, strict=False))
    assert len(tokens) == 2
    assert tokens[0][0] == "DECIMAL"
    assert tokens[0][1] == "0.123e5"
    assert tokens[-1] == EOF

    vnnlib_script = "931870.651e-17"
    tokens = list(tokenize(vnnlib_script, strict=False))
    assert len(tokens) == 2
    assert tokens[0][0] == "DECIMAL"
    assert tokens[0][1] == "931870.651e-17"
    assert tokens[-1] == EOF


def test_string_literal():
    vnnlib_script = '"string"'
    tokens = list(tokenize(vnnlib_script, strict=False))
    assert len(tokens) == 2
    assert tokens[0][0] == "STRING"
    assert tokens[0][1] == '"string"'
    assert tokens[-1] == EOF

    vnnlib_script = '"string with ""quoted string"""'
    tokens = list(tokenize(vnnlib_script, strict=False))
    assert len(tokens) == 2
    assert tokens[0][0] == "STRING"
    assert tokens[0][1] == '"string with ""quoted string"""'
    assert tokens[-1] == EOF


def test_quoted_symbol():
    vnnlib_script = "|test symbol|"
    tokens = list(tokenize(vnnlib_script, strict=False))
    assert len(tokens) == 2
    assert tokens[0][0] == "SYMBOL"
    assert tokens[0][1] == "test symbol"
    assert tokens[-1] == EOF


def test_empty():
    vnnlib_script = ""
    tokens = list(tokenize(vnnlib_script, strict=False))
    assert len(tokens) == 1
    assert tokens[-1] == EOF
