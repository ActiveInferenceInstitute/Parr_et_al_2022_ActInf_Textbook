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

import html
import os
import re
import string
import subprocess
import sys
import urllib.parse
from pathlib import Path
from html.entities import html5

ROOT = Path(__file__).resolve().parent.parent

SCHEME_RE = re.compile(r"^(?:[a-zA-Z][a-zA-Z0-9+.-]*:|//)")
REFERENCE_RE = re.compile(r" {0,3}\[((?:\\.|[^\]\\\n])+)\]:[ \t]*")
FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
ESCAPE_RE = re.compile(r"\\([" + re.escape(string.punctuation) + r"])")
ATX_HEADING_RE = re.compile(r" {0,3}#{1,6}(?:[ \t]|$)", re.MULTILINE)
BLOCK_BREAK_RE = re.compile(
    r"\n(?:[ \t]*\n| {0,3}(?:#{1,6}(?:[ \t]|$)|>|[-+*][ \t]|"
    r"0{0,8}1[.)][ \t]+(?=\S)|(?:[-*_][ \t]*){3,}(?:\n|$)|"
    r"(?:=+|-+)[ \t]*(?:\n|$)|<[/!?A-Za-z]))", re.MULTILINE
)
ENTITY_RE = re.compile(r"&(?:#[0-9]{1,7}|#[xX][0-9A-Fa-f]{1,6}|[A-Za-z][A-Za-z0-9]+);")


def tracked_markdown(root: Path = ROOT) -> list[Path]:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z", "--", "*.md"],
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f"docs: cannot list tracked Markdown: {exc}")
    names = [name for name in completed.stdout.decode("utf-8").split("\0") if name]
    if not names:
        raise SystemExit("docs: git ls-files returned no Markdown files")
    return [root / name for name in names]


def _unfenced_text(text: str) -> str:
    """Hide fenced blocks without changing line numbers or confusing fence delimiters."""
    active: str | None = None
    lines: list[str] = []
    for line in text.splitlines(keepends=True):
        fence = FENCE_RE.match(line.rstrip("\r\n"))
        if active is not None:
            if (
                fence
                and fence[1][0] == active[0]
                and len(fence[1]) >= len(active)
                and not fence[2].strip()
            ):
                active = None
            lines.append("\n" if line.endswith("\n") else "")
        elif fence and (fence[1][0] == "~" or "`" not in fence[2]):
            active = fence[1]
            lines.append("\n" if line.endswith("\n") else "")
        else:
            lines.append(line)
    return "".join(lines)


def _space_end(text: str, start: int) -> int | None:
    end = start
    while end < len(text) and text[end] in " \t\r\n":
        end += 1
    return None if text.count("\n", start, end) > 1 else end


def _destination(text: str, start: int) -> tuple[str, int] | None:
    """Read an angle-delimited or balanced bare destination, preserving escapes."""
    if start < len(text) and text[start] == "<":
        end = start + 1
        while end < len(text):
            if text[end] == "\\" and end + 1 < len(text) and text[end + 1] != "\n":
                end += 2
                continue
            if text[end] == ">":
                return text[start + 1:end], end + 1
            if text[end] in "<\r\n":
                return None
            end += 1
        return None
    end, depth = start, 0
    while end < len(text):
        character = text[end]
        if character == "\\" and end + 1 < len(text) and text[end + 1] != "\n":
            end += 2
            continue
        if character in " \t\r\n" or (character == ")" and depth == 0):
            break
        if character == "<":
            return None
        if character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
        end += 1
    return None if depth else (text[start:end], end)


def _title_end(text: str, start: int) -> int | None:
    if start >= len(text) or text[start] not in "\"'(":
        return None
    closer = ")" if text[start] == "(" else text[start]
    end = start + 1
    while end < len(text):
        if text[end] == "\\" and end + 1 < len(text):
            end += 2
            continue
        if text[end] == closer:
            if re.search(r"\n[ \t]*\n", text[start:end]):
                return None
            return end + 1
        if closer == ")" and text[end] == "(":
            return None
        end += 1
    return None


