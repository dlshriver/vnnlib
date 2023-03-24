import pytest

from vnnlib.compat import CompatTransformer, read_vnnlib_simple
from vnnlib.parser import parse_file


def test_infer_shapes(tmp_path):
    vnnlib_path = tmp_path / "test.vnnlib"
    with open(vnnlib_path, "w+") as f:
        f.write(
            "(declare-const X_0 Real)\n"
            "(declare-const Y_0 Real)\n"
            "(assert (>= X_0 0))\n"
            "(assert (<= X_0 1))\n"
            "(assert (>= Y_0 0))\n"
        )

    result = CompatTransformer("X", "Y").transform(parse_file(vnnlib_path))
    assert len(result) == 1
    assert len(result[0]) == 2
    assert len(result[0][0]) == 1
    assert result[0][0][0] == [0, 1]
    assert len(result[0][1]) == 1
    assert len(result[0][1][0]) == 2
    assert result[0][1][0][0] == -1
    assert result[0][1][0][1] == 0


def test_box_box(tmp_path):
    vnnlib_path = tmp_path / "test.vnnlib"
    with open(vnnlib_path, "w+") as f:
        f.write(
            "(declare-const X_0 Real)\n"
            "(declare-const Y_0 Real)\n"
            "(assert (>= X_0 0))\n"
            "(assert (<= X_0 1))\n"
            "(assert (>= Y_0 0))\n"
        )

    result = read_vnnlib_simple(vnnlib_path, 1, 1)
    assert len(result) == 1
    assert len(result[0]) == 2
    assert len(result[0][0]) == 1
    assert result[0][0][0] == [0, 1]
    assert len(result[0][1]) == 1
    assert len(result[0][1][0]) == 2
    assert result[0][1][0][0] == -1
    assert result[0][1][0][1] == 0


def test_box_box_negation(tmp_path):
    vnnlib_path = tmp_path / "test.vnnlib"
    with open(vnnlib_path, "w+") as f:
        f.write(
            "(declare-const X_0 Real)\n"
            "(declare-const Y_0 Real)\n"
            "(assert (>= X_0 -1))\n"
            "(assert (<= X_0 1))\n"
            "(assert (>= Y_0 0))\n"
        )

    result = read_vnnlib_simple(vnnlib_path, 1, 1)
    assert len(result) == 1
    assert len(result[0]) == 2
    assert len(result[0][0]) == 1
    assert result[0][0][0] == [-1, 1]
    assert len(result[0][1]) == 1
    assert len(result[0][1][0]) == 2
    assert result[0][1][0][0] == -1
    assert result[0][1][0][1] == 0


def test_box_box_exponential_notation(tmp_path):
    vnnlib_path = tmp_path / "test.vnnlib"
    with open(vnnlib_path, "w+") as f:
        f.write(
            "(declare-const X_0 Real)\n"
            "(declare-const Y_0 Real)\n"
            "(assert (>= X_0 -1e0))\n"
            "(assert (<= X_0 1e0))\n"
            "(assert (>= Y_0 0.5))\n"
        )

    result = read_vnnlib_simple(vnnlib_path, 1, 1)
    assert len(result) == 1
    assert len(result[0]) == 2
    assert len(result[0][0]) == 1
    assert result[0][0][0] == [-1, 1]
    assert len(result[0][1]) == 1
    assert len(result[0][1][0]) == 2
    assert result[0][1][0][0] == -1
    assert result[0][1][0][1] == -0.5


def test_box_poly(tmp_path):
    vnnlib_path = tmp_path / "test.vnnlib"
    with open(vnnlib_path, "w+") as f:
        f.write(
            "(declare-const X_0 Real)\n"
            "(declare-const Y_0 Real)\n"
            "(declare-const Y_1 Real)\n"
            "(assert (>= X_0 0))\n"
            "(assert (<= X_0 1))\n"
            "(assert (>= Y_0 Y_1))\n"
        )

    result = read_vnnlib_simple(vnnlib_path, 1, 2)
    assert len(result) == 1
    assert len(result[0]) == 2
    assert len(result[0][0]) == 1
    assert result[0][0][0] == [0, 1]
    assert len(result[0][1]) == 1
    assert len(result[0][1][0]) == 2
    assert all(result[0][1][0][0][0] == [-1, 1])
    assert all(result[0][1][0][1] == 0)


