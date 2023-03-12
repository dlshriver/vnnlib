from __future__ import annotations

import bz2
import gzip
import lzma
import re
import warnings
from pathlib import Path
from typing import (
    Callable,
    Dict,
    Iterator,
    List,
    NamedTuple,
    Optional,
    Set,
    TextIO,
    Union,
)

from .errors import ParserError

Real = float


class Meta(NamedTuple):
    start_pos: int
    end_pos: int


class Token(NamedTuple):
    token_type: str
    value: str
    meta: Meta


def as_dict(t: NamedTuple):
    return t._asdict()


_DUMMY_TOKEN = Token("_", "", Meta(0, 0))
EOF = Token("EOF", "", Meta(-1, -1))


def tokenize(text: str, skip: Set[str], strict=True) -> Iterator[Token]:
    if len(text) == 0:
        return
    tokens: Dict[str, str] = {
        "COMMENT": r";[\t -~]*(?:[\r\n]|$)",
        "WS": r"\x09|\x0a|\x0d|\x20",
        "LPAREN": r"\(",
        "RPAREN": r"\)",
        "BINARY": r"#b[01]+",
        "HEXADECIMAL": r"#x[0-9A-Fa-f]+",
        "_DECIMAL_strict": r"(?:{NUMERAL})\.0*(?:{NUMERAL})",
        "_DECIMAL_extended": r"(?:(?:{NUMERAL})\.0*(?:{NUMERAL})(?:[eE][+-]?0*(?:{NUMERAL}))?)",
        "DECIMAL": f"(?:{{_DECIMAL_{'strict' if strict else 'extended'}}})",
        "NUMERAL": r"(?:(?:[1-9][0-9]*)|0)",
        "STRING": r"\x22(?:(?:{WS})|(?:{_PRINTABLE_CHAR}))*\x22",
        "SYMBOL": r"(?:(?:(?:{_LETTER})|(?:{_CHARACTER}))(?:[0-9]|(?:{_LETTER})|(?:{_CHARACTER}))*)|(?:\x7c(?:[\x20-\x5b]|[\x5d-\x7b]|[\x7d\x7e]|[\x80-\xff])*\x7c)",
        "_PRINTABLE_CHAR": r"[\x20-\x7e]|[\x80-\xff]",
        "_LETTER": r"[A-Za-z]",
        "_CHARACTER": r"[~!@$%^&*+=<>.?/_-]",
    }
    for key, value in tokens.items():
        tokens[key] = value.format(**tokens)
    token_pattern = re.compile(
        "|".join(
            f"(?P<{token_type}>{pattern})"
            for token_type, pattern in tokens.items()
            if not token_type.startswith("_")
        )
    )
    pos: int = 0
    for match in token_pattern.finditer(text):
        start_pos, end_pos = match.span()
        if start_pos != pos:
            raise ParserError(f"Unknown string: {text[pos:start_pos]!r}")
        assert match.lastgroup is not None
        if match.lastgroup not in skip:
            yield Token(match.lastgroup, match.group(), Meta(start_pos, end_pos))
        pos = end_pos
    if pos != len(text):
        raise ParserError(f"Unknown string: {text[pos:]!r}")


class AstNode:
    @property
    def _type(self) -> str:
        return self.__class__.__name__


class Script(AstNode):
    def __init__(self, *commands: Command):
        self.commands = commands


class Command(AstNode):
    pass


class Declare(Command):
    pass


class DeclareConst(Declare):
    def __init__(self, symbol: str, sort: str):
        self.symbol = symbol
        self.sort = sort


class Assert(Command):
    def __init__(self, term: Term):
        self.term = term


class Term(AstNode):
    pass


class FunctionApplication(Term):
    def __init__(self, function: Identifier, *terms: Term):
        self.function = function
        self.terms = terms


class Constant(Term):
    def __init__(self, value: float | int | str | Real):
        self.value = value


class Sort(AstNode):
    def __init__(self, value: str):
        self.value = value


