#!/usr/bin/env python3
"""Prepare, but do not qualify, the original GNN arm's immutable offline inputs.

Run only under authorized native repository setup admission. Git acquisition and
hook review precede this command. The printed manifest digest is a review
candidate, not self-issued acceptance or a GNN verdict.

Venv identity and pip metadata are read without site startup. The genuine pip
wheel and retained registry response authenticate the installer before either
download or installation; sealing performs the same authentication offline.
"""
from __future__ import annotations

import argparse
import email.parser
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import urllib.parse
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from scripts import check_gnn_conformance as consumer
from scripts import gnn_offline

PACKAGE_MANIFEST_SHA256 = "43b33c0b2b40386afa3f306fec4cc13bc1fd7c3b570fbf11d5008bad5c8e6b51"
BOOTSTRAP_SHA256 = "f638d4c01fe7de31e43d793e59bf382d0c3d1a82f365c59238334a2b40adfb37"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def run(argv: list[str], *, cwd: Path | None = None) -> str:
    environment = dict(os.environ, PIP_CONFIG_FILE=os.devnull)
    result = subprocess.run(argv, cwd=cwd, env=environment, stdin=subprocess.DEVNULL,
                            text=True, capture_output=True, check=False, timeout=900)
    if result.returncode:
        raise RuntimeError(f"setup command failed ({result.returncode}): {argv!r}\n"
                           + result.stdout + result.stderr)
    return result.stdout.strip()


def inventory(root: Path) -> dict[str, str]:
    files = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"bundle symlink is forbidden: {path}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise ValueError(f"bundle special file is forbidden: {path}")
        relative = path.relative_to(root).as_posix()
        if relative != "manifest.json":
            files[relative] = digest(path)
    return files


def preserve_proof(source: Path, destination: Path, expected: str | None = None) -> None:
    if not source.is_file() or source.is_symlink():
        raise ValueError(f"proof is not an ordinary file: {source}")
    if expected is not None and digest(source) != expected:
        raise ValueError(f"independent proof digest mismatch: {source}")
    if destination.exists():
        raise ValueError(f"refusing to replace retained proof: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)


def inspect_installer(executable: Path, *, allowed_parent: Path) -> tuple[dict, dict]:
    """Read a real venv and its pip metadata without enabling site startup."""
    python = executable.absolute()
    parent = allowed_parent.absolute()
    prefix = python.parent.parent
    if (
        not parent.is_dir() or parent.resolve() != parent
        or not prefix.is_dir() or prefix.resolve() != prefix
        or not prefix.is_relative_to(parent)
        or python.parent != prefix / "bin" or python.parent.resolve() != python.parent
        or not python.is_file()
    ):
        raise ValueError("installer must be a canonical task-owned environment under the allowed parent")
    configuration = gnn_offline.ordinary_path(prefix, "pyvenv.cfg").read_text(encoding="utf-8")
    settings = {}
    for line in configuration.splitlines():
        if "=" not in line:
            continue
        key, value = (part.strip().lower() for part in line.split("=", 1))
        if key in settings:
            raise ValueError("installer pyvenv.cfg contains duplicate settings")
        settings[key] = value
    if settings.get("include-system-site-packages") != "false":
        raise ValueError("installer virtual environment may borrow system site packages")
    # CPython 3.12 leaves sys.prefix at the base prefix under -S. Derive the
    # venv from its canonical executable path and pyvenv.cfg, never from site.
    program = (
        "import hashlib,json,pathlib,platform,sys,sysconfig; "
        "print(json.dumps(dict(executable=sys.executable,base_prefix=sys.base_prefix,"
        "runtime=dict(implementation=sys.implementation.name,"
        "python='.'.join(map(str,sys.version_info[:3])),cache_tag=sys.implementation.cache_tag,"
        "platform=sysconfig.get_platform(),machine=platform.machine(),"
        "executable_sha256=hashlib.sha256(pathlib.Path(sys.executable).resolve().read_bytes()).hexdigest()))))"
    )
    details = json.loads(run([str(python), "-I", "-S", "-B", "-c", program]))
    if Path(details["executable"]).absolute() != python or Path(details["base_prefix"]).resolve() == prefix:
        raise ValueError("a base/shared interpreter is not a task-owned installer environment")
    runtime = details["runtime"]
    if runtime["implementation"] != "cpython":
        raise ValueError("installer runtime must be CPython")
    version = consumer.version_tuple(runtime["python"])
    library = gnn_offline.ordinary_path(
        prefix, f"lib/python{version[0]}.{version[1]}/site-packages", directory=True,
    )
    # Metadata is untrusted data at this point, not permission to import pip.
    gnn_offline._inventory(library, hashes=False)
    distributions = [
        item for item in importlib.metadata.distributions(path=[str(library)])
        if gnn_offline.canonical_name(item.metadata["Name"]) == "pip"
    ]
    if len(distributions) != 1 or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.!+_-]*", distributions[0].version) is None:
        raise ValueError("installer requires one exact file-backed pip distribution")
    return runtime, {"prefix": str(prefix), "pip_version": distributions[0].version}


