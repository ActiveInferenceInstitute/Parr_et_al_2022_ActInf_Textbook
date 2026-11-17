#!/usr/bin/env python3
"""Real-file Markdown destination and documentation-gate regressions; no network."""

from __future__ import annotations

import contextlib
import io
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.check_docs import link_targets, main, relative_target
from scripts.git_test_support import GitFixtureTests, require_safe_git_environment


class DestinationTests(unittest.TestCase):
    def targets(self, text: str) -> list[tuple[int, str | None]]:
        with tempfile.TemporaryDirectory() as directory:
            document = Path(directory) / "source.md"
            document.write_text(text, encoding="utf-8")
            return [(line, relative_target(raw)) for line, raw in link_targets(document)]

    def test_destinations_are_separate_from_all_three_title_forms(self):
        text = (
            '[angle](<angle path.md> "Not [a link](ghost.md)")\n'
            "[nested](nested(one(two)).md#section 'Title')\n"
            r"[escaped](escaped\(one\).md (Title))" "\n"
            '[ordinary](plain.md "Title with a \\\"quote\\\"")\n'
            '[empty]( "Title only")\n'
            r"[label with \] bracket](plain.md)" "\n"
        )
        self.assertEqual(self.targets(text), [
            (1, "angle path.md"), (2, "nested(one(two)).md"),
            (3, "escaped(one).md"), (4, "plain.md"),
            (5, None), (6, "plain.md"),
        ])

    def test_reference_definitions_allow_angles_titles_and_continuations(self):
        text = (
            '[one]: <reference path.md> "Not [a link](ghost.md)"\n'
            "[two]: nested(one(two)).md 'Title'\n"
            r"[escaped\]label]: escaped\(one\).md (Title)" "\n"
            '[continued]:\n  <continued path.md>\n'
            '  "Not [a link](another-ghost.md)"\n'
            '[one] and [other label][two] and ![one][]\n'
        )
        self.assertEqual(self.targets(text), [
            (1, "reference path.md"), (2, "nested(one(two)).md"),
            (3, "escaped(one).md"), (4, "continued path.md"),
        ])

    def test_angle_destination_spaces_are_not_silently_trimmed(self):
        self.assertEqual(
            self.targets('[spaces](< leading and trailing.md > "Title")\n'),
            [(1, " leading and trailing.md ")],
        )

    def test_urls_decode_after_fragment_and_query_separation(self):
        text = (
            '[encoded](a%20b%23c%3Fd.md?download=1#part)\n'
            '[entity](a&amp;b.md)\n'
            '[fragment](#section)\n'
            '[remote](https://example.invalid/file.md "remote")\n'
            '[protocol-relative](//example.invalid/file.md)\n'
            '[mail](mailto:someone@example.invalid)\n'
        )
        self.assertEqual(self.targets(text), [
            (1, "a b#c?d.md"), (2, "a&b.md"),
            (3, None), (4, None), (5, None), (6, None),
        ])

    def test_fences_require_matching_character_and_sufficient_length(self):
        text = (
            '````markdown\n[hidden](missing-1.md)\n'
            '```\n[hidden](missing-2.md)\n'
            '~~~\n[hidden](missing-3.md)\n'
            '````\n[visible](one.md)\n'
            '~~~ markdown\n[hidden]: missing-4.md\n'
            '```\n[hidden](missing-5.md)\n'
            '~~~~\n[visible](two.md)\n'
        )
        self.assertEqual(self.targets(text), [(8, "one.md"), (14, "two.md")])

    def test_code_spans_and_escaped_labels_do_not_introduce_links(self):
        text = (
            '`[hidden](missing-1.md)` '
            '``[hidden](missing-2.md) ``` still code`` '
            r'\[escaped](missing-3.md) [visible](real.md)' '\n'
        )
        self.assertEqual(self.targets(text), [(1, "real.md")])

    def test_code_spans_do_not_cross_paragraph_boundaries(self):
        self.assertEqual(
            self.targets("`open\n\n[broken](missing.md)\n\n`close\n"),
            [(3, "missing.md")],
        )
        self.assertEqual(self.targets("`open\n[hidden](missing.md) close`\n"), [])

    def test_code_spans_stop_at_nonblank_block_interruptions(self):
        for interruption in (
            "# Heading", "#", "###", "> quotation", "- list item", "1. list item",
            "---", "===", "<div>",
        ):
            with self.subTest(interruption=interruption):
                text = f"`open\n{interruption}\n[broken](missing.md)\n`close\n"
                self.assertEqual(self.targets(text), [(3, "missing.md")])
        self.assertEqual(
            self.targets("# `open\n[broken](missing.md)\n`close\n"),
            [(2, "missing.md")],
        )
        self.assertEqual(
            self.targets("`open\n2. [example](missing.md) close`\n"), [],
        )

    def test_only_complete_markdown_entities_are_decoded(self):
        for raw, expected in (
            ("notes&copy.md", "notes&copy.md"),
            ("notes&copy;.md", "notes©.md"),
            ("notes&notit;.md", "notes&notit;.md"),
            ("notes&#65.md", "notes&"),
            ("notes&#65;.md", "notesA.md"),
            ("notes&#x41;.md", "notesA.md"),
        ):
            with self.subTest(raw=raw):
                self.assertEqual(self.targets(f"[page]({raw})\n"), [(1, expected)])


