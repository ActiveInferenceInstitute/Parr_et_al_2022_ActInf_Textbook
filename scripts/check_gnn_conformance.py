#!/usr/bin/env python3
"""Pinned GNN conformance check (the `gnn` arm of ./run.sh).

`.github/gnn-pin.json` (schema `gnn-importer-pin/v1`) is the only source for the
pinned repository, tag and revision. This script

1. validates the pin document;
2. reads the pinned revision's `requires-python` and picks an interpreter that
   satisfies it (the host default `python3` may not);
3. installs that parser into a throwaway directory, leaving the current
   environment untouched;
4. verifies the installed version equals the pin's tag and that every tracked
   `*.gnn.md` sketch, or - when the repository has none - the pinned upstream
   `input/gnn_files/basics/static_perception.md` exemplar, parses and
   type-checks.

The type checker returns True when every file validates, 2 when files are
invalid or none were found, and False on a hard failure; only True passes.

It prints one JSON receipt whose `scope` and `result` depend on the source:
`repository sketches` / `repository-content-passed`, or `pinned GNN exemplar
baseline` / `pinned-exemplar-baseline-passed` (the pipeline and pin work, but
no repository content was checked). By default it needs network access (pip
and raw.githubusercontent.com). Explicit externally authenticated offline
resources retain the same fresh installation and original verdict scope.

Run:  ./run.sh gnn   (or: python3 scripts/check_gnn_conformance.py)
"""

from __future__ import annotations

import contextlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PIN_PATH = ROOT / ".github" / "gnn-pin.json"
SCHEMA = "gnn-importer-pin/v1"
EXEMPLAR = "input/gnn_files/basics/static_perception.md"
RECEIPTS = {
    "repository": ("repository sketches", "repository-content-passed"),
    "pinned-exemplar": ("pinned GNN exemplar baseline", "pinned-exemplar-baseline-passed"),
}
CANDIDATES = ("python3", "python3.14", "python3.13", "python3.12", "python3.11")
REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
TAG_RE = re.compile(r"^v[0-9]")
REQUIRES_RE = re.compile(r'^requires-python\s*=\s*"([^"]+)"', re.MULTILINE)


def load_pin() -> dict:
    try:
        pin = json.loads(PIN_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"gnn: cannot read {PIN_PATH.relative_to(ROOT)}: {exc}")
    if pin.get("schema") != SCHEMA:
        raise SystemExit(f"gnn: pin schema {pin.get('schema')!r} is not {SCHEMA!r}")
    repository, revision, tag = pin.get("repository"), pin.get("revision"), pin.get("tag")
    if not isinstance(repository, str) or repository.count("/") != 1:
        raise SystemExit(f"gnn: pin repository {repository!r} is not OWNER/REPO")
    if not isinstance(revision, str) or not REVISION_RE.match(revision):
        raise SystemExit(f"gnn: pin revision {revision!r} is not a full 40-character commit id")
    if not isinstance(tag, str) or not TAG_RE.match(tag):
        raise SystemExit(f"gnn: pin tag {tag!r} is not a v-prefixed release tag")
    return pin


def fetch(repository: str, revision: str, path: str) -> bytes:
    url = f"https://raw.githubusercontent.com/{repository}/{revision}/{path}"
    with urllib.request.urlopen(url, timeout=60) as response:
        return response.read()


def version_tuple(text: str) -> tuple[int, ...]:
    """Read a numeric release without discarding patch or later components."""
    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+)*", text):
        raise ValueError(f"unsupported numeric release {text!r}")
    return tuple(int(part) for part in text.split("."))


def parse_requires_python(spec: str) -> list[tuple[str, tuple[int, ...]]]:
    """Parse the supported numeric specifier subset, rejecting every unknown clause."""
    clauses: list[tuple[str, tuple[int, ...]]] = []
    for clause in spec.split(","):
        match = re.fullmatch(r"(>=|<=|==|!=|~=|>|<)\s*([0-9]+(?:\.[0-9]+)*)", clause.strip())
        if match is None:
            raise ValueError(f"unsupported requires-python clause {clause!r}")
        operator, bound_text = match.groups()
        bound = version_tuple(bound_text)
        if operator == "~=" and len(bound) < 2:
            raise ValueError(f"compatible release requires at least major.minor: {clause!r}")
        clauses.append((operator, bound))
    return clauses


