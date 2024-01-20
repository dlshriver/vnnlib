from __future__ import annotations

from typing import Final, Iterator, Tuple

from .errors import TokenizerError

Token = Tuple[str, str]

DUMMY_TOKEN: Final[Token] = ("_", "")
EOF: Final[Token] = ("EOF", "")


class Tokenizer:
    def __init__(
        self, text: str, strict=True, keep_comments=False, keep_whitespace=False
    ):
        self.text = text
        self.strict = strict
        self.keep_comments = keep_comments
        self.keep_whitespace = keep_whitespace

    def __iter__(self) -> Iterator[Token]:
        if len(self.text) == 0:
            yield EOF
            return

        whitespace = frozenset("\x09\x0a\x0d\x20")
        digits = frozenset("0123456789")
        hex_digits = frozenset("0123456789abcdefABCDEF")
        bin_digits = frozenset("01")
        letters = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
        characters = frozenset("~!@$%^&*+=<>.?/_-")
        letters_and_chars = letters | characters
        letters_chars_and_digits = letters_and_chars | digits

        character_stream = iter(self.text)
        try:
            completed_token = True
            c = next(character_stream)
            while c != "":
                completed_token = True
                if c in whitespace:
                    c = next(character_stream)
                elif c == "(":
                    yield ("LPAREN", c)
                    c = next(character_stream)
                elif c == ")":
                    yield ("RPAREN", c)
                    c = next(character_stream)
                elif c in letters_and_chars:
                    completed_token = False
                    symbol = []
                    while c in letters_chars_and_digits:
                        symbol.append(c)
                        c = next(character_stream, "")
                    yield ("SYMBOL", "".join(symbol))
                elif c == ";":
                    while c != "\n" and c != "\r":
                        c = next(character_stream)
                elif c in digits:
                    completed_token = False
                    number = []
                    while c in digits:
                        number.append(c)
                        c = next(character_stream, "")
                    if c not in {".", "e", "E"}:
                        yield ("NUMERAL", "".join(number))
                        continue
                    elif c in {"e", "E"} and self.strict:
                        raise TokenizerError(
                            f"invalid decimal in strict mode: {''.join(number+[c])}"
                        )
                    number.append(c)
                    c = next(character_stream)
                    while c in digits:
                        number.append(c)
                        c = next(character_stream, "")
                    if c not in {"e", "E", "+", "-"}:
                        yield ("DECIMAL", "".join(number))
                        continue
                    elif self.strict:
                        raise TokenizerError(
                            f"invalid decimal in strict mode: {''.join(number+[c])}"
                        )
                    number.append(c)
                    c = next(character_stream)
                    if c in {"+", "-"}:
                        number.append(c)
                        c = next(character_stream)
                    while c in digits:
                        number.append(c)
                        c = next(character_stream, "")
                    yield ("DECIMAL", "".join(number))
                elif c == "#":
                    completed_token = False
                    c = next(character_stream)
                    if c == "x":
                        c = next(character_stream)
                        number = ["#x"]
                        while c in hex_digits:
                            number.append(c)
                            c = next(character_stream, "")
                        yield ("HEXADECIMAL", "".join(number))
                    elif c == "b":
                        c = next(character_stream)
                        number = ["#b"]
                        while c in bin_digits:
                            number.append(c)
                            c = next(character_stream, "")
                        yield ("BINARY", "".join(number))
                    else:
                        raise TokenizerError(f"invalid number prefix: #{c}")
                elif c == '"':
                    completed_token = False
                    string = []
                    num_quotes = 1
                    while c == '"' or num_quotes % 2 == 1:
                        string.append(c)
                        c = next(character_stream, "")
                        if c == '"':
                            num_quotes += 1
                    yield ("STRING", "".join(string))
                elif c == "|":
                    completed_token = False
                    symbol = []
                    c = next(character_stream)
                    while c != "|" and c != "\\":
                        symbol.append(c)
                        c = next(character_stream)
                    yield ("SYMBOL", "".join(symbol))
                    completed_token = True
                    c = next(character_stream)
                else:
                    raise TokenizerError(f"unexpected character: {c}")
            yield EOF
        except StopIteration:
            if not completed_token:
                raise TokenizerError(f"unexpected end of file")
            yield EOF


def tokenize(text: str, strict=True) -> Iterator[Token]:
    yield from Tokenizer(text, strict)
