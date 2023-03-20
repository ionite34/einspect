from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from difflib import unified_diff
from functools import cache
from urllib.parse import urljoin

import requests
from rich.syntax import Syntax
from typing_extensions import Self

CPYTHON_API = "https://api.github.com/repos/python/cpython/"
CPYTHON_GIT = "https://raw.githubusercontent.com/python/cpython/"
CPYTHON_MAIN_VERSION = (3, 12)


@dataclass(frozen=True)
class SourceBlock:
    code: str
    link: str | None = None
    lang: str = "c"

    def __str__(self) -> str:
        return self.code

    def diff(self, other: SourceBlock | str) -> Self | None:
        """Return a unified diff between this and another SourceBlock."""
        if isinstance(other, str):
            other = SourceBlock(other)
        a = self.code.splitlines(keepends=True)
        b = other.code.splitlines(keepends=True)
        # None if equal
        if a == b:
            return None
        length = max(len(a), len(b))
        diff = "".join(unified_diff(b, a))
        return SourceBlock("".join(diff), lang="diff")

    def code_hash(self, comments: bool = False, empty_lines: bool = False) -> str:
        """Return a 10 character blake-2b hash of the source text."""
        block = self
        if not comments:
            block = block.remove_comments()
        if not empty_lines:
            block = block.remove_empty_lines()

        block = block.fix_whitespace()
        return hash_source(block.code)

    def normalize(self) -> Self:
        """Normalize the source code."""
        return self.remove_comments().remove_empty_lines().fix_whitespace()

    def remove_empty_lines(self) -> Self:
        code = re.sub(r"\n\s*\n", "\n", self.code)
        return SourceBlock(code, self.link, self.lang)

    def remove_comments(self) -> Self:
        """Remove C comments from the source code."""
        code = re.sub(r"//.*$", "", self.code, flags=re.MULTILINE)
        code = re.sub(r"/\*.*?\*/", "", code, flags=re.DOTALL)
        return SourceBlock(code, self.link, self.lang)

    def fix_whitespace(self) -> Self:
        """Fix whitespace in the source code."""
        # Remove any whitespace between ; and \n
        code = re.sub(r";\s*\n", ";\n", self.code)
        return SourceBlock(code, self.link, self.lang)

    def as_syntax(self, **kwargs) -> Syntax:
        return Syntax(self.code, self.lang, **kwargs)


@cache
def branches() -> list[str]:
    data = requests.get(urljoin(CPYTHON_API, "branches")).json()
    return [branch["name"] for branch in data]


@cache
def branch_range(start: str, end: str) -> list[str]:
    start = branches().index(start)
    end = branches().index(end) + 1
    return branches()[start:end]


def build_link(path: str, tag: str = "main", base: str = CPYTHON_GIT) -> str:
    path = path.lstrip("/")
    return f"{base}{tag}/{path}"


def fetch_git(path: str, tag: str = "main", base: str = CPYTHON_GIT) -> str:
    link = build_link(path, tag, base)
    resp = requests.get(link)
    resp.raise_for_status()
    return resp.text


def extract_struct(name: str, text: str, mode: str = "auto") -> SourceBlock:
    # trailing mode (i.e. `struct { ... } <name>;`)
    if mode == "t":
        pattern = rf"struct\s+{name}" + r"\s+\{([^}]*)}\s?(\w+)?;"
    # front mode (i.e. `struct <name> { ... } <?>;`)
    elif mode in ("f", "auto"):
        pattern = r"struct\s+\{([^}]*)}\s?" + f"{name};"
    else:
        raise ValueError(f"Invalid mode {mode!r}.")

    match = re.search(pattern, text, re.DOTALL)
    if match is None:
        if mode == "auto":
            return extract_struct(name, text, "t")
        raise ValueError(f"Struct {name!r} not found in text.")
    return SourceBlock(match.group(0).strip())


def hash_source(text: str) -> str:
    """Return a 9+1 character blake-2b hash of the source text. With 10th character as checksum."""
    h = hashlib.blake2b(text.encode()).hexdigest()[:9]
    check = sum(int(c, 16) for c in h) % 16
    return h + hex(check)[-1]


def check_hash(hash_: str) -> bool:
    """Check if a hash is valid."""
    if len(hash_) != 10:
        return False
    # Check checksum
    expected = sum(int(c, 16) for c in hash_[:-1]) % 16
    return int(hash_[-1], 16) == expected
