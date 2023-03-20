"""Parsing struct metadata."""
from __future__ import annotations

import operator
import re
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from typing import NamedTuple

from docutils.core import publish_doctree
from typing_extensions import Self

from einspect import structs

RE_SOURCE = re.compile(
    r"^source(?:\[(?P<version>[^]]+)\])?:"
    r"\s+(?P<file>[^(]+)"
    r"\s+\((?P<name>[^)]+)\)"
    r"(\s+#\[(?P<hash>\w+)])?$"
)
RE_SOURCE_HASH_ONLY = re.compile(
    r"^source(?:\[(?P<version>[^]]+)\])?:" r"(\s+#\[(?P<hash>\w+)])?$"
)

RE_HASH = re.compile(r"#[(?P<hash>.*?)]$")
RE_QUALIFIER = re.compile(r"(?P<qualifier>[<>=]{1,2})(?P<version>\d+\.\d+)")

DEF_KINDS = {"struct"}
QUALIFIERS = {
    ">": operator.gt,
    "<": operator.lt,
    "==": operator.eq,
    "=": operator.eq,
}


# Example
# ..
#   source: Include/internal/pycore_frame.h (struct _frame)
#   source[<3.11]: Include/cpython/frameobject.h (struct _frame)
class SourceEntry(NamedTuple):
    file: str
    def_kind: str
    def_name: str
    version: str | None
    hash: str | None

    @classmethod
    def from_str(cls, text: str, default: Self | None = None) -> Self:
        """
        Create a SourceEntry from a text string.

        If default is specified, contents will be used to fill hash-only entries.
        """
        if m_source := RE_SOURCE.match(text):
            m_version = m_source.group("version")
            m_hash = m_source.group("hash")
            def_kind, def_name = m_source.group("name").strip().split(" ", 1)

            if def_kind not in DEF_KINDS:
                raise ValueError(
                    f"Unknown definition kind {def_kind!r}, expected one of {DEF_KINDS!r}"
                )

            return cls(m_source.group("file"), def_kind, def_name, m_version, m_hash)
        elif m_source_hash := RE_SOURCE_HASH_ONLY.match(text):
            m_version = m_source_hash.group("version")
            m_hash = m_source_hash.group("hash")

            if default is None:
                raise ValueError(f"No default found for hash-only source {text!r}")

            return cls(
                default.file, default.def_kind, default.def_name, m_version, m_hash
            )

        raise ValueError(f"Failed to parse docstring line {text!r}")


@dataclass(frozen=True)
class PyVersionQualifier:
    version: tuple[int, int]
    qualifier: Callable[[tuple, tuple], bool]

    @classmethod
    def from_str(cls, text: str, default: Self | None = None) -> Self:
        """Create a PyVersionQualifier from a text string."""
        if not (m_qual := RE_QUALIFIER.match(text)):
            raise ValueError(f"Failed to parse qualifier {text!r}")

        major, minor = tuple(int(v) for v in m_qual.group("version").split("."))

        if m_qual.group("qualifier") not in QUALIFIERS:
            raise ValueError(f"Unknown qualifier {m_qual.group('qualifier')!r}")
        qualifier = QUALIFIERS[m_qual.group("qualifier")]

        return cls((major, minor), qualifier)

    def match(self, version: str | tuple[int, int]) -> bool:
        """Check if a version matches the qualifier."""
        if isinstance(version, str):
            version = tuple(int(v) for v in version.split("."))
        return self.qualifier(version, self.version)


class StructMetadata(OrderedDict[str, SourceEntry]):
    """Metadata for a struct."""

    source_cls: type | None = None

    @classmethod
    def from_str(cls, text: str) -> StructMetadata:
        """Create a StructMetadata from a text string."""
        lines = text.splitlines()
        result = cls()
        for line in lines:
            if line.strip().startswith("source"):
                # Provide default if available
                default = result.get("default")
                entry = SourceEntry.from_str(line, default=default)
                version = entry.version or "default"
                result[version] = entry
            else:
                raise ValueError(f"Unknown metadata type: {line!r}")

        return cls(result)

    @classmethod
    def from_cls(cls, struct: type) -> StructMetadata:
        """Create a StructMetadata from a struct class."""
        st_doc = struct.__doc__
        nodes = publish_doctree(st_doc).traverse()
        comments: str = next(
            node for node in nodes if node.tagname == "comment"
        ).astext()
        # Include the source class in the metadata
        res = cls.from_str(comments)
        res.source_cls = struct
        return res

    @classmethod
    def from_struct_name(cls, name: str) -> StructMetadata:
        """Create a StructMetadata from a struct class name."""
        if name not in structs.__all__:
            raise ValueError(f"Struct {name!r} not found in structs '__all__'.")
        return cls.from_cls(getattr(structs, name))

    def get_version(self, version: str) -> SourceEntry:
        """Get the file and name for a given version."""
        items = filter(lambda t: t[0] != "default", self.items())
        for key, value in items:
            if PyVersionQualifier.from_str(key).match(version):
                return value

        # If nothing matches, use default
        if (default := self.get("default")) is None:
            data_versions = ", ".join(self.keys())
            raise KeyError(
                f"No matching version {version!r} found in metadata ({data_versions})"
            )
        return default
