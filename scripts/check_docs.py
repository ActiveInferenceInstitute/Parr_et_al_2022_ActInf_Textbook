#!/usr/bin/env python3
"""Documentation gate: relative links resolve and the docs index covers docs/.

The repository has no documentation site and no Markdown link gate upstream
(see docs/validation.md), so this script is the `docs` arm of ./run.sh:

1. every relative link and reference definition in tracked Markdown resolves
   against the file it appears in (anchors and absolute URLs are ignored);
2. every page under docs/ except the generated tree is reachable from
   docs/documentation-index.md, and docs/README.md links that index.

It reads only tracked files and writes nothing.

Run:  ./run.sh docs   (or: python3 scripts/check_docs.py)
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
HUB = DOCS / "README.md"
INDEX = DOCS / "documentation-index.md"
GENERATED = DOCS / "_generated"

SCHEME_RE = re.compile(r"^(?:[a-zA-Z][a-zA-Z0-9+.-]*:|//)")
INLINE_LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]*)\)")
REFERENCE_RE = re.compile(r"^\s{0,3}\[[^\]]+\]:\s*(\S+)")
FENCE_RE = re.compile(r"^\s*(?:```|~~~)")
INLINE_CODE_RE = re.compile(r"`[^`]*`")


def tracked_markdown() -> list[Path]:
    try:
        completed = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "-z", "--", "*.md"],
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f"docs: cannot list tracked Markdown: {exc}")
    names = [name for name in completed.stdout.decode("utf-8").split("\0") if name]
    if not names:
        raise SystemExit("docs: git ls-files returned no Markdown files")
    return [ROOT / name for name in names]


def link_targets(path: Path) -> list[tuple[int, str]]:
    """Return (line number, raw target) for every link outside code fences."""
    targets: list[tuple[int, str]] = []
    in_fence = False
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        stripped = INLINE_CODE_RE.sub("", line)
        for match in INLINE_LINK_RE.finditer(stripped):
            targets.append((number, match.group(1).strip()))
        reference = REFERENCE_RE.match(stripped)
        if reference:
            targets.append((number, reference.group(1)))
    return targets


def relative_target(raw: str) -> str | None:
    """Return the path part of a link, or None when the link is not local."""
    target = raw.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()
    if not target or target.startswith("#") or SCHEME_RE.match(target):
        return None
    target = target.split("#", 1)[0].split("?", 1)[0].strip()
    if not target:
        return None
    return urllib.parse.unquote(target)


def main() -> int:
    failures: list[str] = []
    files = tracked_markdown()
    checked = 0

    for path in files:
        for number, raw in link_targets(path):
            target = relative_target(raw)
            if target is None:
                continue
            checked += 1
            destination = Path(os.path.normpath(os.path.join(path.parent, target)))
            if not destination.exists():
                failures.append(
                    f"{path.relative_to(ROOT)}:{number}: broken relative link {target!r}"
                )

    if not INDEX.is_file():
        failures.append("docs/documentation-index.md is missing")
        linked: set[Path] = set()
    else:
        linked = {
            Path(os.path.normpath(os.path.join(INDEX.parent, target)))
            for _, raw in link_targets(INDEX)
            if (target := relative_target(raw)) is not None
        }
    covered = {
        path
        for path in DOCS.rglob("*.md")
        if GENERATED not in path.parents and path != INDEX
    }
    for path in sorted(covered - linked):
        failures.append(
            f"{path.relative_to(ROOT)}: not listed in docs/documentation-index.md"
        )

    hub_targets = {
        Path(os.path.normpath(os.path.join(HUB.parent, target)))
        for _, raw in link_targets(HUB)
        if (target := relative_target(raw)) is not None
    }
    if INDEX not in hub_targets:
        failures.append("docs/README.md does not link docs/documentation-index.md")

    for failure in failures:
        print(failure, file=sys.stderr)
    print(
        f"docs: {len(files)} Markdown file(s), {checked} relative link(s), "
        f"{len(covered)} docs page(s) indexed, {len(failures)} failure(s)."
    )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
