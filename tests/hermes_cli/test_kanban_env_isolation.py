"""Regression coverage for Kanban env contamination (ALF-268).

The Kanban CLI resolves its database/board via these env vars (highest →
lowest precedence):

* ``HERMES_KANBAN_DB``      — pins the DB file path directly
* ``HERMES_KANBAN_BOARD``   — pins the active board slug
* ``HERMES_KANBAN_HOME``    — pins the shared board root
* ``HERMES_HOME``           — falls back to ``<root>/kanban.db``

A test that spawns a child ``hermes kanban …`` subprocess typically scopes
isolation by setting ``HERMES_HOME=<tmpdir>`` in the child env. If the
PARENT process still has a stale ``HERMES_KANBAN_DB`` / ``HERMES_KANBAN_BOARD``
exported (operator shell, leaky earlier test, CI env), and the child env is
built with ``dict(os.environ)`` (the standard pattern in this repo — see
``tests/hermes_cli/test_kanban_boards.py::_cli``), those higher-precedence
pins leak through and the child writes to the hostile path instead of the
test-isolated board.

This file is the deterministic regression: it deliberately poisons the
parent env with production-like values, spawns a real child CLI with only
``HERMES_HOME`` overridden, and asserts the child wrote ONLY to the
isolated board. Without the ALF-267 isolation fix the child writes to the
hostile DB path; with the fix it writes to the isolated board.
"""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

_WORKTREE = Path(__file__).resolve().parents[2]


def _run_cli(args: list[str], env: dict) -> subprocess.CompletedProcess:
    """Invoke ``python -m hermes_cli.main kanban …`` as a real subprocess.

    Pins ``PYTHONPATH`` to the worktree so the child imports this
    checkout's ``hermes_cli`` rather than a system-installed clone, mirroring
    the ``_cli`` helper in ``test_kanban_boards.py``.
    """
    child_env = dict(env)
    child_env["PYTHONPATH"] = str(_WORKTREE)
    return subprocess.run(
        [sys.executable, "-m", "hermes_cli.main", "kanban", *args],
        env=child_env,
        capture_output=True,
        text=True,
        cwd=str(_WORKTREE),
        timeout=30,
    )


@pytest.mark.xfail(
    strict=True,
    reason=(
        "ALF-267 env-isolation fix is not yet in main. Without it, the "
        "child CLI honors the parent process's HERMES_KANBAN_DB / "
        "HERMES_KANBAN_BOARD and writes to the hostile path instead of "
        "the per-test isolated board. Flip to strict-pass once ALF-267 "
        "lands."
    ),
)
def test_hostile_env_does_not_leak_to_child_cli(tmp_path, monkeypatch):
    """Hostile parent HERMES_KANBAN_* env must not leak into child CLI.

    The child must write the new task to the per-test isolated board
    (``<isolated_home>/kanban.db``) and must NOT touch the hostile DB
    path the parent process has exported.
    """
    # Per-test isolated HERMES_HOME. The child gets only this override —
    # everything else is inherited from os.environ, which is exactly the
    # pattern that exposed the contamination hazard.
    isolated_home = tmp_path / "isolated_hermes_home"
    isolated_home.mkdir()
    isolated_db = isolated_home / "kanban.db"

    # Hostile DB path under a separate "production-like" tree. We point
    # to a path the child would HAVE to create itself if it honored the
    # leaked pin — and we assert it never does.
    hostile_root = tmp_path / "prod_like_hermes_home"
    hostile_root.mkdir()
    hostile_db = hostile_root / "kanban.db"

    # Poison the parent env with the same shape an operator's shell or a
    # leaky earlier test would leave behind.
    monkeypatch.setenv("HERMES_KANBAN_DB", str(hostile_db))
    monkeypatch.setenv("HERMES_KANBAN_BOARD", "production")

    # Build the child env the realistic way: copy os.environ, override
    # only HERMES_HOME. If the isolation fix is missing, the hostile pins
    # ride through unchanged.
    child_env = dict(os.environ)
    child_env["HERMES_HOME"] = str(isolated_home)

    task_title = "alf-268-regression-marker"
    result = _run_cli(
        [
            "create",
            task_title,
            "--assignee", "dev",
            "--json",
        ],
        env=child_env,
    )
    assert result.returncode == 0, (
        f"child CLI failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )

    # The CLI emits the created task as JSON when --json is passed; surface
    # the id for the DB assertions below.
    payload = json.loads(result.stdout)
    task_id = payload["id"]

    # Primary assertion: the hostile DB must not exist. The child must not
    # have written to (or even initialized) the leaked path.
    assert not hostile_db.exists(), (
        f"child CLI wrote to leaked HERMES_KANBAN_DB at {hostile_db}; "
        f"env isolation regression — hostile parent env leaked through."
    )

    # Belt-and-braces: the isolated DB must exist and must contain the
    # task we just created.
    assert isolated_db.exists(), (
        f"isolated DB {isolated_db} was never written; the CLI resolved "
        f"the DB path somewhere else (likely the leaked hostile pin)."
    )
    with sqlite3.connect(str(isolated_db)) as conn:
        row = conn.execute(
            "SELECT title FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
    assert row is not None, (
        f"task {task_id} not found in isolated DB {isolated_db}; the CLI "
        f"wrote it to a different board."
    )
    assert row[0] == task_title


def test_explicit_env_override_in_child_uses_isolated_board(tmp_path, monkeypatch):
    """Control test: when the child env explicitly clears the hostile pins,
    the child must use the isolated board.

    This is the "fix is applied" shape — verifies the test harness itself
    is correct (i.e., when the hazardous env vars are not propagated, the
    isolated board is used). It also doubles as a smoke test for the CLI's
    HERMES_HOME-only resolution path.
    """
    isolated_home = tmp_path / "isolated_hermes_home"
    isolated_home.mkdir()
    isolated_db = isolated_home / "kanban.db"

    hostile_root = tmp_path / "prod_like_hermes_home"
    hostile_root.mkdir()
    hostile_db = hostile_root / "kanban.db"

    monkeypatch.setenv("HERMES_KANBAN_DB", str(hostile_db))
    monkeypatch.setenv("HERMES_KANBAN_BOARD", "production")

    # Explicitly scrubbed child env — what the fix should produce.
    child_env = dict(os.environ)
    child_env["HERMES_HOME"] = str(isolated_home)
    for var in ("HERMES_KANBAN_DB", "HERMES_KANBAN_BOARD", "HERMES_KANBAN_HOME",
                "HERMES_KANBAN_WORKSPACES_ROOT"):
        child_env.pop(var, None)

    task_title = "alf-268-control-marker"
    result = _run_cli(
        ["create", task_title, "--assignee", "dev", "--json"],
        env=child_env,
    )
    assert result.returncode == 0, (
        f"child CLI failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    task_id = json.loads(result.stdout)["id"]

    assert not hostile_db.exists()
    assert isolated_db.exists()
    with sqlite3.connect(str(isolated_db)) as conn:
        row = conn.execute(
            "SELECT title FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
    assert row is not None
    assert row[0] == task_title
