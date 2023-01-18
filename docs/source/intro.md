(intro/get-started)=

# Quickstart

## Compatibility
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/einspect)][pypi]
[![Build](https://github.com/ionite34/einspect/actions/workflows/build.yml/badge.svg)](https://github.com/ionite34/einspect/actions/workflows/build.yml)
- CI Tests currently run from Python 3.8 - 3.11, across Linux, Windows, and macOS.

[![Build][impl-cpython]](https://github.com/ionite34/einspect/actions/workflows/build.yml)
- einspect was developed around the CPython implementation, compatibility with other implementations is not impossible, but is currently unlikely.
  - PyPy compatibility is blocked due to the [lack of a `ctypes.pythonapi` protocol](https://doc.pypy.org/en/latest/discussion/ctypes-implementation.html#discussion-and-limitations).

## Installation

[![PyPI][pypi-badge]][pypi-link]

To install use [pip](https://pip.pypa.io):

```bash
pip install einspect
```
> **Dependencies**
>
> `typing-extensions ~= 4.4.0`

[impl-cpython]: https://img.shields.io/pypi/implementation/einspect
[pypi]: https://pypi.org/project/einspect/
[pypi-badge]: https://img.shields.io/pypi/v/einspect.svg
[pypi-link]: https://pypi.org/project/einspect
(intro/sphinx)=
