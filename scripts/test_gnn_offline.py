"""Real offline resource controls, explicitly selected after native setup/review.

Run with GNN_OFFLINE_BUNDLE, its externally expected
GNN_OFFLINE_MANIFEST_SHA256 and GNN_OFFLINE_TEST_TARGET pointing to an actual
fresh local-VCS pip installation of that bundle. Missing prerequisites ERROR,
never skip. These controls neither replace ./run.sh gnn nor accept its verdict.
No fake parser, mocked installer, generated source attestation or network is used.
"""

from __future__ import annotations

import copy
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts import gnn_offline as offline
from scripts import check_gnn_conformance as consumer

ROOT = Path(__file__).resolve().parent.parent
PIN = json.loads((ROOT / ".github" / "gnn-pin.json").read_text(encoding="utf-8"))
CHECKER = ROOT / "scripts" / "check_gnn_conformance.py"


def prepared_bundle():
    bundle = offline.from_environment(PIN)
    if bundle is None:
        raise RuntimeError("real offline controls require GNN_OFFLINE_BUNDLE and GNN_OFFLINE_MANIFEST_SHA256")
    return bundle


def writable_copytree(source: Path, destination: Path):
    """Copy immutable evidence; make only our separate fixture writable."""
    shutil.copytree(source, destination)
    for directory, directories, files in os.walk(destination):
        path = Path(directory)
        path.chmod(path.stat().st_mode | 0o700)
        for name in files:
            copied = path / name
            copied.chmod(copied.stat().st_mode | 0o200)