def https_url(url: str, host: str) -> None:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.netloc != host or parsed.query or parsed.fragment:
        raise ValueError(f"registry resource is outside its exact HTTPS origin: {url}")


class RegistryRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, newurl):
        https_url(newurl, urllib.parse.urlsplit(request.full_url).netloc)
        return super().redirect_request(request, response, code, message, headers, newurl)


def https_payload(url: str, host: str) -> bytes:
    https_url(url, host)
    opener = urllib.request.build_opener(RegistryRedirect())
    with opener.open(url, timeout=60) as response:
        https_url(response.geturl(), host)
        return response.read()


def registry_document(name: str, version: str, proof: Path, *, retained: bool) -> tuple[dict, Path]:
    destination = proof / "pypi" / f"{name}-{version}.json"
    if retained:
        payload = gnn_offline.ordinary_path(proof, destination.relative_to(proof).as_posix()).read_bytes()
    else:
        if destination.exists() or destination.is_symlink():
            raise ValueError(f"refusing to replace registry evidence: {destination}")
        url = "https://pypi.org/pypi/" + urllib.parse.quote(name, safe="") + "/" + urllib.parse.quote(version, safe="") + "/json"
        payload = https_payload(url, "pypi.org")
    document = json.loads(payload)
    if gnn_offline.canonical_name(document["info"]["name"]) != name or document["info"]["version"] != version:
        raise ValueError(f"registry identity mismatch: {name}=={version}")
    if not retained:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as handle:
            handle.write(payload)
    return document, destination


def pip_bootstrap(root: Path, proof: Path, version: str, *, retained: bool) -> dict:
    """Acquire the exact genuine pip artifact before any installed pip executes."""
    document, _ = registry_document("pip", version, proof, retained=retained)
    filename = f"pip-{version}-py3-none-any.whl"
    matches = [entry for entry in document["urls"] if entry["filename"] == filename]
    if len(matches) != 1:
        raise ValueError("registry does not uniquely advertise the exact universal pip wheel")
    artifact = matches[0]
    https_url(artifact["url"], "files.pythonhosted.org")
    parsed = urllib.parse.urlsplit(artifact["url"])
    if (
        artifact["packagetype"] != "bdist_wheel" or artifact["yanked"] is not False
        or not parsed.path.startswith("/packages/")
        or urllib.parse.unquote(parsed.path.rsplit("/", 1)[-1]) != filename
        or re.fullmatch(r"[0-9a-f]{64}", artifact["digests"]["sha256"]) is None
    ):
        raise ValueError("pip bootstrap lacks an exact registry artifact/hash binding")
    path = root / "wheelhouse" / filename
    if not retained:
        payload = https_payload(artifact["url"], "files.pythonhosted.org")
        if hashlib.sha256(payload).hexdigest() != artifact["digests"]["sha256"]:
            raise ValueError("downloaded pip bootstrap differs from its registry SHA-256")
        with path.open("xb") as handle:
            handle.write(payload)
    record = wheel_record(path, proof, root, retained=True)
    if record["name"] != "pip" or record["version"] != version:
        raise ValueError("pip bootstrap wheel metadata differs from the installed pip identity")
    return record


