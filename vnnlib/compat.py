from __future__ import annotations

import operator
import pathlib
from typing import Dict, List, Optional, Tuple, Union

import numpy as np

from .parser import AstNodeTransformer, Real, parse_file


class CompatTransformer(AstNodeTransformer):
    def __init__(
        self,
        input_name: str,
        output_name: str,
        input_size: Optional[int] = None,
        output_size: Optional[int] = None,
    ) -> None:
        self.input_name = input_name
        self.output_name = output_name

        self.input_size = input_size or 0
        self.output_size = output_size or 0

        self.infer_input_size = input_size is None
        self.infer_output_size = output_size is None

        self._id_map: Dict[str, int] = {}
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
                if len(term[0]):
                    self._num_assertions += max_row + 1
            elif len(self._disjunctions) == 1:
                new_disjunctions = []
                for disjunct in term:
                    disjunct = disjunct.copy()
                    new_disjunctions.append(disjunct)
                    row_offset = max(disjunct, default=(-1,))[0] + 1
                    for (row, *index), value in self._disjunctions[0].items():
                        disjunct[(row + row_offset, *index)] = value
                self._disjunctions = new_disjunctions
            else:
                assert False
            return term
        if isinstance(term, dict):
            row_offset = self._num_assertions
            max_row = 0
            for (row, *index), value in term.items():
                self._assertions[(row + row_offset, *index)] = value
                max_row = max(max_row, row)
            if len(term):
                self._num_assertions += max_row + 1
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
        if value.startswith(f"{self.input_name}_"):
            _, *str_index = value.split("_")
            return {(0, 0, *tuple(map(int, str_index))): 1}
        elif value.startswith(f"{self.output_name}_"):
            _, *str_index = value.split("_")
            return {(0, 1, *tuple(map(int, str_index))): 1}
        elif value in {"<=", ">=", "and", "or"}:
            return value
        if value not in self._id_map:
            self._id_map[value] = len(self._id_map) + 2
        return {(0, self._id_map[value]): 1}

    def transform_Script(self, *commands):
        common_box = [[float("-inf"), float("inf")] for _ in range(self.input_size)]
        common_polytope = []
        input_box_rows = set()
        output_polytope_rows = set()
        rhs = 0
        for (row, var_type, index), value in sorted(
            self._assertions.items(), key=operator.itemgetter(0)
        ):
            assert var_type <= 0 or row not in input_box_rows
            if var_type == -1:
                rhs = value
                continue
            if var_type == 0:
                input_box_rows.add(row)
                if value == 1:
                    common_box[index][1] = min(-rhs, common_box[index][1])
                elif value == -1:
                    common_box[index][0] = max(rhs, common_box[index][0])
                else:
                    raise RuntimeError(f"unexpected lhs coeff for box: {value}")
                rhs = 0
                continue
            if var_type == 1:
                output_polytope_rows.add(row)
                polytope_row = row - min(output_polytope_rows)
                if len(common_polytope) <= polytope_row:
                    common_polytope.append(
                        [[0 for _ in range(self.output_size)], [rhs]]
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
            output_polytope_rows = set()
            rhs = 0
            for (row, var_type, index), value in sorted(
                disjunct.items(), key=lambda kv: kv[0]
            ):
                assert var_type <= 0 or row not in input_box_rows
                if var_type == -1:
                    rhs = value
                    continue
                if var_type == 0:
                    input_box_rows.add(row)
                    if value == 1:
                        box[index][1] = min(-rhs, box[index][1])
                    elif value == -1:
                        box[index][0] = max(rhs, box[index][0])
                    else:
                        raise RuntimeError(f"unexpected lhs coeff for box: {value}")
                    rhs = 0
                    continue
                if var_type == 1:
                    output_polytope_rows.add(row)
                    polytope_row = (
                        row - min(output_polytope_rows) + len(common_polytope)
                    )
                    if len(polytope) <= polytope_row:
                        polytope.append([[0 for _ in range(self.output_size)], [rhs]])
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
        return list(results.values())


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
