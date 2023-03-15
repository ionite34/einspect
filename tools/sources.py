import re
from functools import cache
from urllib.parse import urljoin

import requests

CPYTHON_API = "https://api.github.com/repos/python/cpython/"
CPYTHON_GIT = "https://raw.githubusercontent.com/python/cpython/"


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
    return requests.get(link).text


def extract_struct(name: str, text: str) -> str:
    pattern = rf"struct {re.escape(name)} \{{.*?\}};"
    match = re.search(pattern, text, re.DOTALL).group(0)
    return match
