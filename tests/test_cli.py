import numpy as np
import pytest

from vnnlib.cli import main
from vnnlib.errors import VnnLibError


def test_nano(tmp_path):
    vnnlib_path = tmp_path / "test.vnnlib"
    with open(vnnlib_path, "w+") as f:
        f.write(
            "(declare-const X_0 Real)\n(declare-const Y_0 Real)\n(assert (>= X_0 -1))\n(assert (<= X_0 1))\n(assert (<= Y_0 -1))\n"
        )
    out_path = tmp_path / "out.npy"

    result = main([str(vnnlib_path), "-o", str(out_path), "--compat"])
    assert result is None

    output = np.load(out_path, allow_pickle=True)
    assert output == [([[-1, 1]], [(np.array([[1]]), np.array([[-1]]))])]


def test_unsupported_spec_format(tmp_path):
    vnnlib_path = tmp_path / "test.py"
    with open(vnnlib_path, "w+"):
        pass
    out_path = tmp_path / "out.npy"

    with pytest.raises(VnnLibError, match="Unsupported file type: .py"):
        _ = main([str(vnnlib_path), "-o", str(out_path), "--compat"])


def test_unsupported_output_format(tmp_path):
    vnnlib_path = tmp_path / "test.vnnlib"
    with open(vnnlib_path, "w+") as f:
        f.write(
            "(declare-const X_0 Real)\n(declare-const Y_0 Real)\n(assert (>= X_0 -1))\n(assert (<= X_0 1))\n(assert (<= Y_0 -1))\n"
        )
    out_path = tmp_path / "out.npy"

    with pytest.raises(
        NotImplementedError,
        match="Currently only the VNN-COMP-1 output format is supported",
    ):
        _ = main([str(vnnlib_path), "-o", str(out_path)])
