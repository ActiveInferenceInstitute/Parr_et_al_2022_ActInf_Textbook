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
import sys
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


    def assert_sourceless_rejected(self, relative: str):
        marker = self.root / "unchecked-bytecode-executed"
        source = self.root / "bytecode-control.py"
        source.write_text(
            f"import pathlib; pathlib.Path({str(marker)!r}).write_text('executed')\n", encoding="utf-8",
        )
        bytecode = self.library / relative
        bytecode.parent.mkdir(parents=True, exist_ok=True)
        builder.run([
            str(self.python), "-I", "-S", "-B", "-c",
            "import py_compile,sys; py_compile.compile(sys.argv[1], cfile=sys.argv[2], doraise=True)",
            str(source), str(bytecode),
        ])
        source.unlink()
        with self.assertRaisesRegex(offline.OfflineError, "search root contains files outside"):
            self.command(self.python, self.runtime, self.installer)
        self.assertFalse(marker.exists(), "installer authentication executed sourceless code")

    def test_sourceless_standard_library_override_is_rejected(self):
        self.assert_sourceless_rejected("logging.pyc")

    def test_sourceless_package_override_is_rejected(self):
        self.assert_sourceless_rejected("logging/__init__.pyc")

    def test_real_pip_configuration_cannot_delegate_or_redirect_setup(self):
        alternate = self.root / "unauthenticated-runtime"
        destination = self.root / "declared-destination"
        for prefix in (alternate, destination):
            builder.run([
                str(self.python), "-I", "-S", "-B", "-m", "venv", "--without-pip", str(prefix),
            ])
        major, minor, _ = consumer.version_tuple(self.runtime["python"])
        alternate_library = alternate / "lib" / f"python{major}.{minor}" / "site-packages"
        markers = [self.root / "delegated-pth-executed", self.root / "delegated-site-executed"]
        for filename, marker in zip(("unexpected.pth", "sitecustomize.py"), markers):
            (alternate_library / filename).write_text(
                f"import pathlib; pathlib.Path({str(marker)!r}).write_text('executed')\n", encoding="utf-8",
            )
        redirected = self.root / "undeclared-destination"
        configuration = self.root / "pip.conf"
        configuration.write_text(
            f"[global]\npython = {alternate / 'bin' / 'python'}\n[install]\ntarget = {redirected}\n",
            encoding="utf-8",
        )
        wheel = self.bundle.wheels["pip"]
        requirements = self.root / "controlled-pip-requirements.txt"
        requirements.write_text(
            f"pip=={wheel['version']} --hash=sha256:{wheel['sha256']}\n", encoding="utf-8",
        )
        hostile = {
            "PIP_CONFIG_FILE": str(configuration), "PIP_PYTHON": str(alternate / "bin" / "python"),
            "PIP_TARGET": str(redirected), "PIP_PREFIX": str(redirected),
        }
        previous = {name: os.environ.get(name) for name in hostile}
        os.environ.update(hostile)
        observed = []
        observing = True

        def observe_launch(event, arguments):
            if observing and event == "subprocess.Popen" and isinstance(arguments[3], dict):
                observed.append(arguments[3])

        sys.addaudithook(observe_launch)
        try:
            builder.run(self.command(self.python, self.runtime, self.installer) + [
                "--isolated", "install", "--disable-pip-version-check", "--no-index", "--no-cache-dir",
                "--find-links", str(self.bundle.wheelhouse), "--require-hashes", "--no-deps", "--no-compile",
                "--ignore-installed", "--prefix", str(destination), "-r", str(requirements),
            ])
        finally:
            observing = False
            for name, value in previous.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value
        self.assertEqual(len(observed), 1, "expected the real authenticated pip installation launch")
        self.assertEqual(observed[0]["PIP_CONFIG_FILE"], os.devnull)
        bindings = ("PIP_CACHE_DIR", "UV_CACHE_DIR", "TMPDIR", "TEMP", "UV_LINK_MODE")
        for name in bindings:
            self.assertIn(name, os.environ, "native setup controls require declared installer bindings")
            self.assertTrue(observed[0].get(name) == os.environ[name], f"lost declared {name} binding")
        self.assertTrue(
            all(observed[0].get(name) == value for name, value in os.environ.items() if name.startswith("GITVAULT_")),
            "setup lost an inherited native guard binding",
        )
        python = destination / "bin" / "python"
        runtime, installer = builder.inspect_installer(python, allowed_parent=self.root)
        version = builder.run(self.command(python, runtime, installer) + ["--isolated", "--version"])
        self.assertIn(str(destination / "lib" / f"python{major}.{minor}" / "site-packages"), version)
        self.assertFalse(redirected.exists())
        for marker in markers:
            self.assertFalse(marker.exists(), "setup delegated to unauthenticated site-enabled Python")


if __name__ == "__main__":
    unittest.main()