def wheel_record(path: Path, proof: Path, root: Path, *, retained: bool = False) -> dict:
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
        if len(names) != 1:
            raise ValueError(f"wheel has ambiguous distribution metadata: {path.name}")
        metadata = email.parser.BytesParser().parsebytes(archive.read(names[0]))
    name = re.sub(r"[-_.]+", "-", metadata["Name"]).lower()
    version = metadata["Version"]
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", name) or not version:
        raise ValueError(f"invalid wheel identity: {path.name}")
    document, destination = registry_document(name, version, proof, retained=retained)
    sha256 = digest(path)
    matches = [entry for entry in document["urls"]
               if entry["filename"] == path.name and entry["digests"]["sha256"] == sha256]
    if len(matches) != 1:
        raise ValueError(f"wheel is not the registry's exact advertised artifact: {path.name}")
    artifact = matches[0]
    https_url(artifact["url"], "files.pythonhosted.org")
    parsed = urllib.parse.urlsplit(artifact["url"])
    if (
        artifact["packagetype"] != "bdist_wheel" or artifact["yanked"] is not False
        or not parsed.path.startswith("/packages/")
        or urllib.parse.unquote(parsed.path.rsplit("/", 1)[-1]) != path.name
    ):
        raise ValueError(f"wheel lacks its exact external registry artifact/hash binding: {path.name}")
    return {"name": name, "version": version, "path": path.relative_to(root).as_posix(),
            "sha256": sha256, "registry": destination.relative_to(root).as_posix()}