class OrdinaryFileTests(unittest.TestCase):
    def test_offline_version_probe_does_not_execute_site_startup(self):
        with tempfile.TemporaryDirectory(prefix="gnn-probe-startup-") as directory:
            root = Path(directory).resolve()
            prefix = root / "runtime"
            subprocess.run(
                [sys.executable, "-I", "-S", "-B", "-m", "venv", "--without-pip", str(prefix)],
                stdin=subprocess.DEVNULL, capture_output=True, text=True, check=True,
            )
            executable = prefix / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            probe = subprocess.run(
                [str(executable), "-I", "-B", "-c", "import sysconfig; print(sysconfig.get_path('purelib'))"],
                stdin=subprocess.DEVNULL, capture_output=True, text=True, check=True,
            )
            library = Path(probe.stdout.strip())
            pth_marker, site_marker = root / "pth-executed", root / "site-executed"
            (library / "unexpected.pth").write_text(
                f"import pathlib; pathlib.Path({str(pth_marker)!r}).write_text('executed')\n",
                encoding="utf-8",
            )
            (library / "sitecustomize.py").write_text(
                f"import pathlib; pathlib.Path({str(site_marker)!r}).write_text('executed')\n",
                encoding="utf-8",
            )
            self.assertEqual(consumer.interpreter_version(str(executable), isolated=True), sys.version_info[:3])
            self.assertFalse(pth_marker.exists())
            self.assertFalse(site_marker.exists())

    def test_relative_escape_and_absolute_path_are_rejected(self):
        with tempfile.TemporaryDirectory(prefix="gnn-path-control-") as directory:
            root = Path(directory).resolve()
            (root / "inside").write_bytes(b"actual file")
            self.assertEqual(offline.ordinary_path(root, "inside").read_bytes(), b"actual file")
            for relative in (".", "../inside", "/inside", "nested/../inside", "./inside", "inside\\escape"):
                with self.subTest(relative=relative), self.assertRaises(offline.OfflineError):
                    offline.ordinary_path(root, relative)

    def test_leaf_and_directory_symlinks_are_rejected(self):
        with tempfile.TemporaryDirectory(prefix="gnn-symlink-control-") as directory:
            root = Path(directory).resolve()
            (root / "actual").mkdir()
            (root / "actual" / "file").write_bytes(b"actual file")
            (root / "leaf").symlink_to(root / "actual" / "file")
            (root / "redirected").symlink_to(root / "actual", target_is_directory=True)
            for relative in ("leaf", "redirected/file"):
                with self.subTest(relative=relative), self.assertRaisesRegex(offline.OfflineError, "symlink"):
                    offline.ordinary_path(root, relative)

    def test_partial_and_empty_environment_configuration_errors(self):
        helper = ROOT / "scripts" / "gnn_offline.py"
        program = (
            "import runpy; module=runpy.run_path(" + repr(str(helper)) + "); "
            "module['from_environment'](" + repr(PIN) + ")"
        )
        for names in (
            {"GNN_OFFLINE_BUNDLE": "/nonexistent"},
            {"GNN_OFFLINE_MANIFEST_SHA256": "0" * 64},
            {"GNN_OFFLINE_BUNDLE": "", "GNN_OFFLINE_MANIFEST_SHA256": "0" * 64},
        ):
            environment = {
                key: value for key, value in os.environ.items()
                if key not in ("GNN_OFFLINE_BUNDLE", "GNN_OFFLINE_MANIFEST_SHA256")
            }
            environment.update(names)
            with self.subTest(names=tuple(names)):
                completed = subprocess.run(
                    [sys.executable, "-I", "-S", "-B", "-c", program],
                    stdin=subprocess.DEVNULL, capture_output=True, text=True, env=environment,
                )
                self.assertNotEqual(completed.returncode, 0)
                self.assertIn("must both be nonempty", completed.stderr)

    def test_old_verify_interface_cannot_bypass_offline_install(self):
        environment = dict(os.environ, GNN_OFFLINE_BUNDLE="/nonexistent")
        completed = subprocess.run(
            [sys.executable, "-I", "-S", "-B", str(CHECKER), "--verify", "/nonexistent"],
            stdin=subprocess.DEVNULL, capture_output=True, text=True, env=environment,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("cannot bypass interpreter selection and fresh installation", completed.stderr)


class PreparedResourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = prepared_bundle()  # A real positive resource admission precedes mutations.

    def test_external_manifest_digest_mismatch_is_rejected(self):
        expected = self.bundle.digest
        incorrect = ("0" if expected[0] != "0" else "1") + expected[1:]
        with self.assertRaisesRegex(offline.OfflineError, "manifest digest differs"):
            offline.load_bundle(self.bundle.root, incorrect, PIN)

    def test_actual_wheel_byte_tampering_is_rejected(self):
        record = self.bundle.wheels["pip"]
        with tempfile.TemporaryDirectory(prefix="gnn-wheel-control-") as directory:
            root = Path(directory).resolve()
            wheel = root / record["path"]
            wheel.parent.mkdir(parents=True)
            shutil.copyfile(self.bundle.root / record["path"], wheel)
            self.assertEqual(offline.sha256_file(wheel), record["sha256"])
            with wheel.open("ab") as handle:
                handle.write(b"real negative-control corruption")
            with self.assertRaisesRegex(offline.OfflineError, "wheel digest differs"):
                offline._check_wheels(root, [record])

    def test_installer_rechecks_actual_pip_wheel_digest(self):
        record = self.bundle.wheels["pip"]
        installer = self.bundle.manifest["installer"]
        runtime = self.bundle.manifest["runtime"]
        executable = str(Path(installer["prefix"]) / "bin" / "python")
        with tempfile.TemporaryDirectory(prefix="gnn-installer-wheel-control-") as directory:
            root = Path(directory).resolve()
            wheel = root / record["path"]
            wheel.parent.mkdir(parents=True)
            shutil.copyfile(self.bundle.root / record["path"], wheel)
            self.assertEqual(offline.sha256_file(wheel), record["sha256"])
            bytecode_root = root / "bytecode"
            bytecode_root.mkdir()
            command = offline.installer_command(
                executable, root=root, runtime=runtime, installer=installer,
                pip_wheel=record, bytecode_root=bytecode_root,
            )
            self.assertEqual(command[:4], [executable, "-I", "-S", "-B"])
            self.assertEqual(command[-2], str(bytecode_root))
            # Appended bytes leave ZIP members readable: content comparison alone
            # would accept this changed archive without the point-of-use digest.
            with wheel.open("ab") as handle:
                handle.write(b"real installer-wheel negative-control corruption")
            with self.assertRaisesRegex(offline.OfflineError, "wheel digest differs"):
                offline.installer_command(
                    executable, root=root, runtime=runtime, installer=installer,
                    pip_wheel=record, bytecode_root=bytecode_root,
                )

    def copy_source(self, root):
        record = copy.deepcopy(self.bundle.manifest["source"])
        checkout = root / record["path"]
        checkout.parent.mkdir(parents=True, exist_ok=True)
        writable_copytree(self.bundle.source, checkout)
        for name in ("admission", "identity"):
            relative = record["acquisition"][name]
            destination = root / relative
            if not destination.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(self.bundle.root / relative, destination)
        self.assertEqual(offline._check_source(root, record, PIN), checkout)
        return record, checkout

    def test_incomplete_acquisition_result_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="gnn-acquisition-incomplete-control-") as directory:
            root = Path(directory).resolve()
            record, _ = self.copy_source(root)
            receipt = root / record["acquisition"]["admission"]
            evidence = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(
                evidence["result"],
                "complete-current-pinned-installable-project-acquired-not-built-installed-or-tested",
            )
            self.assertIsNone(evidence.get("error"))
            evidence["result"] = "incomplete"
            receipt.write_text(json.dumps(evidence), encoding="utf-8")
            with self.assertRaisesRegex(offline.OfflineError, "native acquisition evidence is incomplete or failed"):
                offline._check_source(root, record, PIN)

    def test_late_acquisition_error_with_complete_fields_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="gnn-acquisition-error-control-") as directory:
            root = Path(directory).resolve()
            record, _ = self.copy_source(root)
            receipt = root / record["acquisition"]["admission"]
            evidence = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(
                evidence["result"],
                "complete-current-pinned-installable-project-acquired-not-built-installed-or-tested",
            )
            self.assertIsNone(evidence.get("error"))
            evidence["error"] = "deterministic late acquisition failure"
            receipt.write_text(json.dumps(evidence), encoding="utf-8")
            with self.assertRaisesRegex(offline.OfflineError, "native acquisition evidence is incomplete or failed"):
                offline._check_source(root, record, PIN)

    def test_actual_git_origin_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="gnn-origin-control-") as directory:
            root = Path(directory).resolve()
            record, checkout = self.copy_source(root)
            configuration = checkout / ".git" / "config"
            original = configuration.read_text(encoding="utf-8")
            self.assertIn(record["origin"], original)
            configuration.write_text(original.replace(record["origin"], "https://example.invalid/wrong.git"), encoding="utf-8")
            with self.assertRaisesRegex(offline.OfflineError, "different actual origin"):
                offline._check_source(root, record, PIN)

    def test_actual_git_head_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="gnn-commit-control-") as directory:
            root = Path(directory).resolve()
            record, checkout = self.copy_source(root)
            (checkout / ".git" / "HEAD").write_text("0" * 40 + "\n", encoding="ascii")
            with self.assertRaisesRegex(offline.OfflineError, "HEAD differs|inspection failed"):
                offline._check_source(root, record, PIN)

    def test_real_interpreter_rejects_changed_runtime_binding(self):
        changed = copy.copy(self.bundle)
        changed.manifest = copy.deepcopy(self.bundle.manifest)
        executable = str(Path(changed.manifest["installer"]["prefix"]) / "bin" / "python")
        self.bundle.check_runtime(executable)
        changed.manifest["runtime"]["cache_tag"] += "-wrong"
        with self.assertRaisesRegex(offline.OfflineError, "authenticated bundle runtime"):
            changed.check_runtime(executable)
        with tempfile.TemporaryDirectory(prefix="gnn-installer-runtime-control-") as directory:
            with self.assertRaisesRegex(offline.OfflineError, "authenticated bundle runtime"):
                offline.installer_command(
                    executable, root=self.bundle.root, runtime=changed.manifest["runtime"],
                    installer=self.bundle.manifest["installer"], pip_wheel=self.bundle.wheels["pip"],
                    bytecode_root=Path(directory).resolve(),
                )


class InstalledOriginTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = prepared_bundle()
        name = "GNN_OFFLINE_TEST_TARGET"
        if not os.environ.get(name):
            raise RuntimeError(f"real installed-origin controls require {name}: an actual fresh VCS pip target")
        cls.target = Path(os.environ[name])
        distributions, _ = offline.validate_installed(cls.target, cls.bundle)
        cls.distribution = distributions[offline.DISTRIBUTION]
        # The real installed package, not a fixed-result parser fixture, must be
        # byte-identical to the independently trusted package before copying it.
        expected = json.loads(cls.bundle.package_manifest)["files"]
        actual = {
            "src/gnn/" + relative: digest
            for relative, digest in offline._inventory(cls.target / "gnn").items()
            if "__pycache__" not in Path(relative).parts and not relative.endswith((".pyc", ".pyo"))
        }
        if actual != expected:
            raise RuntimeError("real installed-origin prerequisite differs from the trusted 1,225-file package")
        metadata = [item for item in cls.distribution.files if str(item).endswith(".dist-info/METADATA")]
        cls.metadata_directory = Path(cls.distribution.locate_file(metadata[0])).parent

    def copy_install(self, root):
        # Only this real GNN distribution is copied for focused metadata controls;
        # this is not an alternative dependency/install/conformance acceptance arm.
        writable_copytree(self.target / "gnn", root / "gnn")
        destination = root / self.metadata_directory.name
        writable_copytree(self.metadata_directory, destination)
        distributions = list(importlib.metadata.distributions(path=[str(root)]))
        self.assertEqual(len(distributions), 1)
        distribution = distributions[0]
        offline.validate_vcs_origin(root, self.bundle, distribution)
        return distribution, destination / "direct_url.json"

    def test_installed_pep610_url_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="gnn-installed-url-control-") as directory:
            root = Path(directory).resolve()
            distribution, direct_url = self.copy_install(root)
            origin = json.loads(direct_url.read_text(encoding="utf-8"))
            origin["url"] = "file:///wrong/native/source"
            direct_url.write_text(json.dumps(origin), encoding="utf-8")
            with self.assertRaisesRegex(offline.OfflineError, "PEP 610 local URL/VCS commit differs"):
                offline.validate_vcs_origin(root, self.bundle, distribution)

    def test_installed_pep610_commit_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="gnn-installed-commit-control-") as directory:
            root = Path(directory).resolve()
            distribution, direct_url = self.copy_install(root)
            origin = json.loads(direct_url.read_text(encoding="utf-8"))
            origin["vcs_info"]["commit_id"] = "0" * 40
            direct_url.write_text(json.dumps(origin), encoding="utf-8")
            with self.assertRaisesRegex(offline.OfflineError, "PEP 610 local URL/VCS commit differs"):
                offline.validate_vcs_origin(root, self.bundle, distribution)

    def test_real_distribution_outside_target_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="gnn-installed-root-control-") as directory:
            root = Path(directory).resolve()
            with self.assertRaisesRegex(offline.OfflineError, "module root differs"):
                offline.validate_vcs_origin(root, self.bundle, self.distribution)

    def test_installed_module_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="gnn-installed-symlink-control-") as directory:
            root = Path(directory).resolve()
            distribution, _ = self.copy_install(root)
            module = root / "gnn" / "__init__.py"
            module.unlink()
            module.symlink_to(self.target / "gnn" / "__init__.py")
            with self.assertRaisesRegex(offline.OfflineError, "symlink"):
                offline.validate_vcs_origin(root, self.bundle, distribution)


if __name__ == "__main__":
    unittest.main()
