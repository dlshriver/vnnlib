from __future__ import annotations

import operator
import pathlib
import re
from typing import Dict, List, Optional, Tuple, Union

import numpy as np

from .parser import Real, parse_file
from .transformer import AstNodeTransformer


class CompatTransformer(AstNodeTransformer):
    def __init__(
        self,
        input_name: str,
        output_name: str,
        input_size: Optional[int] = None,
        output_size: Optional[int] = None,
    ) -> None:
        super().__init__()
        self.input_name = input_name
        self.output_name = output_name

        self.input_size = input_size or 0
        self.output_size = output_size or 0

        self.infer_input_size = input_size is None
        self.infer_output_size = output_size is None

        self._io_name_pattern = re.compile(f"{self.input_name}|{self.output_name}")
        self._id_map: Dict[str, int] = {self.input_name: 0, self.output_name: 1}
        self._id_cache: Dict[str, Dict[Tuple[int, ...], Real]] = {}
        self._assertions: Dict[Tuple[int, ...], Real] = {}
        self._num_assertions = 0
        self._disjunctions: List[Dict[Tuple[int, ...], Real]] = [{}]

    def transform_Assert(
        self,
        term: Union[List[Dict[Tuple[int, ...], Real]], Dict[Tuple[int, ...], Real]],
    ) -> List[Dict[Tuple[int, ...], Real]]:
        if isinstance(term, list):
            if len(term) == 1:
                row_offset = self._num_assertions
                max_row = 0
                for (row, *index), value in term[0].items():
                    self._assertions[(row + row_offset, *index)] = value
                    max_row = max(max_row, row)
                self._num_assertions += max_row + (1 if len(term[0]) else 0)
            elif len(self._disjunctions) == 1:
                assert len(self._disjunctions[0]) == 0, "please open a bug report"
                new_disjunctions = []
                for disjunct in term:
                    new_disjunct = disjunct.copy()
                    new_disjunctions.append(new_disjunct)
                self._disjunctions = new_disjunctions
            else:
                new_disjunctions = []
                for disjunct in term:
                    row_offset = max(disjunct, default=(-1,))[0] + 1
                    for _disjunct in self._disjunctions:
                        new_disjunct = disjunct.copy()
                        new_disjunctions.append(new_disjunct)
                        for (row, *index), value in _disjunct.items():
                            new_disjunct[(row + row_offset, *index)] = value
                self._disjunctions = new_disjunctions
            return term
        if isinstance(term, dict):
            row_offset = self._num_assertions
            max_row = 0
            for (row, *index), value in term.items():
                self._assertions[(row + row_offset, *index)] = value
                max_row = max(max_row, row)
            self._num_assertions += max_row + (1 if len(term) else 0)
            return [term]
        raise RuntimeError("unexpected term for assert")

    def transform_Constant(self, value) -> Dict[Tuple[int, ...], Real]:
        assert isinstance(value, (Real, int))
        return {(0, -1, -1): value}

    def transform_DeclareConst(self, symbol: str, sort: str) -> None:
        if self.infer_input_size and symbol.startswith(f"{self.input_name}_"):
            _, index = symbol.split("_")
            self.input_size = max(self.input_size, int(index) + 1)
        elif self.infer_output_size and symbol.startswith(f"{self.output_name}_"):
            _, index = symbol.split("_")
            self.output_size = max(self.output_size, int(index) + 1)
        self._id_map[symbol] = len(self._id_map)

    def transform_FunctionApplication(
        self,
        symbol: str,
        *terms: Union[List[Dict[Tuple[int, ...], Real]], Dict[Tuple[int, ...], Real]],
    ) -> Union[List[Dict[Tuple[int, ...], Real]], Dict[Tuple[int, ...], Real]]:
        if symbol == "<=":
            lhs, rhs = terms
            assert isinstance(lhs, dict)
            assert isinstance(rhs, dict)
            result = lhs.copy()
            for key, value in rhs.items():
                result[key] = result.get(key, 0) - value
            return result
        elif symbol == ">=":
            lhs, rhs = terms
            assert isinstance(lhs, dict)
            assert isinstance(rhs, dict)
            result = rhs.copy()
            for key, value in lhs.items():
                result[key] = result.get(key, 0) - value
            return result
        elif symbol == "+":
            result = {}
            for term in terms:
                assert isinstance(term, dict)
                for key, value in term.items():
                    result[key] = result.get(key, 0) + value
            return result
        elif symbol == "-":
            assert isinstance(terms[0], dict)
            if len(terms) == 1:
                return {key: -value for key, value in terms[0].items()}
            else:
                result = terms[0].copy()
                for term in terms[1:]:
                    assert isinstance(term, dict)
                    for key, value in term.items():
                        result[key] = result.get(key, 0) - value
            return result
        elif symbol == "*":
            sorted_terms = tuple(
                sorted(
                    terms,
                    key=lambda term: -sum(
                        map(lambda x: x >= 0, map(operator.itemgetter(1), term))
                    ),
                )
            )
            assert isinstance(sorted_terms[0], dict)
            result = sorted_terms[0].copy()
            for term in sorted_terms[1:]:
                assert isinstance(term, dict)
                if len(term) > 1 or (0, -1, -1) not in term:
                    raise NotImplementedError(
                        "Nonlinear constraints are not supported by the legacy parser"
                    )
                const = term[(0, -1, -1)]
                for key, value in result.items():
                    result[key] = value * const
            return result
        elif symbol == "and":
            conjuncts = {}
            for i, term in enumerate(terms):
                assert isinstance(term, dict)
                for (row, *index), value in term.items():
                    assert row == 0
                    assert len(index) == 2, "please open a bug report"
                    conjuncts[(i, *index)] = value
            return [conjuncts]
        elif symbol == "or":
            or_result = []
            for term in terms:
                if isinstance(term, dict):
                    term = [term]
                assert isinstance(term, list), "please open a bug report"
                for subterm in term:
                    assert isinstance(subterm, dict), "please open a bug report"
                or_result.extend(term)
            return or_result
        else:
            raise NotImplementedError(
                f"Function {symbol!r} is not supported by the legacy parser"
            )

    def transform_Identifier(
        self, value: str
    ) -> Union[str, Dict[Tuple[int, ...], Real]]:
        if value not in self._id_map:
            return value
        if value not in self._id_cache:
            if self._io_name_pattern.match(value):
                name, *str_index = value.split("_")
                self._id_cache[value] = {
                    (0, self._id_map[name], *map(int, str_index)): 1
                }
            else:
                self._id_cache[value] = {(0, self._id_map[value], 0): 1}
        return self._id_cache[value]

    def transform_Script(
        self, *commands
    ) -> List[Tuple[List[Real], Tuple[np.ndarray, np.ndarray]]]:
        common_box = [[float("-inf"), float("inf")] for _ in range(self.input_size)]
        common_polytope = []
        input_box_rows = set()
        output_polytope_rows = set()
        rhs = 0
        for (row, var_type, index), value in sorted(
            self._assertions.items(), key=operator.itemgetter(0)
        ):
            assert var_type != 1 or row not in input_box_rows
            if var_type == -1:
                rhs = value
                continue
            if var_type == 0:
                input_box_rows.add(row)
                if value > 0:
                    common_box[index][1] = min(-rhs / value, common_box[index][1])
                elif value < 0:
                    common_box[index][0] = max(-rhs / value, common_box[index][0])
                rhs = 0
                continue
            if var_type == 1:
                output_polytope_rows.add(row)
                polytope_row = row - min(output_polytope_rows)
                if len(common_polytope) <= polytope_row:
                    common_polytope.append(
                        [[0 for _ in range(self.output_size)], [-rhs]]
                    )
                    rhs = 0
                common_polytope[polytope_row][0][index] = value
                continue
            raise RuntimeError(f"unexpected variable type {var_type}")
        results = {}
        for disjunct in self._disjunctions:
            box = [interval.copy() for interval in common_box]
            polytope = [[lhs.copy(), rhs.copy()] for lhs, rhs in common_polytope]
            input_box_rows = set()
            output_polytope_rows = {}
            rhs = 0
            for (row, var_type, index), value in sorted(
                disjunct.items(), key=operator.itemgetter(0)
            ):
                assert var_type != 1 or row not in input_box_rows
                if var_type == -1:
                    rhs = value
                    continue
                if var_type == 0:
                    input_box_rows.add(row)
                    if value > 0:
                        box[index][1] = min(-rhs / value, box[index][1])
                    elif value < 0:
                        box[index][0] = max(-rhs / value, box[index][0])
                    rhs = 0
                    continue
                if var_type == 1:
                    if row not in output_polytope_rows:
                        output_polytope_rows[row] = len(output_polytope_rows)
                    polytope_row = output_polytope_rows[row]
                    if len(polytope) <= polytope_row:
                        polytope.append([[0 for _ in range(self.output_size)], [-rhs]])
                        rhs = 0
                    polytope[polytope_row][0][index] = value
                    continue
                raise RuntimeError(f"unexpected variable type {var_type}")
            box_str = str(box)
            polytope_arr = (
                np.array([lhs for lhs, _ in polytope]),
                np.array([rhs for _, rhs in polytope]),
            )
            if box_str not in results:
                results[box_str] = [box, [polytope_arr]]
            else:
                results[box_str][1].append(polytope_arr)
        return list(map(tuple, results.values()))


def read_vnnlib_simple(
    vnnlib_filename: Union[str, pathlib.Path], num_inputs: int, num_outputs: int
) -> List[Tuple[List[Real], Tuple[np.ndarray, np.ndarray]]]:
    """process in a vnnlib file. You can get num_inputs and num_outputs using get_num_inputs_outputs().

    output a list containing 2-tuples:
        1. input ranges (box), list of pairs for each input variable
        2. specification, provided as a list of pairs (mat, rhs), as in: mat * y <= rhs, where y is the output.
                          Each element in the list is a term in a disjunction for the specification.
    """
    ast_node = parse_file(vnnlib_filename, strict=False)
    result = CompatTransformer("X", "Y", num_inputs, num_outputs).transform(ast_node)
    return result


__all__ = [
    "read_vnnlib_simple",
]
