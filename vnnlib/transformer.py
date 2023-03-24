from __future__ import annotations

from typing import Set, Type, TypeVar

from .parser import (
    Assert,
    AstNode,
    Constant,
    DeclareConst,
    FunctionApplication,
    Identifier,
    Script,
)


class _Discard:
    pass


Discard = _Discard()

T = TypeVar("T")


def get_subclasses(cls: Type[T]) -> Set[Type[T]]:
    c = list(cls.__subclasses__())
    for sub in c:
        c.extend(get_subclasses(sub))
    return set(c)


class AstNodeTransformer:
    def __init__(self) -> None:
        self._visitor_table = {
            node_class: getattr(self, f"_visit_{node_class.__name__}")
            for node_class in get_subclasses(AstNode)
            if hasattr(self, f"_visit_{node_class.__name__}")
        }
        self._transform_table = {
            node_class: getattr(self, f"transform_{node_class.__name__}")
            for node_class in get_subclasses(AstNode)
            if hasattr(self, f"transform_{node_class.__name__}")
        }

    def transform(self, node: AstNode):
        args = self._visitor_table[node.__class__](node)
        if node.__class__ in self._transform_table:
            return self._transform_table[node.__class__](*args)
        return args

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


__all__ = ["AstNodeTransformer"]