class Identifier(Term):
    def __init__(self, value: str, sort: Sort):
        self.value = value


def _hex_to_int(x: str) -> int:
    return int(x[2:], 16)


def _bin_to_int(x: str) -> int:
    return int(x[2:], 2)


def _identity(x: str) -> str:
    return x


LITERAL_CONVERTERS: Dict[str, Callable[[str], float | int | str | Real]] = {
    "DECIMAL": Real,
    "NUMERAL": int,
    "HEXADECIMAL": _hex_to_int,
    "BINARY": _bin_to_int,
    "STRING": _identity,
}
CORE_IDS: Dict[str, Identifier] = {
    # arithmetic
    "+": Identifier("+", Sort("(A A) A")),
    "-": Identifier("-", Sort("(A A) A")),
    "*": Identifier("*", Sort("(A A) A")),
    "/": Identifier("/", Sort("(A A) A")),
    # comparisons
    ">": Identifier(">", Sort("(A A) Bool")),
    ">=": Identifier(">=", Sort("(A A) Bool")),
    "<": Identifier("<", Sort("(A A) Bool")),
    "<=": Identifier("<=", Sort("(A A) Bool")),
    "=": Identifier("=", Sort("(A A) Bool")),
    # logic
    "true": Identifier("true", Sort("Bool")),
    "false": Identifier("false", Sort("Bool")),
    "not": Identifier("not", Sort("(Bool Bool)")),
    "=>": Identifier("=>", Sort("(Bool Bool) Bool")),
    "or": Identifier("or", Sort("(Bool Bool) Bool")),
    "and": Identifier("and", Sort("(Bool Bool) Bool")),
    "xor": Identifier("xor", Sort("(Bool Bool) Bool")),
    "ite": Identifier("ite", Sort("(Bool A A) A")),
}


