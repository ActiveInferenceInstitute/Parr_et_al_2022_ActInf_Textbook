#!/usr/bin/env python3
"""Offline regressions for GNN selection, staging, version constraints and receipts.

Selection and staging use real temporary files and Git indexes. Only the existing
receipt-protocol tests replace the parser with fixed-result modules; those tests
do not qualify the pinned upstream parser or its scientific semantics.

Run:  ./run.sh tests   (or: python3 -m unittest scripts.test_check_gnn_conformance)
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path

from scripts.git_test_support import GitFixtureTests

SCRIPT = Path(__file__).resolve().parent / "check_gnn_conformance.py"
SPEC = importlib.util.spec_from_file_location("check_gnn_conformance", SCRIPT)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class Parsed:
    parse_errors: list = []


def install_fixture(outcome, is_content_calls):
    def validate_gnn_syntax(text, is_content=False):
        is_content_calls.append(is_content)
        return True, []

    class Checker:
        def validate_gnn_files(self, model_dir, output_dir):
            return outcome

    root = types.ModuleType("gnn")
    root.__version__ = module.load_pin()["tag"].removeprefix("v")
    parsers = types.ModuleType("gnn.parsers")
    basic = types.ModuleType("gnn.parsers.basic")
    basic.parse_gnn_formal = lambda path: Parsed()
    basic.validate_gnn_syntax = validate_gnn_syntax
    checking = types.ModuleType("gnn.type_checker")
    checking.GNNTypeChecker = Checker
    return {
        "gnn": root,
        "gnn.parsers": parsers,
        "gnn.parsers.basic": basic,
        "gnn.type_checker": checking,
    }


class VersionTests(unittest.TestCase):
    def test_patch_versions_and_compatible_releases(self):
        cases = [
            ((3, 12, 1), ">=3.12.2", False),
            ((3, 12, 2), ">=3.12.2,<3.13", True),
            ((3, 12, 0), "==3.12", True),
            ((3, 12, 1), "==3.12", False),
            ((3, 12, 1), "!=3.12.1", False),
            ((3, 12, 2), "!=3.12.1", True),
            ((3, 12, 1), "~=3.12.1", True),
            ((3, 12, 99), "~=3.12.1", True),
            ((3, 12, 0), "~=3.12.1", False),
            ((3, 13, 0), "~=3.12.1", False),
            ((3, 99, 0), "~=3.12", True),
            ((4, 0, 0), "~=3.12", False),
            ((3, 12, 1, 5), "~=3.12.1.2", True),
            ((3, 12, 2, 0), "~=3.12.1.2", False),
        ]
        for version, specification, expected in cases:
            with self.subTest(version=version, specification=specification):
                self.assertEqual(module.satisfies(version, specification), expected)

    def test_unsupported_syntax_is_not_a_pass_or_an_ordinary_mismatch(self):
        for specification in (
            "", "garbage", ">=3.11,", "=>3.12", "==3.12.*",
            ">=3.12rc1", "===3.12", "~=3", ">=9,not-a-clause",
        ):
            with self.subTest(specification=specification):
                with self.assertRaises(ValueError):
                    module.satisfies((3, 12, 1), specification)

    def test_numeric_releases_are_complete_and_the_real_probe_keeps_patch_precision(self):
        self.assertEqual(module.version_tuple("3.12.11"), (3, 12, 11))
        self.assertEqual(module.interpreter_version(sys.executable), sys.version_info[:3])
        for malformed in ("Python 3.12.11", "3.12rc1", "3.12.1+local"):
            with self.subTest(malformed=malformed), self.assertRaises(ValueError):
                module.version_tuple(malformed)


class TrackedSourceTests(GitFixtureTests):
    def test_tracked_equal_basenames_reach_distinct_staged_documents(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
            expected = {
                "first/model.gnn.md": b"## GNNSection\nfirst\n",
                "second/model.gnn.md": b"## GNNSection\nsecond\n",
            }
            for name, content in expected.items():
                path = root / name
                path.parent.mkdir()
                path.write_bytes(content)
            (root / ".gitignore").write_text("ignored.gnn.md\n", encoding="utf-8")
            (root / "ignored.gnn.md").write_text("ignored", encoding="utf-8")
            (root / "untracked.gnn.md").write_text("untracked", encoding="utf-8")
            subprocess.run(
                ["git", "-C", str(root), "add", "--", ".gitignore", *expected],
                check=True, capture_output=True,
            )

            selected = module.tracked_sketches(root)
            self.assertEqual([path.relative_to(root).as_posix() for path in selected], list(expected))
            documents = module.stage_documents(selected, root, root / "staged")
            self.assertEqual({name: path.read_bytes() for name, path in documents}, expected)
            self.assertEqual({path.name for _, path in documents}, {"model.gnn.md"})
            self.assertEqual(len({path.parent for _, path in documents}), 2)
            self.assertEqual({name: (root / name).read_bytes() for name in expected}, expected)
            self.assertEqual((root / "ignored.gnn.md").read_text(), "ignored")
            self.assertEqual((root / "untracked.gnn.md").read_text(), "untracked")

    def test_untracked_only_checkout_has_no_repository_sketches(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
            (root / "untracked.gnn.md").write_text("untracked", encoding="utf-8")
            self.assertEqual(module.tracked_sketches(root), [])

    def test_missing_or_replaced_tracked_documents_are_not_an_exemplar_fallback(self):
        for replacement in ("deleted", "symlink"):
            with self.subTest(replacement=replacement), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
                sketch = root / "model.gnn.md"
                sketch.write_text("tracked", encoding="utf-8")
                subprocess.run(
                    ["git", "-C", str(root), "add", "--", sketch.name],
                    check=True, capture_output=True,
                )
                sketch.unlink()
                if replacement == "symlink":
                    other = root / "other.md"
                    other.write_text("not the tracked document", encoding="utf-8")
                    sketch.symlink_to(other)
                with self.assertRaises(SystemExit):
                    module.tracked_sketches(root)


class VerifyTests(GitFixtureTests):
    def run_verify(self, outcome, with_sketch, names=("m.gnn.md",)):
        calls: list = []
        saved_modules = dict(sys.modules)
        saved_path = list(sys.path)
        saved_root, saved_fetch = module.ROOT, module.fetch
        out, err = io.StringIO(), io.StringIO()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
            if with_sketch:
                for name in names:
                    sketch = root / name
                    sketch.parent.mkdir(parents=True, exist_ok=True)
                    sketch.write_text(f"## GNNSection\n{name}\n", encoding="utf-8")
                subprocess.run(
                    ["git", "-C", str(root), "add", "--", *names],
                    check=True, capture_output=True,
                )
            module.ROOT = root
            module.fetch = lambda repository, revision, path: b"## GNNSection\nX\n"
            sys.modules.update(install_fixture(outcome, calls))
            try:
                with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                    try:
                        code = module.verify(directory)
                        message = None
                    except SystemExit as exit_:
                        code, message = 1, str(exit_)
            finally:
                module.ROOT, module.fetch = saved_root, saved_fetch
                sys.path[:] = saved_path
                for name in list(sys.modules):
                    if name not in saved_modules:
                        del sys.modules[name]
                sys.modules.update(saved_modules)
        return code, message, out.getvalue(), calls

    def test_non_true_type_checker_results_fail_closed(self):
        for outcome in (2, False, None, 0):
            for with_sketch in (True, False):
                with self.subTest(outcome=outcome, with_sketch=with_sketch):
                    code, message, stdout, _ = self.run_verify(outcome, with_sketch)
                    self.assertEqual(code, 1)
                    self.assertIn(f"returned {outcome!r}", message)
                    self.assertEqual(stdout, "")

    def test_repository_sketch_receipt(self):
        code, _, stdout, calls = self.run_verify(True, True)
        receipt = json.loads(stdout)
        self.assertEqual(code, 0)
        self.assertEqual(receipt["source"], "repository")
        self.assertEqual(receipt["scope"], "repository sketches")
        self.assertEqual(receipt["result"], "repository-content-passed")
        self.assertEqual(calls, [True])
        self.assertEqual(receipt["documents"], ["m.gnn.md"])
        self.assertEqual(receipt["models"], 1)

    def test_equal_basename_receipt_names_every_checked_source(self):
        names = ("first/model.gnn.md", "second/model.gnn.md")
        code, _, stdout, calls = self.run_verify(True, True, names)
        receipt = json.loads(stdout)
        self.assertEqual(code, 0)
        self.assertEqual(receipt["documents"], list(names))
        self.assertEqual(receipt["models"], 2)
        self.assertEqual(calls, [True, True])

    def test_pinned_exemplar_receipt_is_a_baseline(self):
        code, _, stdout, calls = self.run_verify(True, False)
        receipt = json.loads(stdout)
        self.assertEqual(code, 0)
        self.assertEqual(receipt["source"], "pinned-exemplar")
        self.assertEqual(receipt["scope"], "pinned GNN exemplar baseline")
        self.assertEqual(receipt["result"], "pinned-exemplar-baseline-passed")
        self.assertEqual(calls, [True])
        self.assertEqual(receipt["documents"], [module.EXEMPLAR])
        self.assertEqual(receipt["models"], 1)


if __name__ == "__main__":
    unittest.main()
