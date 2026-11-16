#!/usr/bin/env python3
"""Conservative plaintext cleaning on real strings and temporary files."""

from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from scripts.clean_plaintext import clean_text, count_nonws, process


class CleanerTests(unittest.TestCase):
    def test_ambiguous_mathematical_lines_are_retained(self):
        for token in ("x", "i", "iv", "mix", "X", "IV", "0", "12", "999", "1000"):
            with self.subTest(token=token):
                original = f"Derivation\n\n{token}\n\nExplanation\n"
                cleaned, footers, pages, removed = clean_text(original)
                self.assertEqual(cleaned, original)
                self.assertEqual((footers, pages, removed), (0, 0, 0))
                boundary = f"{token}\n\nBody\n\n{token}\n"
                self.assertEqual(clean_text(boundary)[0], boundary)

    def test_only_explicit_pagination_and_recognized_footers_are_removed(self):
        footer = (
            "Downloaded from http://direct.mit.edu/books/chapter-pdf/example "
            "by guest on 01 January 2022"
        )
        removed_lines = ["Page 12", "page 13 of 100", footer]
        original = "\n".join(["Derivation", *removed_lines, "x", "Explanation", ""])
        cleaned, footers, pages, removed = clean_text(original)
        self.assertEqual(cleaned, "Derivation\nx\nExplanation\n")
        self.assertEqual((footers, pages), (1, 2))
        self.assertEqual(removed, sum(count_nonws(line) for line in removed_lines))
        self.assertEqual(count_nonws(original) - removed, count_nonws(cleaned))

    def test_page_mentions_and_unrecognized_downloads_are_content(self):
        original = (
            "See Page 12 for the derivation.\n"
            "Page x\n"
            "Downloaded from https://example.org/book by guest on Monday\n"
        )
        self.assertEqual(clean_text(original), (original, 0, 0, 0))

    def test_cleaning_is_idempotent_and_preserves_retained_character_order(self):
        prose = " ".join(["probability", "and", "inference"] * 12)
        original = f"Page 12\n\n{prose}   \n\n\nx\n\nExplanation\n"
        cleaned, _, _, _ = clean_text(original)
        again, footers, pages, removed = clean_text(cleaned)
        self.assertEqual(again, cleaned)
        self.assertEqual((footers, pages, removed), (0, 0, 0))
        expected = prose + "xExplanation"
        self.assertEqual(
            "".join(character for character in cleaned if not character.isspace()),
            "".join(character for character in expected if not character.isspace()),
        )

    def test_wrapping_does_not_create_removable_lines(self):
        footer = "Downloaded from http://direct.mit.edu/book by guest on Monday"
        for marker in ("Page 12", "page 13 of 100", footer):
            for prose in (
                ("derivation " * 18) + marker,
                marker + " " + ("z" * 95 + " ") * 2,
                ("derivation " * 18) + marker + " " + "z" * 95,
            ):
                with self.subTest(marker=marker, prose=prose):
                    original = prose.rstrip() + "\n"
                    cleaned, footers, pages, removed = clean_text(original)
                    self.assertEqual((footers, pages, removed), (0, 0, 0))
                    self.assertEqual(clean_text(cleaned), (cleaned, 0, 0, 0))
                    self.assertEqual(
                        "".join(original.split()), "".join(cleaned.split()),
                    )

    def test_report_only_preserves_original_file_bytes(self):
        original = b"\xef\xbb\xbfDerivation\r\n\r\nx\r\n\r\nPage 12\r\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.txt"
            path.write_bytes(original)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertTrue(process(path, apply=False))
            self.assertEqual(path.read_bytes(), original)

    def test_apply_changes_only_the_explicitly_supplied_temporary_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.txt"
            other = Path(directory) / "other.txt"
            path.write_text("Derivation\n\nx\n\nPage 12\nExplanation\n", encoding="utf-8")
            other.write_text("Page 99\n", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertTrue(process(path, apply=True))
            self.assertEqual(path.read_text(encoding="utf-8"), "Derivation\n\nx\n\nExplanation\n")
            self.assertEqual(other.read_text(encoding="utf-8"), "Page 99\n")


if __name__ == "__main__":
    unittest.main()
