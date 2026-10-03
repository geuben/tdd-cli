"""The ledger's surface: one query layer, and every method of it classified for guests.

A ledger service exposes `Ledger` methods by name over a socket, so the only SQL in the
codebase must be the SQL behind those names. A module that spoke SQL on its own would
be a query the service cannot see, scope or refuse.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import tddcli

SRC = Path(tddcli.__file__).resolve().parent

SQL = re.compile(
    r"^\s*(SELECT|INSERT\s+INTO|UPDATE\s+\w+\s+SET|DELETE\s+FROM|CREATE\s+(TABLE|INDEX)"
    r"|ALTER\s+TABLE|PRAGMA)\b",
    re.IGNORECASE,
)
GENERIC = {"one", "all", "insert", "update", "db", "_write"}


def _receiver_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _offences(path: Path) -> list[str]:
    found: list[str] = []
    for node in ast.walk(ast.parse(path.read_text(), filename=str(path))):
        if isinstance(node, ast.Import) and any(a.name == "sqlite3" for a in node.names):
            found.append(f"{node.lineno}: import sqlite3")
        elif isinstance(node, ast.ImportFrom) and node.module == "sqlite3":
            found.append(f"{node.lineno}: from sqlite3")
        elif (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and SQL.match(node.value)
        ):
            found.append(f"{node.lineno}: SQL {node.value.strip()[:40]!r}")
        elif (
            isinstance(node, ast.Attribute)
            and node.attr in GENERIC
            and _receiver_name(node.value) == "ledger"
        ):
            found.append(f"{node.lineno}: ledger.{node.attr}")
    return found


def test_no_module_but_the_ledger_speaks_sql():
    offenders = {
        str(path.relative_to(SRC)): found
        for path in sorted(SRC.rglob("*.py"))
        if path.name != "ledger.py" or path.parent != SRC
        if (found := _offences(path))
    }
    assert offenders == {}