class FixtureEnvironmentTests(unittest.TestCase):
    def test_repository_and_object_selectors_are_refused(self):
        for name in (
            "GIT_DIR", "GIT_COMMON_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE",
            "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
            "GIT_CONFIG_COUNT", "GIT_CONFIG_GLOBAL", "GIT_TRACE", "GIT_SSH_COMMAND",
        ):
            with self.subTest(name=name), self.assertRaises(RuntimeError):
                require_safe_git_environment({name: "/outside/fixture"})
        require_safe_git_environment({
            "GIT_OPTIONAL_LOCKS": "0", "GIT_PAGER": "cat",
            "GIT_CEILING_DIRECTORIES": "/outside/fixture",
        })


class DocumentationGateTests(GitFixtureTests):
    def repository(self, root: Path) -> None:
        files = {
            "README.md": '[Hub](docs/README.md "Documentation")\n',
            "docs/README.md": "[Index](documentation-index.md 'Index')\n",
            "docs/documentation-index.md": (
                '[Hub](README.md "Hub")\n'
                '[Page](<page (one).md> "Page")\n'
                r'[Escaped](escaped\(parent\).md)' '\n'
                '[Encoded](encoded%23name.md#part)\n'
            ),
            "docs/page (one).md": '![Plot](../assets/plot(one).svg (Diagram))\n',
            "docs/escaped(parent).md": '````\n[not a link](absent.md)\n```\n````\n',
            "docs/encoded#name.md": '# Part\n',
            "assets/plot(one).svg": '<svg xmlns="http://www.w3.org/2000/svg"/>\n',
        }
        for name, text in files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(root), "add", "."], check=True, capture_output=True)

    def run_gate(self, root: Path) -> tuple[int, str]:
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            result = main(root)
        return result, output.getvalue()

    def test_real_files_and_documentation_coverage_accept_valid_destinations(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.repository(root)
            code, output = self.run_gate(root)
            self.assertEqual(code, 0, output)

    def test_actual_missing_links_still_fail_with_source_location(self):
        for link in (
            '[missing](<missing-link.md> "Title")',
            '[missing]: missing-link.md "Title"',
        ):
            with self.subTest(link=link), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self.repository(root)
                (root / "README.md").write_text(link + "\n", encoding="utf-8")
                code, output = self.run_gate(root)
                self.assertEqual(code, 1, output)
                self.assertIn("README.md:1: broken relative link 'missing-link.md'", output)


if __name__ == "__main__":
    unittest.main()
