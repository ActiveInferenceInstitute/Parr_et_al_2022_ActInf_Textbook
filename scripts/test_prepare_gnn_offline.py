"""Offline setup controls using externally accepted, genuinely installed resources.

Select alongside test_gnn_offline only after the native original arm has retained
its real installation. GNN_OFFLINE_BUNDLE, GNN_OFFLINE_MANIFEST_SHA256 and native
GITVAULT_EXECUTION_OUTPUT are mandatory; missing resources error, never skip.
Temporary stdlib venvs receive the actual registry-bound pip wheel through its
already authenticated genuine installer, with no network or mocked resources.
"""
from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest

from scripts import check_gnn_conformance as consumer
from scripts import gnn_offline as offline
from scripts import prepare_gnn_offline as builder


class PreparedInstallerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = offline.from_environment(consumer.load_pin())
        if cls.bundle is None:
            raise RuntimeError("setup controls require GNN_OFFLINE_BUNDLE and GNN_OFFLINE_MANIFEST_SHA256")
        output = os.environ.get("GITVAULT_EXECUTION_OUTPUT")
        if not output:
            raise RuntimeError("setup controls require native GITVAULT_EXECUTION_OUTPUT")
        cls.output = Path(output)
        if not cls.output.is_absolute() or not cls.output.is_dir() or cls.output.resolve() != cls.output:
            raise RuntimeError("native setup-control output must be a canonical ordinary directory")
        cls.executable = Path(cls.bundle.manifest["installer"]["prefix"]) / "bin" / "python"

    def command(self, executable: Path, runtime: dict, installer: dict) -> list[str]:
        bytecode = Path(tempfile.mkdtemp(prefix="bytecode-", dir=self.root))
        return offline.installer_command(
            str(executable), root=self.bundle.root, runtime=runtime, installer=installer,
            pip_wheel=self.bundle.wheels["pip"], bytecode_root=bytecode,
        )

    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="gnn-setup-startup-", dir=self.output)
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.prefix = self.root / "installer"
        builder.run([
            str(self.executable), "-I", "-S", "-B", "-m", "venv", "--without-pip", str(self.prefix),
        ])
        wheel = self.bundle.wheels["pip"]
        requirements = self.root / "pip-requirements.txt"
        requirements.write_text(
            f"pip=={wheel['version']} --hash=sha256:{wheel['sha256']}\n", encoding="utf-8",
        )
        command = self.command(
            self.executable, self.bundle.manifest["runtime"], self.bundle.manifest["installer"],
        )
        builder.run(command + [
            "--isolated", "install", "--disable-pip-version-check", "--no-index", "--no-cache-dir",
            "--find-links", str(self.bundle.wheelhouse), "--require-hashes", "--no-deps", "--no-compile",
            "--ignore-installed", "--prefix", str(self.prefix), "-r", str(requirements),
        ])
        self.python = self.prefix / "bin" / "python"
        self.runtime, self.installer = builder.inspect_installer(self.python, allowed_parent=self.root)
        self.assertEqual(self.runtime, self.bundle.manifest["runtime"])
        self.assertEqual(self.installer, {"prefix": str(self.prefix), "pip_version": wheel["version"]})
        # A genuine positive admission and real pip execution precede every mutation.
        version = builder.run(self.command(self.python, self.runtime, self.installer) + ["--isolated", "--version"])
        self.assertIn(f"pip {wheel['version']} ", version)
        major, minor, _ = consumer.version_tuple(self.runtime["python"])
        self.library = self.prefix / "lib" / f"python{major}.{minor}" / "site-packages"

    def assert_startup_rejected(self, filename: str):
        marker = self.root / "unchecked-startup-executed"
        (self.library / filename).write_text(
            f"import pathlib; pathlib.Path({str(marker)!r}).write_text('executed')\n", encoding="utf-8",
        )
        runtime, installer = builder.inspect_installer(self.python, allowed_parent=self.root)
        self.assertEqual(runtime, self.runtime)
        self.assertEqual(installer, self.installer)
        self.assertFalse(marker.exists(), "original setup inspection executed site startup")
        with self.assertRaisesRegex(offline.OfflineError, "search root contains files outside"):
            self.command(self.python, runtime, installer)
        self.assertFalse(marker.exists(), "installer authentication executed unchecked startup")

    def test_original_inspection_and_authentication_do_not_execute_pth(self):
        self.assert_startup_rejected("unexpected.pth")

    def test_original_inspection_and_authentication_do_not_execute_sitecustomize(self):
        self.assert_startup_rejected("sitecustomize.py")

    def test_real_pip_code_tampering_is_rejected_before_execution(self):
        marker = self.root / "unchecked-pip-executed"
        module = self.library / "pip" / "__main__.py"
        original = module.read_text(encoding="utf-8")
        module.write_text(
            f"import pathlib; pathlib.Path({str(marker)!r}).write_text('executed')\n" + original,
            encoding="utf-8",
        )
        runtime, installer = builder.inspect_installer(self.python, allowed_parent=self.root)
        with self.assertRaisesRegex(offline.OfflineError, "installed dependency content differs"):
            self.command(self.python, runtime, installer)
        self.assertFalse(marker.exists(), "setup executed pip before authenticating its bytes")

    def test_temporary_venv_cannot_use_production_parent(self):
        with self.assertRaisesRegex(ValueError, "canonical task-owned environment"):
            builder.inspect_installer(self.python, allowed_parent=builder.ROOT / ".gnn-env")

    def test_seal_bootstrap_uses_exact_retained_registry_proof(self):
        wheel = self.bundle.wheels["pip"]
        registry = self.bundle.root / wheel["registry"]
        before = registry.read_bytes()
        retained = builder.pip_bootstrap(
            self.bundle.root, self.bundle.root / "proof", wheel["version"], retained=True,
        )
        self.assertEqual(retained, wheel)
        self.assertEqual(registry.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
