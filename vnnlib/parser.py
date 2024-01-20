from __future__ import annotations

import bz2
import gzip
import lzma
import warnings
from pathlib import Path
from typing import Callable, Dict, Iterator, List, Optional, TextIO, Union

from .errors import ParserError
from .tokenizer import DUMMY_TOKEN, EOF, Token, tokenize

Real = float


class AstNode:
    pass


class Script(AstNode):
    __slots__ = ("commands",)

    def __init__(self, *commands: Command):
        self.commands = commands


class Command(AstNode):
    pass


class Declare(Command):
    pass


class DeclareConst(Declare):
    __slots__ = "symbol", "sort"

    def __init__(self, symbol: str, sort: str):
        self.symbol = symbol
        self.sort = sort


class Assert(Command):
    __slots__ = ("term",)

    def __init__(self, term: Term):
        self.term = term


class Term(AstNode):
    pass


class FunctionApplication(Term):
    __slots__ = "function", "terms"

    def __init__(self, function: Identifier, *terms: Term):
        self.function = function
        self.terms = terms


class Constant(Term):
    __slots__ = ("value",)

    def __init__(self, value: float | int | str | Real):
        self.value = value


class Sort(AstNode):
    __slots__ = ("value",)

    def __init__(self, value: str):
        self.value = value


class Identifier(Term):
    __slots__ = ("value",)

    def __init__(self, value: str, sort: Sort):
        self.value = value


def _hex_to_int(x: str) -> int:
    return int(x[2:], 16)


def _bin_to_int(x: str) -> int:
    return int(x[2:], 2)


def _string_to_str(x: str) -> str:
    return x[1:-1].replace('""', '"')


LITERAL_CONVERTERS: Dict[str, Callable[[str], float | int | str | Real]] = {
    "DECIMAL": Real,
    "NUMERAL": int,
    "HEXADECIMAL": _hex_to_int,
    "BINARY": _bin_to_int,
    "STRING": _string_to_str,
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
        self.curr_token = DUMMY_TOKEN
        self.sorts = {"Bool": Sort("Bool"), "Int": Sort("Int"), "Real": Sort("Real")}
        self.identifiers: Dict[str, Identifier] = CORE_IDS.copy()

    def advance_token_stream(self) -> Token:
        self.curr_token = next(self.token_stream)
        return self.curr_token

    def ensure_token_type(
        self,
        token: Token,
        expected_token_type: str,
        *,
        expected_value: Optional[str] = None,
        msg: str = "Unexpected token: {token_type}({value!r})",
    ) -> bool:
        if token[0] == expected_token_type:
            return True
        if expected_value:
            raise ParserError(
                f"Unexpected token: {token[1]!r}" f", expected {expected_value!r}"
            )
        raise ParserError(msg.format(token_type=token[0], value=token[1]))

    def lookup_identifier(self, identifier: str) -> Identifier:
        if identifier not in self.identifiers:
            if (
                identifier.startswith("e")
                and len(identifier) >= 2
                and not set(identifier[1:]).difference(set("0123456789+-"))
            ):
                raise ParserError(
                    (
                        f"Undeclared identifier: {identifier!r}."
                        "\n\tIt looks like this may be exponential notation, which is not SMT-LIB compliant."
                        "\n\tTry turning of strict mode."
                    )
                )
            raise ParserError(f"Undeclared identifier: {identifier!r}")
        return self.identifiers[identifier]

    def lookup_sort(self, name: str) -> Sort:
        if name not in self.sorts:
            raise ParserError(f"Undeclared sort: {name!r}")
        return self.sorts[name]

    @classmethod
    def parse(cls, text: str, strict=True) -> Script:
        parser = VnnLibParser(tokenize(text, strict=strict))
        parser.advance_token_stream()
        commands = []
        while parser.curr_token != EOF:
            command = parser.parse_command()
            commands.append(command)
        return Script(*commands)

    def parse_command(self) -> Command:
        self.ensure_token_type(self.curr_token, "LPAREN", expected_value="(")
        curr_token = self.advance_token_stream()
        command = curr_token[1]
        if command == "assert":
            node: Command = self.parse_assert()
        elif command == "declare-const":
            node = self.parse_declare_const()
        else:
            raise ParserError(f"Unknown command: {command!r}")
        self.ensure_token_type(self.curr_token, "RPAREN", expected_value=")")
        self.advance_token_stream()
        return node

    def parse_declare_const(self) -> Declare:
        symbol = self.advance_token_stream()
        self.ensure_token_type(symbol, "SYMBOL")
        sort = self.advance_token_stream()
        self.ensure_token_type(sort, "SYMBOL")
        self.advance_token_stream()
        self.identifiers[symbol[1]] = Identifier(symbol[1], self.lookup_sort(sort[1]))
        return DeclareConst(symbol[1], sort[1])

    def parse_assert(self) -> Assert:
        self.advance_token_stream()
        return Assert(self.parse_term())

    def parse_term(self) -> Term:
        curr_token = self.curr_token
        token_type = curr_token[0]
        if token_type == "SYMBOL":
            self.advance_token_stream()
            try:
                return self.lookup_identifier(curr_token[1])
            except ParserError:
                if curr_token[1].startswith("-"):
                    warnings.warn("literal negation does not strictly follow SMT-LIB")
                    try:
                        float_value = Real(curr_token[1])
                        return Constant(float_value)
                    except ValueError:
                        return FunctionApplication(
                            self.lookup_identifier("-"),
                            self.lookup_identifier(curr_token[1][1:]),
                        )
                raise
        if token_type == "LPAREN":
            children: List[Term] = []
            function_id_token = self.advance_token_stream()
            self.ensure_token_type(function_id_token, "SYMBOL")
            self.advance_token_stream()
            while self.curr_token[0] != "RPAREN":
                child = self.parse_term()
                children.append(child)
            self.advance_token_stream()
            function = self.lookup_identifier(function_id_token[1])
            return FunctionApplication(function, *children)
        if token_type in LITERAL_CONVERTERS:
            value = LITERAL_CONVERTERS[token_type](curr_token[1])
            self.advance_token_stream()
            return Constant(value)
        raise ParserError(f"Unexpected token: {curr_token}")


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
