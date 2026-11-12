#!/usr/bin/env python3
"""Unit tests for the pinned GNN arm's fail-closed type check and receipt labels.

The real parser is replaced by fixed-result modules, so these tests need neither
network nor the pinned package.  This is the `tests` arm of ./run.sh.

Run:  ./run.sh tests   (or: python3 -m unittest scripts.test_check_gnn_conformance)
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path

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


class VerifyTests(unittest.TestCase):
    def run_verify(self, outcome, with_sketch):
        calls: list = []
        saved_modules = dict(sys.modules)
        saved_path = list(sys.path)
        saved_root, saved_fetch = module.ROOT, module.fetch
        out, err = io.StringIO(), io.StringIO()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            if with_sketch:
                (root / "m.gnn.md").write_text("## GNNSection\nX\n", encoding="utf-8")
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

    def test_pinned_exemplar_receipt_is_a_baseline(self):
        code, _, stdout, calls = self.run_verify(True, False)
        receipt = json.loads(stdout)
        self.assertEqual(code, 0)
        self.assertEqual(receipt["source"], "pinned-exemplar")
        self.assertEqual(receipt["scope"], "pinned GNN exemplar baseline")
        self.assertEqual(receipt["result"], "pinned-exemplar-baseline-passed")
        self.assertEqual(calls, [True])


if __name__ == "__main__":
    unittest.main()
