from __future__ import annotations

import re
from typing import Dict, Final, Iterator, Set

from .errors import ParserError


class Meta:
    def __init__(self, start_pos: int, end_pos: int):
        start_pos = start_pos
        end_pos = end_pos


class Token:
    def __init__(self, token_type: str, value: str, meta: Meta):
        self.token_type = token_type
        self.value = value
        self.meta = meta


DUMMY_TOKEN: Final[Token] = Token("_", "", Meta(0, 0))
EOF: Final[Token] = Token("EOF", "", Meta(-1, -1))


def tokenize(text: str, skip: Set[str], strict=True) -> Iterator[Token]:
    if len(text) == 0:
        return
    _token_patterns: Dict[str, str] = {
        "COMMENT": r";[\t -~]*(?:[\r\n]|$)",
        "WS": r"\x09|\x0a|\x0d|\x20",
        "LPAREN": r"\(",
        "RPAREN": r"\)",
        "BINARY": r"#b[01]+",
        "HEXADECIMAL": r"#x[0-9A-Fa-f]+",
        "_DECIMAL_strict": r"(?:{NUMERAL})\.0*(?:{NUMERAL})",
        "_DECIMAL_extended": r"(?:(?:{NUMERAL})\.[0-9]+(?:[eE][+-]?[0-9]+)?)|(?:(?:{NUMERAL})[eE][+-]?[0-9]+)",
        "DECIMAL": f"(?:{{_DECIMAL_{'strict' if strict else 'extended'}}})",
        "NUMERAL": r"(?:(?:[1-9][0-9]*)|0)",
        "STRING": r"\x22(?:(?:{WS})|(?:{_PRINTABLE_CHAR}))*\x22",
        "SYMBOL": r"(?:(?:(?:{_LETTER})|(?:{_CHARACTER}))(?:[0-9]|(?:{_LETTER})|(?:{_CHARACTER}))*)|(?:\x7c(?:[\x20-\x5b]|[\x5d-\x7b]|[\x7d\x7e]|[\x80-\xff])*\x7c)",
        "_PRINTABLE_CHAR": r"[\x20-\x7e]|[\x80-\xff]",
        "_LETTER": r"[A-Za-z]",
        "_CHARACTER": r"[~!@$%^&*+=<>.?/_-]",
    }
    for key, value in _token_patterns.items():
        _token_patterns[key] = value.format(**_token_patterns)
    token_pattern = re.compile(
        "|".join(
            f"(?P<{token_type}>{pattern})"
            for token_type, pattern in _token_patterns.items()
            if not token_type.startswith("_")
        )
    )
    pos: int = 0
    for match in token_pattern.finditer(text):
        start_pos, end_pos = match.span()
        token_type = match.lastgroup
        if token_type in skip:
            pos = end_pos
            continue
        if start_pos != pos:
            raise ParserError(f"Unknown string: {text[pos:start_pos]!r}")
        assert token_type is not None
        yield Token(token_type, match.group(), Meta(start_pos, end_pos))
        pos = end_pos
    if pos != len(text):
        raise ParserError(f"Unknown string: {text[pos:]!r}")