def _inline_destination(text: str, start: int) -> tuple[str, int] | None:
    target_start = _space_end(text, start)
    if target_start is None:
        return None
    if target_start > start and target_start < len(text) and text[target_start] in "\"'":
        parsed = ("", target_start)
    else:
        parsed = _destination(text, target_start)
    if parsed is None:
        return None
    target, end = parsed
    after = _space_end(text, end)
    if after is None or after >= len(text):
        return None
    if text[after] == ")":
        return target, after + 1
    if after == end and target:
        return None
    title_end = _title_end(text, after)
    if title_end is None:
        return None
    after = _space_end(text, title_end)
    if after is not None and after < len(text) and text[after] == ")":
        return target, after + 1
    return None


def _reference_destination(text: str, start: int) -> tuple[str, int] | None:
    target_start = _space_end(text, start)
    if target_start is None:
        return None
    parsed = _destination(text, target_start)
    if parsed is None:
        return None
    target, end = parsed
    if end == target_start:
        return None
    after = end
    while after < len(text) and text[after] in " \t\r":
        after += 1
    line_end = after
    if after == len(text):
        return target, after
    next_line = text[after] == "\n"
    if next_line:
        after = _space_end(text, after)
        if after is None:
            return target, line_end
    if after == end:
        return None
    title_end = _title_end(text, after)
    if title_end is None:
        return (target, line_end) if next_line else None
    after = title_end
    while after < len(text) and text[after] in " \t\r":
        after += 1
    if after == len(text) or text[after] == "\n":
        return target, after
    return (target, line_end) if next_line else None


def _code_span_end(text: str, start: int) -> int:
    end = start
    while end < len(text) and text[end] == "`":
        end += 1
    delimiter = text[start:end]
    block_break = BLOCK_BREAK_RE.search(text, end)
    limit = block_break.start() if block_break else len(text)
    line_start = text.rfind("\n", 0, start) + 1
    if ATX_HEADING_RE.match(text, line_start):
        heading_end = text.find("\n", end)
        if heading_end != -1:
            limit = min(limit, heading_end)
    candidate = text.find(delimiter, end, limit)
    while candidate != -1:
        after = candidate + len(delimiter)
        if text[candidate - 1] != "`" and (after == len(text) or text[after] != "`"):
            return after
        candidate = text.find(delimiter, after, limit)
    return end


def link_targets(path: Path) -> list[tuple[int, str]]:
    """Return line numbers and destinations, excluding titles and fenced/inline code."""
    text = _unfenced_text(path.read_text(encoding="utf-8"))
    targets: list[tuple[int, str]] = []
    labels: list[int] = []
    index, number = 0, 1
    while index < len(text):
        following = index + 1
        reference = REFERENCE_RE.match(text, index) if index == 0 or text[index - 1] == "\n" else None
        parsed = _reference_destination(text, reference.end()) if reference else None
        if parsed is not None:
            target, following = parsed
            targets.append((number, target))
        elif text[index] == "\\":
            following = min(index + 2, len(text))
        elif text[index] == "`":
            following = _code_span_end(text, index)
        elif text[index] == "[":
            labels.append(index)
        elif text[index] == "]" and labels:
            labels.pop()
            if following < len(text) and text[following] == "(":
                parsed = _inline_destination(text, following + 1)
                if parsed is not None:
                    target, following = parsed
                    targets.append((number, target))
        number += text.count("\n", index, following)
        index = following
    return targets


def relative_target(raw: str) -> str | None:
    """Normalize a parsed destination; retain significant spaces inside angle links."""
    target = ENTITY_RE.sub(
        lambda match: html.unescape(match[0]) if match[0].startswith("&#")
        else html5.get(match[0][1:], match[0]),
        ESCAPE_RE.sub(r"\1", raw),
    )
    if not target or target.startswith("#") or SCHEME_RE.match(target):
        return None
    target = target.split("#", 1)[0].split("?", 1)[0]
    if not target:
        return None
    return urllib.parse.unquote(target)


def main(root: Path = ROOT) -> int:
    root = root.resolve()
    docs = root / "docs"
    hub = docs / "README.md"
    index = docs / "documentation-index.md"
    generated = docs / "_generated"
    failures: list[str] = []
    files = tracked_markdown(root)
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
                    f"{path.relative_to(root)}:{number}: broken relative link {target!r}"
                )

    if not index.is_file():
        failures.append("docs/documentation-index.md is missing")
        linked: set[Path] = set()
    else:
        linked = {
            Path(os.path.normpath(os.path.join(index.parent, target)))
            for _, raw in link_targets(index)
            if (target := relative_target(raw)) is not None
        }
    covered = {
        path

[Showing lines 1-300 of 327. Use :301 to continue]