def test_box_poly_and(tmp_path):
    vnnlib_path = tmp_path / "test.vnnlib"
    with open(vnnlib_path, "w+") as f:
        f.write(
            "(declare-const X_0 Real)\n"
            "(declare-const Y_0 Real)\n"
            "(declare-const Y_1 Real)\n"
            "(assert (and (>= X_0 0) (<= X_0 1)))\n"
            "(assert (>= Y_0 Y_1))\n"
        )

    result = read_vnnlib_simple(vnnlib_path, 1, 2)
    assert len(result) == 1
    assert len(result[0]) == 2
    assert len(result[0][0]) == 1
    assert result[0][0][0] == [0, 1]
    assert len(result[0][1]) == 1
    assert len(result[0][1][0]) == 2
    assert all(result[0][1][0][0][0] == [-1, 1])
    assert all(result[0][1][0][1] == 0)


def test_box_poly_or(tmp_path):
    vnnlib_path = tmp_path / "test.vnnlib"
    with open(vnnlib_path, "w+") as f:
        f.write(
            "(declare-const X_0 Real)\n"
            "(declare-const Y_0 Real)\n"
            "(declare-const Y_1 Real)\n"
            "(assert (>= X_0 0))\n"
            "(assert (<= X_0 1))\n"
            "(assert (or (>= Y_0 Y_1) (>= Y_0 1000)))\n"
        )

    result = read_vnnlib_simple(vnnlib_path, 1, 2)
    assert len(result) == 1
    assert len(result[0]) == 2
    assert len(result[0][0]) == 1
    assert result[0][0][0] == [0, 1]
    assert len(result[0][1]) == 2

    assert len(result[0][1][0]) == 2
    assert result[0][1][0][0].tolist() == [[-1, 1]]
    assert result[0][1][0][1].tolist() == [[0]]

    assert len(result[0][1][1]) == 2
    assert result[0][1][1][0].tolist() == [[-1, 0]]
    assert result[0][1][1][1].tolist() == [[-1000]]


def test_box_poly_dnf_1(tmp_path):
    vnnlib_path = tmp_path / "test.vnnlib"
    with open(vnnlib_path, "w+") as f:
        f.write(
            "(declare-const X_0 Real)\n"
            "(declare-const Y_0 Real)\n"
            "(declare-const Y_1 Real)\n"
            "(assert (>= X_0 0))\n"
            "(assert (<= X_0 1))\n"
            "(assert (or (and (>= Y_0 Y_1)) (and (>= Y_0 1000) (<= Y_1 1010))))\n"
        )

    result = read_vnnlib_simple(vnnlib_path, 1, 2)
    assert len(result) == 1
    assert len(result[0]) == 2
    assert len(result[0][0]) == 1
    assert result[0][0][0] == [0, 1]
    assert len(result[0][1]) == 2

    assert len(result[0][1][0]) == 2
    assert result[0][1][0][0].tolist() == [[-1, 1]]
    assert result[0][1][0][1].tolist() == [[0]]

    assert len(result[0][1][1]) == 2
    assert result[0][1][1][0].tolist() == [[-1, 0], [0, 1]]
    assert result[0][1][1][1].tolist() == [[-1000], [1010]]


def test_box_poly_dnf_2(tmp_path):
    vnnlib_path = tmp_path / "test.vnnlib"
    with open(vnnlib_path, "w+") as f:
        f.write(
            "(declare-const X_0 Real)\n"
            "(declare-const Y_0 Real)\n"
            "(declare-const Y_1 Real)\n"
            "(assert (>= X_0 0))\n"
            "(assert (<= X_0 1))\n"
            "(assert (or (and (>= X_0 0.5) (>= Y_0 Y_1)) (and (<= X_0 0.5) (<= Y_0 Y_1))))\n"
        )

    result = read_vnnlib_simple(vnnlib_path, 1, 2)
    assert len(result) == 2

    assert len(result[0]) == 2
    assert len(result[0][0]) == 1
    assert result[0][0][0] == [0.5, 1.0]
    assert len(result[0][1]) == 1
    assert all(result[0][1][0][0][0] == [-1, 1])
    assert all(result[0][1][0][1] == 0)

    assert len(result[1]) == 2
    assert len(result[1][0]) == 1
    assert result[1][0][0] == [0, 0.5]
    assert len(result[1][1]) == 1
    assert all(result[1][1][0][0][0] == [1, -1])
    assert all(result[1][1][0][1] == 0)