def satisfies(version: tuple[int, ...], spec: str) -> bool:
    """Compare complete numeric releases, including PEP 440 compatible-release bounds."""
    clauses = parse_requires_python(spec)
    for operator, bound in clauses:
        width = max(len(version), len(bound))
        left = version + (0,) * (width - len(version))
        right = bound + (0,) * (width - len(bound))
        if operator == ">=" and not left >= right:
            return False
        if operator == "<=" and not left <= right:
            return False
        if operator == ">" and not left > right:
            return False
        if operator == "<" and not left < right:
            return False
        if operator == "==" and left != right:
            return False
        if operator == "!=" and left == right:
            return False
        if operator == "~=":
            prefix = bound[:-1]
            upper = prefix[:-1] + (prefix[-1] + 1,)
            upper += (0,) * (width - len(upper))
            if not right <= left < upper:
                return False
    return True


def interpreter_version(executable: str, *, isolated: bool = False) -> tuple[int, ...] | None:
    arguments = ("-I", "-S", "-B") if isolated else ()
    try:
        completed = subprocess.run(
            [executable, *arguments, "-c", "import sys; print('.'.join(map(str, sys.version_info[:3])))"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    try:
        return version_tuple(completed.stdout.strip())
    except ValueError:
        return None


def interpreters(*, isolated: bool = False) -> list[tuple[str, tuple[int, ...]]]:
    found: list[tuple[str, tuple[int, ...]]] = []
    seen: set[str] = set()
    names = (os.environ.get("GNN_PIN_PYTHON"), *CANDIDATES)
    for name in names:
        if not name:
            continue
        executable = shutil.which(name)
        if not executable:
            continue
        real = os.path.realpath(executable)
        if real in seen:
            continue
        seen.add(real)
        version = interpreter_version(executable, isolated=isolated)
        if version is not None:
            found.append((executable, version))
    return found


def offline_resources(pin: dict):
    """Load the sibling consumer only for an explicitly requested offline arm."""
    if not any(name in os.environ for name in ("GNN_OFFLINE_BUNDLE", "GNN_OFFLINE_MANIFEST_SHA256")):
        return None
    name = "_textbook_gnn_offline"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name("gnn_offline.py"))
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    try:
        return sys.modules[name].from_environment(pin)
    except ValueError as error:
        raise SystemExit(f"gnn: offline resources: {error}") from error


def install_offline(executable: str, target: str, pin: dict, bundle) -> bool:
    """Use real pip, its isolated build backend and the complete locked closure."""
    helper = sys.modules[type(bundle).__module__]
    try:
        destination = Path(target)
        if (
            not destination.is_absolute() or not destination.is_dir() or destination.is_symlink()
            or destination.resolve() != destination or any(destination.iterdir())
        ):
            raise ValueError("offline installation requires a new empty canonical target")
        environment = {
            key: value for key, value in helper.git_environment().items()
            if not key.startswith("PIP_") and key not in ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP")
        }
        environment.update(
            PIP_CONFIG_FILE=os.devnull, PIP_NO_INDEX="1", PIP_FIND_LINKS=str(bundle.wheelhouse),
            PIP_NO_CACHE_DIR="1", PIP_DISABLE_PIP_VERSION_CHECK="1", PIP_NO_INPUT="1",
            PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1",
        )
        with tempfile.TemporaryDirectory(prefix="gnn-pip-") as directory:
            bytecode_root = Path(directory) / "bytecode"
            bytecode_root.mkdir()
            command = helper.installer_command(
                executable, root=bundle.root, runtime=bundle.manifest["runtime"],
                installer=bundle.manifest["installer"], pip_wheel=bundle.wheels["pip"],
                bytecode_root=bytecode_root,
            )
            environment["PYTHONPYCACHEPREFIX"] = str(bytecode_root)
            requirements = Path(directory) / "requirements.txt"
            constraints = Path(directory) / "constraints.txt"
            requirements.write_text(bundle.requirements(hashes=True), encoding="utf-8")
            constraints.write_text(bundle.requirements(hashes=False), encoding="utf-8")
            environment["PIP_CONSTRAINT"] = str(constraints)
            environment["PIP_BUILD_CONSTRAINT"] = str(constraints)
            spec = f"generalized-notation-notation @ git+{bundle.source.as_uri()}@{pin['revision']}"
            for step in (("--require-hashes", "-r", str(requirements)), ("--upgrade", spec)):
                completed = subprocess.run(
                    [
                        *command, "install", "--disable-pip-version-check", "--no-input", "--quiet",
                        "--no-index", "--find-links", str(bundle.wheelhouse), "--no-cache-dir",
                        "--no-compile", "--ignore-installed", "--target", target, *step,
                    ],
                    stdin=subprocess.DEVNULL, capture_output=True, text=True, env=environment,
                )
                if completed.returncode != 0:
                    print((completed.stderr or completed.stdout).strip(), file=sys.stderr)
                    return False
        return True
    except (OSError, ValueError) as error:
        raise SystemExit(f"gnn: offline installation: {error}") from error


def install(executable: str, target: str, pin: dict) -> bool:
    spec = (
        f"generalized-notation-notation @ git+https://github.com/"
        f"{pin['repository']}.git@{pin['revision']}"
    )
    steps = (
        ("defusedxml", "psutil", "pyyaml"),
        ("--no-deps", spec),
    )
    for step in steps:
        completed = subprocess.run(
            [
                executable,
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--no-input",
                "--quiet",
                "--target",
                target,
                *step,
            ],
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            print((completed.stderr or completed.stdout).strip(), file=sys.stderr)
            return False
    return True


def tracked_sketches(root: Path) -> list[Path]:
    """Select index-tracked sketches, never untracked or ignored filesystem discoveries."""
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z", "--", "*.gnn.md"],
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise SystemExit(f"gnn: cannot list tracked sketches: {error}") from error
    sketches = sorted(root / os.fsdecode(name) for name in completed.stdout.split(b"\0") if name)
    for sketch in sketches:
        if sketch.is_symlink() or not sketch.is_file():
            raise SystemExit(f"gnn: tracked sketch is not a regular file: {sketch.relative_to(root)}")
    return sketches


def stage_documents(
    sources: list[Path], source_root: Path, destination: Path
) -> list[tuple[str, Path]]:
    """Keep each source identity and basename in its own checker input directory."""
    documents: list[tuple[str, Path]] = []
    for index, source in enumerate(sources):
        identity = source.relative_to(source_root).as_posix()
        staged = destination / str(index) / source.name
        staged.parent.mkdir(parents=True)
        shutil.copy2(source, staged)
        documents.append((identity, staged))
    return documents


def verify(target: str, bundle=None) -> int:
    sys.path.insert(0, target)
    qualification = None
    guard = (
        contextlib.nullcontext()
        if bundle is None
        else sys.modules[type(bundle).__module__].qualified_install(target, bundle, PIN_PATH)
    )
    try:
        with guard as qualification:
            from gnn import __version__
            from gnn.parsers.basic import parse_gnn_formal, validate_gnn_syntax
            from gnn.type_checker import GNNTypeChecker

            pin = load_pin()
            expected = pin["tag"].removeprefix("v")
            if __version__ != expected:
                raise SystemExit(f"gnn: installed {__version__!r} does not match pin tag {pin['tag']!r}")

            sketches = tracked_sketches(ROOT)
            checked_documents: list[str] = []
            with tempfile.TemporaryDirectory(prefix="gnn-check-") as output_dir:
                output = Path(output_dir)
                if sketches:
                    sources = sketches
                    source = "repository"
                    source_root = ROOT
                else:
                    source_root = output / "exemplar"
                    exemplar = source_root / EXEMPLAR
                    exemplar.parent.mkdir(parents=True)
                    exemplar.write_bytes(
                        bundle.exemplar if bundle is not None
                        else fetch(pin["repository"], pin["revision"], EXEMPLAR)
                    )
                    sources = [exemplar]
                    source = "pinned-exemplar"

                documents = stage_documents(sources, source_root, output / "models")
                for index, (identity, sketch) in enumerate(documents):
                    parsed = parse_gnn_formal(sketch)
                    if parsed is None or getattr(parsed, "parse_errors", None):
                        raise SystemExit(f"gnn: {identity} did not parse cleanly")
                    valid, errors = validate_gnn_syntax(sketch.read_text(encoding="utf-8"), is_content=True)
                    if not valid:
                        raise SystemExit(f"gnn: {identity} syntax errors: {errors!r}")

                    # One unchanged basename per directory prevents collisions and does
                    # not rely on whether this pinned checker recurses into subdirectories.
                    report_dir = output / "reports" / str(index)
                    report_dir.mkdir(parents=True)
                    outcome = GNNTypeChecker().validate_gnn_files(sketch.parent, report_dir)
                    if outcome is not True:
                        raise SystemExit(
                            f"gnn: type checker did not pass {source} document {identity!r} "
                            f"(returned {outcome!r}; expected True)"
                        )
                    checked_documents.append(identity)
    except ValueError as error:
        if bundle is None:
            raise
        raise SystemExit(f"gnn: offline installed-origin/content qualification: {error}") from error

    scope, result = RECEIPTS[source]
    receipt = {
        "gnn-version": __version__,
        "pin-revision": pin["revision"],
        "models": len(checked_documents),
        "documents": checked_documents,
        "scope": scope,
        "source": source,
        "result": result,
    }
    if bundle is not None:
        receipt["offline-resources"] = {
            "manifest-sha256": bundle.digest,
            "installed-target": target,
            "retained-installation": "GITVAULT_EXECUTION_OUTPUT" in os.environ,
            "source-origin": bundle.manifest["source"]["origin"],
            "source-tree": bundle.manifest["source"]["tree"],
            "installed-vcs-url": bundle.source.as_uri(),
            "installed-vcs-commit": pin["revision"],
            "runtime": bundle.manifest["runtime"],
            "installed-versions": {name: item["version"] for name, item in bundle.wheels.items()},
            "source-qualification": qualification,
        }
    # Never emit a successful receipt before the trusted guard's exit rechecks.
    print(json.dumps(receipt, sort_keys=True))
    return 0


def main(argv: list[str]) -> int:
    if argv[:1] == ["--verify"]:
        if any(name in os.environ for name in ("GNN_OFFLINE_BUNDLE", "GNN_OFFLINE_MANIFEST_SHA256")):
            raise SystemExit("gnn: offline --verify cannot bypass interpreter selection and fresh installation")
        return verify(argv[1])

    pin = load_pin()
    bundle = offline_resources(pin)
    try:
        requires = REQUIRES_RE.search(
            (
                bundle.pyproject if bundle is not None
                else fetch(pin["repository"], pin["revision"], "pyproject.toml")
            ).decode("utf-8")
        )
    except OSError as error:
        raise SystemExit(f"gnn: cannot read pinned requires-python: {error}") from error
    if requires is None:
        raise SystemExit("gnn: pinned pyproject.toml has no supported requires-python declaration")
    spec = requires.group(1)
    try:
        parse_requires_python(spec)
    except ValueError as error:
        raise SystemExit(f"gnn: {error}") from error

    available = interpreters(isolated=bundle is not None)
    if not available:
        raise SystemExit("gnn: no usable python3 interpreter on PATH")
    for executable, version in available:
        label = ".".join(str(part) for part in version)
        if spec and not satisfies(version, spec):
            print(f"gnn: skipping {executable} ({label}) for requires-python {spec}", file=sys.stderr)
            continue
        if bundle is not None:
            try:
                bundle.check_runtime(executable)
            except ValueError as error:
                print(f"gnn: skipping {executable} ({label}): {error}", file=sys.stderr)
                continue
        retain_target = bundle is not None and "GITVAULT_EXECUTION_OUTPUT" in os.environ
        output = None
        if retain_target:
            output = Path(os.environ["GITVAULT_EXECUTION_OUTPUT"])
            if not output.is_absolute() or not output.is_dir() or output.is_symlink() or output.resolve() != output:
                raise SystemExit("gnn: native execution output is not a canonical ordinary directory")
        target = tempfile.mkdtemp(prefix="gnn-pin-", dir=output)
        if bundle is not None:
            target = str(Path(target).resolve())
        try:
            installed = (
                install_offline(executable, target, pin, bundle)
                if bundle is not None else install(executable, target, pin)
            )
            if not installed:
                continue
            print(f"gnn: installed {pin['tag']} with {executable} ({label})", file=sys.stderr)
            environment = dict(os.environ)
            if bundle is not None:
                environment.pop("PYTHONPATH", None)
                environment.pop("PYTHONHOME", None)
                # This only loads the ORIGINAL verify function in a fresh no-site
                # child. There is no second verifier or offline --verify shortcut.
                program = (
                    "import runpy,sys; checker=runpy.run_path(sys.argv[1]); "
                    "bundle=checker['offline_resources'](checker['load_pin']()); "
                    "raise SystemExit(checker['verify'](sys.argv[2],bundle))"
                )
                return subprocess.run(
                    [executable, "-I", "-S", "-B", "-c", program, str(Path(__file__).resolve()), target],
                    stdin=subprocess.DEVNULL, env=environment, cwd=ROOT,
                ).returncode
            environment["PYTHONPATH"] = os.pathsep.join(
                part for part in (target, environment.get("PYTHONPATH")) if part
            )
            return subprocess.run(
                [executable, str(Path(__file__).resolve()), "--verify", target],
                env=environment,
                cwd=ROOT,
            ).returncode
        finally:
            if not retain_target:
                shutil.rmtree(target, ignore_errors=True)

    detail = spec or "unknown"
    seen = ", ".join(f"{e} ({'.'.join(map(str, v))})" for e, v in available)
    raise SystemExit(
        f"gnn: no interpreter installed the pin; requires-python {detail}, available {seen}"
    )


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
