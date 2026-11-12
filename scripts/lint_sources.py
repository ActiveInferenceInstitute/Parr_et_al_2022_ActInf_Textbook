#!/usr/bin/env python3
"""Repository lint: every tracked Python file compiles and every tracked JSON/notebook file parses.

This is the `lint` arm of ./run.sh. The repository has no style linter and no
type checker (see docs/validation.md), so the static arm is exactly what it
says: syntax and machine-readable-metadata validity over tracked files. It
reads only files `git ls-files` reports and writes nothing.

Run:  ./run.sh lint   (or: python3 scripts/lint_sources.py)
"""

from __future__ import annotations

import json
import py_compile
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYTHON_SUFFIXES = {".py"}
JSON_SUFFIXES = {".json", ".ipynb"}


def tracked_files() -> list[Path]:
    """Return the tracked files as absolute paths, or stop with the git error."""
    try:
        completed = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "-z"],
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f"lint: cannot list tracked files: {exc}")
    names = [name for name in completed.stdout.decode("utf-8").split("\0") if name]
    if not names:
        raise SystemExit("lint: git ls-files returned no tracked files")
    return [ROOT / name for name in names]


def main() -> int:
    files = tracked_files()
    python_files = [path for path in files if path.suffix in PYTHON_SUFFIXES]
    json_files = [path for path in files if path.suffix in JSON_SUFFIXES]
    failures: list[str] = []

    with tempfile.TemporaryDirectory(prefix="lint-pycache-") as cache:
        for index, path in enumerate(python_files):
            try:
                py_compile.compile(
                    str(path),
                    cfile=str(Path(cache) / f"{index}.pyc"),
                    doraise=True,
                )
            except py_compile.PyCompileError as exc:
                failures.append(f"{path.relative_to(ROOT)}: {exc.msg.strip()}")

    for path in json_files:
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            failures.append(f"{path.relative_to(ROOT)}: {exc}")

    for failure in failures:
        print(failure, file=sys.stderr)
    print(
        f"lint: {len(python_files)} Python file(s) compiled, "
        f"{len(json_files)} JSON/notebook file(s) parsed, {len(failures)} failure(s)."
    )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())