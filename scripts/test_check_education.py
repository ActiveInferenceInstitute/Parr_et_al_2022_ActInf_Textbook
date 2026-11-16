#!/usr/bin/env python3
"""Education consumer regressions using the real, explicitly selected producer.

AdapterTests are hermetic admission controls included in ./run.sh tests.
MemberContractTests require COURSES_ROOT with the qualified explicit-repo_root API;
missing prerequisites are errors, never skips. They run in ./run.sh education.
No producer implementation or schema validator is fabricated in these tests.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts import check_education as adapter

SCRIPT = Path(adapter.__file__).resolve()


def invoke(arguments: list[str], environment: dict[str, str], cwd: Path) -> subprocess.CompletedProcess:
    environment = dict(environment, PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run(
        [sys.executable, "-B", str(SCRIPT), *arguments],
        cwd=cwd, env=environment, text=True, capture_output=True,
    )


class AdapterTests(unittest.TestCase):
    def test_missing_explicit_source_is_a_cli_failure_not_a_skip(self):
        environment = dict(os.environ)
        environment.pop("COURSES_ROOT", None)
        with tempfile.TemporaryDirectory() as directory:
            result = invoke([], environment, Path(directory))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")

    def test_unavailable_source_is_a_cli_failure_not_a_skip(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = invoke(["--courses-root", str(root / "missing")], dict(os.environ), root)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")

    def test_explicit_source_without_checker_does_not_use_an_installed_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = invoke(["--courses-root", str(root)], dict(os.environ), root)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")


class MemberContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source_root = adapter.courses_root()

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.workspace = Path(temporary.name)
        self.member = self.workspace / "isolated-worktree-not-the-registry-id"
        self.member.mkdir()
        self.pointer_path = self.member / "education-contract.json"
        self.pointer = json.loads((adapter.ROOT / "education-contract.json").read_text(encoding="utf-8"))
        self.bundles = list(self.pointer["bundles"])
        for name in ("education-contract.json", "specs/education/schema.json", *self.bundles):
            destination = self.member / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(adapter.ROOT / name, destination)

    def write_json(self, path: Path, document) -> None:
        path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")

    def check(self) -> dict:
        return adapter.check_education(self.source_root, self.member)

    def assert_diverged(self, receipt: dict, issue_code: str | None = None) -> None:
        self.assertFalse(receipt["ok"], receipt)
        self.assertEqual(receipt["state"], "diverged", receipt)
        self.assertTrue(receipt["issues"], receipt)
        if issue_code is not None:
            self.assertIn(issue_code, [issue["code"] for issue in receipt["issues"]], receipt)

    def test_real_member_with_empty_glossary_passes_under_a_different_checkout_name(self):
        for name in self.bundles:
            path = self.member / name
            bundle = json.loads(path.read_text(encoding="utf-8"))
            bundle["glossary"] = []
            self.write_json(path, bundle)
        receipt = self.check()
        self.assertTrue(receipt["ok"], receipt)
        self.assertEqual(receipt["state"], "adopted")
        self.assertEqual(receipt["member_id"], adapter.MEMBER_ID)
        self.assertEqual(receipt["repository"], adapter.MEMBER_REPOSITORY)
        self.assertEqual(receipt["member_checkout"], str(self.member.resolve()))
        self.assertEqual(receipt["declared_bundles"], self.bundles)

    def test_pointer_digest_drift_is_rejected(self):
        self.pointer["schema_sha256"] = "0" * 64
        self.write_json(self.pointer_path, self.pointer)
        self.assert_diverged(self.check(), "EC203")

    def test_json_equivalent_but_nonidentical_schema_bytes_are_rejected(self):
        schema = self.member / "specs/education/schema.json"
        schema.write_bytes(schema.read_bytes() + b"\n")
        self.assert_diverged(self.check(), "EC205")

    def test_missing_pointer_is_rejected(self):
        self.pointer_path.unlink()
        self.assert_diverged(self.check(), "EC201")

    def test_malformed_pointer_json_is_rejected(self):
        self.pointer_path.write_text("{", encoding="utf-8")
        self.assert_diverged(self.check(), "EC202")

    def test_nonobject_pointer_is_rejected_without_a_consumer_validator(self):
        self.write_json(self.pointer_path, [])
        self.assert_diverged(self.check())

    def test_malformed_bundle_json_is_rejected(self):
        (self.member / self.bundles[0]).write_text("{", encoding="utf-8")
        self.assert_diverged(self.check(), "EC207")

    def test_structurally_invalid_bundle_is_rejected(self):
        self.write_json(self.member / self.bundles[0], {})
        self.assert_diverged(self.check())

    def test_producer_semantic_rules_are_not_bypassed(self):
        path = self.member / self.bundles[0]
        bundle = json.loads(path.read_text(encoding="utf-8"))
        bundle["units"].append(bundle["units"][0])
        self.write_json(path, bundle)
        self.assert_diverged(self.check(), "EC101")

    def test_invalid_second_bundle_cannot_hide_behind_a_valid_first_bundle(self):
        second = "specs/education/invalid-second.json"
        self.write_json(self.member / second, {})
        self.pointer["bundles"].append(second)
        self.write_json(self.pointer_path, self.pointer)
        receipt = self.check()
        self.assert_diverged(receipt)
        self.assertEqual(receipt["declared_bundles"], self.bundles + [second])
        self.assertTrue(any(issue["location"].startswith(second + ":") for issue in receipt["issues"]), receipt)

    def test_missing_second_bundle_is_rejected(self):
        self.pointer["bundles"].append("specs/education/missing.json")
        self.write_json(self.pointer_path, self.pointer)
        self.assert_diverged(self.check(), "EC206")

    def test_declared_bundle_outside_actual_checkout_is_rejected(self):
        outside = self.workspace / "outside.json"
        shutil.copyfile(self.member / self.bundles[0], outside)
        self.pointer["bundles"].append("../outside.json")
        self.write_json(self.pointer_path, self.pointer)
        self.assert_diverged(self.check(), "EC207")

    def test_pending_and_unavailable_members_are_failures_not_skips(self):
        empty = self.workspace / "empty-member"
        empty.mkdir()
        for checkout, expected_state in ((empty, "pending"), (self.workspace / "absent", "unavailable")):
            with self.subTest(state=expected_state):
                receipt = adapter.check_education(self.source_root, checkout)
                self.assertEqual(receipt["state"], expected_state)
                self.assertFalse(receipt["ok"], receipt)

    def test_cli_uses_the_explicit_producer_and_actual_checkout(self):
        environment = dict(os.environ, COURSES_ROOT=str(self.source_root))
        result = invoke(["--member-checkout", str(self.member)], environment, self.workspace)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        receipt = json.loads(result.stdout)
        self.assertTrue(receipt["ok"], receipt)
        self.assertEqual(receipt["courses_root"], str(self.source_root))
        self.assertEqual(receipt["member_checkout"], str(self.member.resolve()))
        self.assertEqual(receipt["member_id"], adapter.MEMBER_ID)

    def test_invalid_member_cli_exits_nonzero_with_the_producer_diagnostics(self):
        self.pointer["schema_sha256"] = "0" * 64
        self.write_json(self.pointer_path, self.pointer)
        environment = dict(os.environ, COURSES_ROOT=str(self.source_root))
        result = invoke(["--member-checkout", str(self.member)], environment, self.workspace)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assert_diverged(json.loads(result.stdout), "EC203")


if __name__ == "__main__":
    unittest.main()
