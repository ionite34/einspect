from dataclasses import dataclass


class Tuple(tuple):
    """Tuple extensions."""


# noinspection PyPep8Naming
@dataclass(frozen=True)
class ptr:
    """A pointer to a PyObject."""

    id: int
