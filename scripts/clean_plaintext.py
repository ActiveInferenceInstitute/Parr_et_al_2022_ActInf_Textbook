#!/usr/bin/env python3
"""Deterministic cleaner for TextbookContent/PlainText/*.txt.

Recognized removable material is limited to MIT Press download footers and
explicit decimal pagination labels: ``Page N`` or ``Page N of M`` (case-insensitive,
positive integers). A bare integer, roman numeral, ``x``, or ``i`` is not evidence
of pagination, even when surrounded by blank lines or at a page boundary.

The cleaner also wraps long lines independently, collapses blank runs, and strips
trailing whitespace. It never merges neighbouring nonblank lines.

The non-whitespace count check accounts for recognized removals and wrapping.
It is a mechanical invariant, not proof of scientific fidelity or evidence that
any existing corpus was damaged. Regeneration remains a separately reviewed step.

Usage:
  python3 scripts/clean_plaintext.py            # report only (no writes)
  python3 scripts/clean_plaintext.py --apply    # write cleaned files in place
"""

import argparse
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TXT_DIR = os.path.join(ROOT, "TextbookContent", "PlainText")
GLOB = os.path.join(TXT_DIR, "*.txt")

FOOTER_RE = re.compile(r"^Downloaded from http://direct\.mit\.edu/.+ by guest on .+$")
PAGENUM_RE = re.compile(r"^Page [1-9][0-9]*(?: of [1-9][0-9]*)?$", re.IGNORECASE)

MAX_LINE = 110   # lines strictly longer than this get wrapped
WRAP = 100       # wrap width


def wrap_long_line(line: str) -> list:
    """Wrap one line unless a chunk would become removable on the next pass."""
    if len(line) <= MAX_LINE:
        return [line]
    words = line.split()
    out, cur = [], ""
    for w in words:
        if not cur:
            cur = w
        elif len(cur) + 1 + len(w) <= WRAP:
            cur += " " + w
        else:
            out.append(cur)
            cur = w
    if cur:
        out.append(cur)
    # A prose reference must not become pagination/footer evidence after wrapping.
    if any(PAGENUM_RE.fullmatch(chunk) or FOOTER_RE.match(chunk) for chunk in out):
        return [line]
    return out



def clean_text(text: str):
    lines = text.split("\n")
    kept = []
    removed_footer = removed_pagenum = 0
    removed_chars = 0
    for raw in lines:
        s = raw.strip()
        if FOOTER_RE.match(s):
            removed_footer += 1
            removed_chars += count_nonws(s)
            continue
        if PAGENUM_RE.fullmatch(s):
            removed_pagenum += 1
            removed_chars += count_nonws(s)
            continue
        kept.append(raw.rstrip())

    # wrap long prose lines (independent, no cross-line merge)
    wrapped = []
    for ln in kept:
        if ln.strip():
            wrapped.extend(wrap_long_line(ln))
        else:
            wrapped.append("")

    # collapse blank runs to a single blank line
    final = []
    for ln in wrapped:
        if ln.strip() == "":
            if final and final[-1].strip() == "":
                continue
            final.append("")
        else:
            final.append(ln)

    cleaned = "\n".join(final).rstrip("\n") + "\n"
    return cleaned, removed_footer, removed_pagenum, removed_chars


def count_nonws(s):
    return sum(1 for ch in s if not ch.isspace())


def process(path, apply):
    with open(path, encoding="utf-8-sig") as source:
        raw = source.read()
    cleaned, nf, np_, nc = clean_text(raw)

    # integrity: cleaned must contain exactly (raw - removed line chars) non-ws chars
    base = count_nonws(raw) - nc
    got = count_nonws(cleaned)
    ok = (got == base)

    fn = os.path.basename(path)
    print(f"{fn:26s} footer={nf:3d} pagenum={np_:3d} "
          f"nonws {count_nonws(raw):7d}->{got:7d} (expect {base:7d}) "
          f"{'OK' if ok else 'MISMATCH!'}")
    if not ok:
        return False
    if apply:
        with open(path, "w", encoding="utf-8") as f:
            f.write(cleaned)
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true",
                    help="write cleaned files in place (default: report only)")
    args = ap.parse_args()

    paths = sorted(glob.glob(GLOB))
    if not paths:
        print(f"no .txt files found in {TXT_DIR}")
        sys.exit(1)

    all_ok = True
    for p in paths:
        if not process(p, args.apply):
            all_ok = False

    print(f"\n{len(paths)} file(s) processed. "
          + ("ALL INTEGRITY CHECKS PASSED." if all_ok else "INTEGRITY FAILURES DETECTED — no files were written for failed ones."))
    sys.exit(0 if all_ok else 2)


if __name__ == "__main__":
    main()
