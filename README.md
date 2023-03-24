# vnnlib

[![PyPI - Version](https://img.shields.io/pypi/v/vnnlib.svg)](https://pypi.org/project/vnnlib)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/vnnlib.svg)](https://pypi.org/project/vnnlib)

-----

A python package for parsing neural network properties in the [VNN-LIB format](https://www.vnnlib.org/).
It should currently parse a superset of the VNN-LIB spec that was supported by the [example parser](https://github.com/stanleybak/nnenum/blob/master/src/nnenum/vnnlib.py) written by Stan Bak for [VNN-COMP](https://sites.google.com/view/vnn2023), and will produce compiled specs in the same format.
Additionally, we allow parsing of gzip, bzip2, and lzma compressed specs.

> Our parser is currently slower for large files than the previous scripts due to the increased specification support. 
> However, we expect significant optimization opportunities are available, and that overhead will decrease over time.

> This package is still alpha software and APIs other than the compatibility API may change before the first release. 
> We hope to have a stable release out before or during the benchmark proposal phase of VNN-COMP 2023.


## Installation

For the latest stable version, you can install from PyPI with:

```console
pip install vnnlib
```

> PyPI currently only has pre-releases of `vnnlib`. 
> To install a pre-release version, add the `--pre` option to the above command.

For the latest updates of `vnnlib`, you can pip install directly from the GitHub repo with:

```console
pip install git+https://github.com/dlshriver/vnnlib.git@main
```

## Usage

This package can be used as a drop-in replacement for the VNN-COMP utility script by importing 

```python
from vnnlib.compat import read_vnnlib_simple
```

wherever you previously imported `read_vnnlib_simple`.

### Standalone

The parser can also be used to compile vnnlib ahead of time to reduce future property read times. The result of parsing will be pickled and saved to the location specified.

```console
python -m vnnlib [FILE] --compat -o [OUTPUTFILE]
```

### API

We provide a full VNN-LIB parser which will generate an AST for a given specification.
To manipulate this AST to generate useful representations that can be dispatched to a verifier, we provide a transformer class which visits the nodes of the AST.
We implement one version of this to parse and generate outputs in the format used in prior years of VNN-COMP in `vnnlib/compat.py`

> Documentation will hopefully be coming soon.

## License

`vnnlib` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
