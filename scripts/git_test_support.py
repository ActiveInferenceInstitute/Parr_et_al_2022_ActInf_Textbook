"""Refuse inherited Git controls before temporary repositories are created."""

import os
import unittest


SAFE_GIT_NAMES = frozenset({
    "GIT_TERMINAL_PROMPT", "GIT_OPTIONAL_LOCKS", "GIT_NO_LAZY_FETCH",
    "GIT_HTTP_LOW_SPEED_LIMIT", "GIT_HTTP_LOW_SPEED_TIME",
    # Restricts parent discovery; cannot redirect explicit fixture-root writes.
    "GIT_CEILING_DIRECTORIES",
})


def require_safe_git_environment(environment=None):
    environment = os.environ if environment is None else environment
    blocked = sorted(
        name for name, value in environment.items()
        if name.startswith("GIT_") and name not in SAFE_GIT_NAMES
        and not (name == "GIT_PAGER" and value in ("", "cat"))
    )
    if blocked:
        raise RuntimeError("Unsafe inherited Git fixture controls: " + ", ".join(blocked))


class GitFixtureTests(unittest.TestCase):
    def setUp(self):
        super().setUp()
        require_safe_git_environment()
