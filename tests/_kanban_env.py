"""Helper for scrubbing Kanban env-var pins from a subprocess env dict.

Lives in a regular module (not ``tests/conftest.py``) so test files can
import it via ``from tests._kanban_env import clean_kanban_env`` without
relying on pytest's special conftest discovery. Importing a conftest by
its module path is unusual — under some rootdir/``__init__.py`` resolution
combinations pytest may load ``tests/conftest.py`` under a different
module name, leaving callers with a different copy of the helper than the
conftest pytest actually used. Keeping the helper here sidesteps that.
"""

from __future__ import annotations

import os


_KANBAN_ISOLATION_VARS = (
    "HERMES_KANBAN_DB",
    "HERMES_KANBAN_HOME",
    "HERMES_KANBAN_BOARD",
    "HERMES_KANBAN_WORKSPACES_ROOT",
)


def clean_kanban_env(env: dict | None = None) -> dict:
    """Return a copy of ``env`` (or ``os.environ``) with kanban pins removed.

    Use this helper when constructing the ``env=`` arg for a subprocess
    spawn of ``hermes kanban …`` — it guarantees the child cannot inherit
    a stale ``HERMES_KANBAN_DB`` / ``HERMES_KANBAN_BOARD`` /
    ``HERMES_KANBAN_HOME`` / ``HERMES_KANBAN_WORKSPACES_ROOT`` from the
    parent process and write to a hostile path (see ALF-267).
    """
    base = dict(os.environ if env is None else env)
    for var in _KANBAN_ISOLATION_VARS:
        base.pop(var, None)
    return base