def test_box_poly_dnf_3(tmp_path):
    vnnlib_path = tmp_path / "test.vnnlib"
    with open(vnnlib_path, "w+") as f:
        f.write(
            "(declare-const X_0 Real)\n"
            "(declare-const X_1 Real)\n"
            "(declare-const Y_0 Real)\n"
            "(declare-const Y_1 Real)\n"
            "(assert (>= X_0 0))\n"
            "(assert (<= X_0 1))\n"
            "(assert (>= X_1 0))\n"
            "(assert (<= X_1 1))\n"
            "(assert (or (and (>= X_0 0.5) (>= Y_0 Y_1)) (and (<= X_0 0.5) (<= Y_0 Y_1))))\n"
            "(assert (or (and (>= X_1 0.5) (>= Y_0 Y_1)) (and (<= X_1 0.5) (<= Y_0 Y_1))))\n"
        )

    result = read_vnnlib_simple(vnnlib_path, 2, 2)
    assert len(result) == 4

    assert result[0][0] == [[0.5, 1.0], [0.5, 1.0]]
    assert result[0][1][0][0].tolist() == [[-1, 1], [-1, 1]]
    assert result[0][1][0][1].tolist() == [[0], [0]]

    assert result[1][0] == [[0.0, 0.5], [0.5, 1.0]]
    assert result[1][1][0][0].tolist() == [[-1, 1], [1, -1]]
    assert result[1][1][0][1].tolist() == [[0], [0]]

    assert result[2][0] == [[0.5, 1.0], [0.0, 0.5]]
    assert result[2][1][0][0].tolist() == [[1, -1], [-1, 1]]
    assert result[2][1][0][1].tolist() == [[0], [0]]

    assert result[3][0] == [[0.0, 0.5], [0.0, 0.5]]
    assert result[3][1][0][0].tolist() == [[1, -1], [1, -1]]
    assert result[3][1][0][1].tolist() == [[0], [0]]


def test_error_non_model_variables_1(tmp_path):
    vnnlib_path = tmp_path / "test.vnnlib"
    with open(vnnlib_path, "w+") as f:
        f.write(
            "(declare-const X_0 Real)\n"
            "(declare-const Y_0 Real)\n"
            "(declare-const Y_1 Real)\n"
            "(declare-const eps Real)\n"
            "(assert (and (>= X_0 eps) (<= X_0 eps)))\n"
            "(assert (>= Y_0 Y_1))\n"
        )

    with pytest.raises(RuntimeError, match="unexpected variable type"):
        _ = read_vnnlib_simple(vnnlib_path, 1, 2)


def test_error_non_model_variables_2(tmp_path):
    vnnlib_path = tmp_path / "test.vnnlib"
    with open(vnnlib_path, "w+") as f:
        f.write(
            "(declare-const X_0 Real)\n"
            "(declare-const Y_0 Real)\n"
            "(declare-const Y_1 Real)\n"
            "(declare-const eps Real)\n"
            "(assert (and (>= X_0 0) (<= X_0 1)))\n"
            "(assert (or (and (>= X_0 eps) (>= Y_0 Y_1)) (and (<= X_0 eps) (<= Y_0 Y_1))))\n"
        )

    with pytest.raises(RuntimeError, match="unexpected variable type"):
        _ = read_vnnlib_simple(vnnlib_path, 1, 2)


def test_error_unsupported_func(tmp_path):
    vnnlib_path = tmp_path / "test.vnnlib"
    with open(vnnlib_path, "w+") as f:
        f.write(
            "(declare-const X_0 Real)\n"
            "(declare-const Y_0 Real)\n"
            "(declare-const Y_1 Real)\n"
            "(assert (and (>= X_0 0) (<= (xor 2 X_0) 1)))\n"
            "(assert (>= Y_0 Y_1))\n"
        )

    with pytest.raises(
        RuntimeError, match="Function 'xor' is not supported by the legacy parser"
    ):
        _ = read_vnnlib_simple(vnnlib_path, 1, 2)


def test_add_const(tmp_path):
    vnnlib_path = tmp_path / "test.vnnlib"
    with open(vnnlib_path, "w+") as f:
        f.write(
            "(declare-const X_0 Real)\n"
            "(declare-const Y_0 Real)\n"
            "(assert (>= (+ X_0 1) 1))\n"
            "(assert (<= X_0 1))\n"
            "(assert (>= Y_0 0))\n"
        )

    result = read_vnnlib_simple(vnnlib_path, 1, 1)
    assert len(result) == 1
    assert result[0][0] == [[0, 1]]
    assert len(result[0][1]) == 1
    assert len(result[0][1][0]) == 2
    assert result[0][1][0][0].item() == -1
    assert result[0][1][0][1].item() == 0