def prepare(args: argparse.Namespace) -> dict:
    root = args.bundle.resolve(strict=True)
    source = args.source.resolve(strict=True)
    source_relative = source.relative_to(root).as_posix()
    if source == root or (root / "manifest.json").exists():
        raise ValueError("use an unsealed acquisition directory with a contained source checkout")
    python = args.python.absolute()
    fingerprint, installer = inspect_installer(python, allowed_parent=ROOT / ".gnn-env")
    prefix = Path(installer["prefix"])
    pip_version = installer["pip_version"]
    pin = consumer.load_pin()
    pin_identity = {key: pin[key] for key in ("repository", "revision", "tag")}
    origin = f"https://github.com/{pin['repository']}.git"
    git = ["git", "-c", "core.fsmonitor=false", "--no-optional-locks", "-C", str(source)]
    if run(git + ["remote", "get-url", "origin"]) != origin:
        raise ValueError("acquired source does not retain its genuine pinned HTTPS origin")
    if run(git + ["rev-parse", "HEAD"]) != pin["revision"]:
        raise ValueError("acquired source HEAD does not match the original pin")
    tree = run(git + ["rev-parse", "HEAD^{tree}"])
    if run(git + ["status", "--porcelain=v1", "--untracked-files=all"]):
        raise ValueError("acquired source worktree is not clean")
    project = tomllib.loads((source / "pyproject.toml").read_text(encoding="utf-8"))
    requires_python = project["project"]["requires-python"]
    if not consumer.satisfies(consumer.version_tuple(fingerprint["python"]), requires_python):
        raise ValueError("task-owned interpreter does not satisfy the original requires-python")
    # The setup owner must inspect all immutable upstream packaging hooks first.
    requirements = list(project["project"]["dependencies"]) + list(project["build-system"]["requires"])
    requirements.extend(["defusedxml", "psutil", "pyyaml", "packaging", f"pip=={pip_version}"])
    wheelhouse = root / "wheelhouse"
    proof = root / "proof"
    if args.seal_prepared:
        for original, retained, expected in (
            (args.admission, proof / "native-acquisition.json", None),
            (args.identity, proof / "mapped-identity.json", None),
            (args.package_manifest, proof / "v5.1.0-source-manifest.json", PACKAGE_MANIFEST_SHA256),
            (args.bootstrap, proof / "gnn_bootstrap.py", BOOTSTRAP_SHA256),
        ):
            if not retained.is_file() or retained.is_symlink() or digest(original) != digest(retained):
                raise ValueError(f"retained acquisition proof changed: {retained}")
            if expected is not None and digest(retained) != expected:
                raise ValueError(f"independent proof digest mismatch: {retained}")
        acquisition = json.loads((proof / "wheel-acquisition.json").read_text(encoding="utf-8"))
        if acquisition["requirements"] != requirements or acquisition["requires_python"] != requires_python:
            raise ValueError("retained wheel acquisition does not match the original declarations")
        if not wheelhouse.is_dir() or wheelhouse.is_symlink():
            raise ValueError("retained wheelhouse is unavailable")
    else:
        if wheelhouse.exists():
            raise ValueError("refusing to overwrite a retained wheelhouse; use explicit --seal-prepared only after diagnosis")
        preserve_proof(args.admission, proof / "native-acquisition.json")
        preserve_proof(args.identity, proof / "mapped-identity.json")
        preserve_proof(args.package_manifest, proof / "v5.1.0-source-manifest.json", PACKAGE_MANIFEST_SHA256)
        preserve_proof(args.bootstrap, proof / "gnn_bootstrap.py", BOOTSTRAP_SHA256)
        wheelhouse.mkdir()
    pip_wheel = pip_bootstrap(root, proof, pip_version, retained=args.seal_prepared)
    with tempfile.TemporaryDirectory(prefix="gnn-setup-bytecode-", dir=prefix) as directory:
        command = gnn_offline.installer_command(
            str(python), root=root, runtime=fingerprint, installer=installer,
            pip_wheel=pip_wheel, bytecode_root=Path(directory),
        )
        if not args.seal_prepared:
            command += ["--isolated", "download", "--disable-pip-version-check",
                        "--no-cache-dir", "--only-binary=:all:", "--index-url", "https://pypi.org/simple",
                        "--dest", str(wheelhouse), *requirements]
            output = run(command)
            (proof / "wheel-acquisition.json").write_text(json.dumps({"argv": command, "stdout": output,
                    "requirements": requirements, "requires_python": requires_python}, indent=2) + "\n", encoding="utf-8")
    wheels = [
        wheel_record(path, proof, root, retained=args.seal_prepared or path == root / pip_wheel["path"])
        for path in sorted(wheelhouse.iterdir())
    ]
    gnn_offline._check_wheels(root, wheels)
    installer_lock = proof / "installer-requirements.txt"
    installer_wheels = [wheel for wheel in wheels if wheel["name"] == "pip"]
    if len(installer_wheels) != 1:
        raise ValueError("the exact installer pip wheel is missing")
    lock_text = "".join(f"{wheel['name']}=={wheel['version']} --hash=sha256:{wheel['sha256']}\n"
                        for wheel in installer_wheels)
    if args.seal_prepared:
        if installer_lock.read_text(encoding="utf-8") != lock_text:
            raise ValueError("retained installer wheel lock changed")
        installer_setup = json.loads((proof / "installer-setup.json").read_text(encoding="utf-8"))
        if installer_setup["prefix"] != str(prefix) or installer_setup["pip_version"] != pip_version:
            raise ValueError("retained installer setup does not match the actual task-owned environment")
    else:
        installer_lock.write_text(lock_text, encoding="utf-8")
        with tempfile.TemporaryDirectory(prefix="gnn-setup-bytecode-", dir=prefix) as directory:
            command = gnn_offline.installer_command(
                str(python), root=root, runtime=fingerprint, installer=installer,
                pip_wheel=pip_wheel, bytecode_root=Path(directory),
            )
            # -S does not activate a 3.12 venv prefix; installation must name it.
            command += ["--isolated", "install", "--disable-pip-version-check", "--prefix", str(prefix),
                        "--force-reinstall", "--no-index", "--find-links", str(wheelhouse),
                        "--no-cache-dir", "--require-hashes", "--no-deps", "--no-compile", "-r", str(installer_lock)]
            install_output = run(command)
        (proof / "installer-setup.json").write_text(json.dumps({"prefix": str(prefix), "pip_version": pip_version,
                        "stdout": install_output}, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "schema": "gnn-offline-bundle/v1", "pin": pin_identity,
        "source": {"path": source_relative, "origin": origin, "commit": pin["revision"], "tree": tree,
                   "acquisition": {"method": "git-clone", "origin": origin, "commit": pin["revision"],
                                   "tree": tree, "admission": "proof/native-acquisition.json",
                                   "identity": "proof/mapped-identity.json"}},
        "package_manifest": "proof/v5.1.0-source-manifest.json", "bootstrap": "proof/gnn_bootstrap.py",
        "runtime": fingerprint, "installer": installer,
        "wheels": wheels, "files": inventory(root),
    }
    manifest_path = root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"bundle": str(root), "candidate_manifest_sha256": digest(manifest_path),
            "wheels": len(wheels), "source_commit": pin["revision"], "source_tree": tree,
            "runtime": fingerprint, "installer": manifest["installer"],
            "scope": "setup only; external source/resource review must accept this digest before any original-arm gate"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seal-prepared", action="store_true",
                        help="validate and seal already acquired exact resources without network or installation")
    for name in ("bundle", "source", "python", "admission", "identity", "package-manifest", "bootstrap"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(prepare(args), indent=2, sort_keys=True))
    except (OSError, ValueError, RuntimeError, KeyError, TypeError, subprocess.TimeoutExpired, zipfile.BadZipFile) as error:
        print(f"gnn setup: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