class VnnLibParser:
    def __init__(self, token_stream: Iterator[Token]):
        self.token_stream = token_stream
        self.curr_token = _DUMMY_TOKEN
        self.sorts = {"Bool": Sort("Bool"), "Int": Sort("Int"), "Real": Sort("Real")}
        self.identifiers: Dict[str, Identifier] = CORE_IDS.copy()

    def advance_token_stream(self) -> Token:
        self.curr_token = next_token = next(self.token_stream, EOF)
        return next_token

    def expect_token_type(
        self,
        type: str,
        *,
        expected_value: Optional[str] = None,
        msg: str = "unexpected token: {token_type}({value!r})",
    ) -> bool:
        if self.curr_token.token_type == type:
            return True
        if expected_value:
            raise ParserError(f"Expected {expected_value!r}")
        raise ParserError(msg.format(**as_dict(self.curr_token)))

    def lookup_identifier(self, identifier: str) -> Identifier:
        if identifier not in self.identifiers:
            if (
                identifier.startswith("e")
                and len(identifier) >= 2
                and not set(identifier[1:]).difference(set("0123456789+-"))
            ):
                raise ParserError(
                    (
                        f"undeclared identifier: {identifier!r}."
                        "\n\tIt looks like this may be exponential notation, which is not SMT-LIB compliant."
                        "\n\tTry turning of strict mode."
                    )
                )
            raise ParserError(f"undeclared identifier: {identifier!r}")
        return self.identifiers[identifier]

    def lookup_sort(self, name: str) -> Sort:
        if name not in self.sorts:
            raise ParserError(f"undeclared sort: {name!r}")
        return self.sorts[name]

    @classmethod
    def parse(cls, text: str, strict=True) -> Script:
        parser = VnnLibParser(tokenize(text, {"WS", "COMMENT"}, strict=strict))
        parser.advance_token_stream()
        commands = []
        while parser.curr_token != EOF:
            commands.append(parser.parse_command())
        return Script(*commands)

    def parse_command(self) -> Command:
        self.expect_token_type(type="LPAREN", expected_value="(")
        curr_token = self.advance_token_stream()
        command = curr_token.value
        command_parsers = {
            "assert": self.parse_assert,
            "declare-const": self.parse_declare_const,
        }
        if command not in command_parsers:
            raise ParserError(f"Unknown command: {command!r}")
        node = command_parsers[command]()
        self.expect_token_type(type="RPAREN", expected_value=")")
        self.advance_token_stream()
        return node

    def parse_declare_const(self) -> Declare:
        symbol = self.advance_token_stream()
        self.expect_token_type("SYMBOL")
        sort = self.advance_token_stream()
        self.expect_token_type("SYMBOL")
        self.advance_token_stream()
        self.identifiers[symbol.value] = Identifier(
            symbol.value, self.lookup_sort(sort.value)
        )
        return DeclareConst(symbol.value, sort.value)

    def parse_assert(self) -> Assert:
        self.advance_token_stream()
        return Assert(self.parse_term())

    def parse_term(self) -> Term:
        curr_token = self.curr_token
        token_type = curr_token.token_type
        if token_type == "SYMBOL":
            self.advance_token_stream()
            if curr_token.value.startswith("-"):
                warnings.warn("literal negation does not strictly follow SMT-LIB")
                try:
                    float_value = Real(curr_token.value)
                    return Constant(float_value)
                except:
                    pass
                return FunctionApplication(
                    self.lookup_identifier("-"),
                    self.lookup_identifier(curr_token.value[1:]),
                )
            return self.lookup_identifier(curr_token.value)
        if token_type == "LPAREN":
            children: List[Term] = []
            function_id_token = self.advance_token_stream()
            self.expect_token_type("SYMBOL")
            self.advance_token_stream()
            children.append(self.parse_term())
            while self.curr_token.token_type != "RPAREN":
                children.append(self.parse_term())
            self.advance_token_stream()
            return FunctionApplication(
                self.lookup_identifier(function_id_token.value), *children
            )
        if token_type in LITERAL_CONVERTERS:
            value = LITERAL_CONVERTERS[token_type](curr_token.value)
            self.advance_token_stream()
            return Constant(value)
        raise ParserError(f"Unexpected token: {curr_token}")


def _identity_args(*args):
    return args


class _Discard:
    pass


Discard = _Discard()


class AstNodeTransformer:
    def transform(self, node: AstNode):
        args = getattr(self, f"_visit_{node._type}")(node)
        return getattr(self, f"transform_{node._type}", _identity_args)(*args)

    def _visit_Assert(self, node: Assert):
        result = self.transform(node.term)
        return (result,)

    def _visit_Constant(self, node: Constant):
        return (node.value,)

    def _visit_DeclareConst(self, node: DeclareConst):
        return (node.symbol, node.sort)

    def _visit_FunctionApplication(self, node: FunctionApplication):
        function = self.transform(node.function)
        terms = [self.transform(term) for term in node.terms]
        return (function, *terms)

    def _visit_Identifier(self, node: Identifier):
        return (node.value,)

    def _visit_Script(self, node: Script):
        results = []
        for command in node.commands:
            result = self.transform(command)
            if result is not Discard:
                results.append(result)
        return results


def parse_file(filename: Union[str, Path], strict=True) -> AstNode:
    if isinstance(filename, str):
        filename = Path(filename)
    open_func: Callable[[Union[str, Path]], TextIO]
    if filename.suffix in {".gz", ".gzip"}:
        open_func = lambda fname: gzip.open(fname, "rt")
    elif filename.suffix in {".bz2", ".bzip2"}:
        open_func = lambda fname: bz2.open(fname, "rt")
    elif filename.suffix == ".xz":
        open_func = lambda fname: lzma.open(fname, "rt")
    else:
        open_func = open

    with open_func(filename) as f:
        text = f.read()
    ast_node = VnnLibParser.parse(text, strict=strict)
    return ast_node


__all__ = ["VnnLibParser", "parse_file"]