def test_add_var(tmp_path):
    vnnlib_path = tmp_path / "test.vnnlib"
    with open(vnnlib_path, "w+") as f:
        f.write(
            "(declare-const X_0 Real)\n"
            "(declare-const Y_0 Real)\n"
            "(declare-const Y_1 Real)\n"
            "(assert (>= X_0 0))\n"
            "(assert (<= X_0 1))\n"
            "(assert (>= Y_0 0))\n"
            "(assert (>= Y_1 0))\n"
            "(assert (<= (+ Y_0 Y_1) 1))\n"
        )

    result = read_vnnlib_simple(vnnlib_path, 1, 2)
    assert len(result) == 1
    assert result[0][0] == [[0, 1]]
    assert len(result[0][1]) == 1
    assert len(result[0][1][0]) == 2
    assert result[0][1][0][0].tolist() == [[-1, 0], [0, -1], [1, 1]]
    assert result[0][1][0][1].tolist() == [[0], [0], [1]]


def test_subtract_const(tmp_path):
    vnnlib_path = tmp_path / "test.vnnlib"
    with open(vnnlib_path, "w+") as f:
        f.write(
            "(declare-const X_0 Real)\n"
            "(declare-const Y_0 Real)\n"
            "(assert (>= (- X_0 1) 0))\n"
            "(assert (<= X_0 10))\n"
            "(assert (>= Y_0 0))\n"
        )

    result = read_vnnlib_simple(vnnlib_path, 1, 1)
    assert len(result) == 1
    assert result[0][0] == [[1, 10]]
    assert len(result[0][1]) == 1
    assert len(result[0][1][0]) == 2
    assert result[0][1][0][0].item() == -1
    assert result[0][1][0][1].item() == 0


def test_subtract_var(tmp_path):
    vnnlib_path = tmp_path / "test.vnnlib"
    with open(vnnlib_path, "w+") as f:
        f.write(
            "(declare-const X_0 Real)\n"
            "(declare-const Y_0 Real)\n"
            "(declare-const Y_1 Real)\n"
            "(assert (>= X_0 0))\n"
            "(assert (<= X_0 1))\n"
            "(assert (>= Y_0 0))\n"
            "(assert (>= Y_1 0))\n"
            "(assert (>= (- Y_0 Y_1) 1))\n"
        )

    result = read_vnnlib_simple(vnnlib_path, 1, 2)
    assert len(result) == 1
    assert result[0][0] == [[0, 1]]
    assert len(result[0][1]) == 1
    assert len(result[0][1][0]) == 2
    assert result[0][1][0][0].tolist() == [[-1, 0], [0, -1], [-1, 1]]
    assert result[0][1][0][1].tolist() == [[0], [0], [-1]]


def test_mul_const(tmp_path):
    vnnlib_path = tmp_path / "test.vnnlib"
    with open(vnnlib_path, "w+") as f:
        f.write(
            "(declare-const X_0 Real)\n"
            "(declare-const Y_0 Real)\n"
            "(assert (>= (* X_0 2) 0))\n"
            "(assert (>= (* (- 2) X_0) (- 2)))\n"
            "(assert (<= (* 0 X_0) 1000))\n"
            "(assert (>= Y_0 0))\n"
        )

    result = read_vnnlib_simple(vnnlib_path, 1, 1)
    assert len(result) == 1
    assert result[0][0] == [[0, 1]]
    assert len(result[0][1]) == 1
    assert len(result[0][1][0]) == 2
    assert result[0][1][0][0].item() == -1
    assert result[0][1][0][1].item() == 0


def test_mul_vars(tmp_path):
    vnnlib_path = tmp_path / "test.vnnlib"
    with open(vnnlib_path, "w+") as f:
        f.write(
            "(declare-const X_0 Real)\n"
            "(declare-const Y_0 Real)\n"
            "(assert (>= (* X_0 2) 0))\n"
            "(assert (<= (* 2 X_0) 2))\n"
            "(assert (>= (* Y_0 Y_0) 0))\n"
        )

    with pytest.raises(NotImplementedError):
        _ = read_vnnlib_simple(vnnlib_path, 1, 1)
