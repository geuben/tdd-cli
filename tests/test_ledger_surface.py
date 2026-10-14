"""The ledger's surface: one query layer, and every method of it classified for guests.

A ledger service exposes `Ledger` methods by name over a socket, so the only SQL in the
codebase must be the SQL behind those names. A module that spoke SQL on its own would
be a query the service cannot see, scope or refuse.
"""

from __future__ import annotations

import ast
import inspect
import re
from pathlib import Path

import tddcli
from tddcli import ledger as ledger_mod

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
            isinstance(node, ast.Constant) and isinstance(node.value, str) and SQL.match(node.value)
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


#: A method that touches one run's rows names that run by one of these parameters.
OWNERSHIP = {"run_id", "cycle_id", "contract_id"}


def test_every_ledger_method_is_classified_and_scoped():
    reads = getattr(ledger_mod, "GUEST_READS", frozenset())
    writes = getattr(ledger_mod, "GUEST_WRITES", frozenset())
    host_only = getattr(ledger_mod, "HOST_ONLY", frozenset())
    rooted = getattr(ledger_mod, "SOURCE_ROOTED", frozenset())
    public = sorted(
        name
        for name, value in vars(ledger_mod.Ledger).items()
        if not name.startswith("_") and callable(value)
    )
    problems = []
    for name in public:
        classes = [s for s in (reads, writes, host_only) if name in s]
        if len(classes) != 1:
            problems.append(f"{name}: in {len(classes)} of GUEST_READS/GUEST_WRITES/HOST_ONLY")
        elif (name in reads or name in writes) and name not in rooted:
            params = set(inspect.signature(getattr(ledger_mod.Ledger, name)).parameters)
            if not params & OWNERSHIP:
                problems.append(f"{name}: a guest method with no run, cycle or contract id")
    assert problems == []
