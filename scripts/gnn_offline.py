"""Content-bound resources for the original GNN gate; no acquisition or verdicts.

The externally reviewed manifest protocol is documented in .github/GNN.md.
All inputs are untrusted until the caller-supplied manifest digest is checked.
"""

from __future__ import annotations

import contextlib
import email.parser
import hashlib
import importlib.metadata
import importlib.util
import io
import json
import os
import re
import stat
import subprocess
import sys
import sysconfig
import tomllib
import urllib.parse
import zipfile
from pathlib import Path, PurePosixPath

SCHEMA = "gnn-offline-bundle/v1"
PACKAGE_MANIFEST_SHA256 = "43b33c0b2b40386afa3f306fec4cc13bc1fd7c3b570fbf11d5008bad5c8e6b51"
BOOTSTRAP_SHA256 = "f638d4c01fe7de31e43d793e59bf382d0c3d1a82f365c59238334a2b40adfb37"
DISTRIBUTION = "generalized-notation-notation"
EXEMPLAR = "input/gnn_files/basics/static_perception.md"
RUNTIME_FIELDS = {
    "implementation", "python", "cache_tag", "platform", "machine", "executable_sha256"
}
GIT_SELECTORS = {
    "GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE", "GIT_NAMESPACE",
    "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_SHALLOW_FILE",
    "GIT_REPLACE_REF_BASE",
}


class OfflineError(ValueError):
    """A prepared resource does not satisfy the offline gate's contract."""


def _fail(message: str):
    raise OfflineError(message)


def _fields(value, expected: set[str], label: str) -> dict:
    if not isinstance(value, dict) or set(value) != expected:
        _fail(f"{label} must contain exactly {', '.join(sorted(expected))}")
    return value


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            _fail(f"duplicate JSON field {key!r}")
        result[key] = value
    return result


def _json(data: bytes, label: str) -> dict:
    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=_object)
    except (UnicodeError, ValueError) as error:
        raise OfflineError(f"cannot read {label}: {error}") from error
    if not isinstance(value, dict):
        _fail(f"{label} is not a JSON object")
    return value


def _digest(value, label: str, width: int = 64) -> str:
    if not isinstance(value, str) or re.fullmatch(rf"[0-9a-f]{{{width}}}", value) is None:
        _fail(f"{label} is not a lowercase {width}-hex digest")
    return value


def _relative(value) -> str:
    if (
        not isinstance(value, str) or not value or "\\" in value
        or any(ord(character) < 32 for character in value)
    ):
        _fail("bundle path is not a safe relative POSIX path")
    path = PurePosixPath(value)
    if not path.parts or path.is_absolute() or str(path) != value or any(part in (".", "..") for part in path.parts):
        _fail(f"bundle path is not normalized and contained: {value!r}")
    return value


def ordinary_path(root: Path, relative: str, *, directory: bool = False) -> Path:
    """Reject redirected ancestors as well as redirected leaf files."""
    path = root
    parts = PurePosixPath(_relative(relative)).parts
    try:
        for index, part in enumerate(parts):
            path = path / part
            mode = path.lstat().st_mode
            expected_directory = index < len(parts) - 1 or directory
            if not (stat.S_ISDIR(mode) if expected_directory else stat.S_ISREG(mode)):
                _fail(f"bundle path is a symlink or nonordinary file: {relative!r}")
        if not path.resolve().is_relative_to(root):
            _fail(f"bundle path escapes its root: {relative!r}")
    except OSError as error:
        raise OfflineError(f"cannot read bundle path {relative!r}: {error}") from error
    return path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _inventory(root: Path, *, omit_manifest: bool = False, hashes: bool = True) -> dict:
    files = {}

    def failed(error):
        raise OfflineError(f"cannot inventory resources: {error}") from error

    try:
        for directory, directories, names in os.walk(root, followlinks=False, onerror=failed):
            for name in directories:
                ordinary_path(root, (Path(directory) / name).relative_to(root).as_posix(), directory=True)
            for name in names:
                relative = (Path(directory) / name).relative_to(root).as_posix()
                path = ordinary_path(root, relative)
                if not (omit_manifest and relative == "manifest.json"):
                    files[relative] = sha256_file(path) if hashes else None
    except OSError as error:
        raise OfflineError(f"cannot inventory resources: {error}") from error
    return files


def git_environment() -> dict[str, str]:
    environment = {key: value for key, value in os.environ.items() if key not in GIT_SELECTORS}
    environment.update(GIT_OPTIONAL_LOCKS="0", GIT_NO_REPLACE_OBJECTS="1", GIT_TERMINAL_PROMPT="0", GIT_NO_LAZY_FETCH="1")
    return environment


def _git(source: Path, *arguments: str, missing: bool = False, data: bytes | None = None) -> bytes:
    try:
        completed = subprocess.run(
            ["git", "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", str(source), *arguments],
            stdin=subprocess.DEVNULL if data is None else None, input=data,
            capture_output=True, env=git_environment(),
        )
    except OSError as error:
        raise OfflineError(f"cannot inspect prepared Git source: {error}") from error
    if completed.returncode != 0 and not (missing and completed.returncode == 1):
        _fail(f"prepared Git source inspection failed: {arguments[0]}")
    return completed.stdout


def _check_source(root: Path, source: dict, pin: dict) -> Path:
    _fields(source, {"path", "origin", "commit", "tree", "acquisition"}, "source")
    origin = f"https://github.com/{pin['repository']}.git"
    if source["origin"] != origin or source["commit"] != pin["revision"]:
        _fail("source origin/commit differs from the original pin")
    _digest(source["tree"], "source tree", 40)
    acquisition = _fields(
        source["acquisition"], {"method", "origin", "commit", "tree", "admission", "identity"},
        "source acquisition",
    )
    if acquisition["method"] not in ("git-clone", "git-fetch"):
        _fail("source acquisition is not native Git clone/fetch")
    if any(acquisition[key] != source[key] for key in ("origin", "commit", "tree")):
        _fail("source acquisition origin/commit/tree differs from the source")
    evidence = _json(ordinary_path(root, acquisition["admission"]).read_bytes(), "native acquisition evidence")
    if (
        evidence.get("result") != "complete-current-pinned-installable-project-acquired-not-built-installed-or-tested"
        or evidence.get("error") is not None
    ):
        _fail("native acquisition evidence is incomplete or failed")
    if (
        evidence.get("schema") != "textbook-pinned-source-acquisition/v1"
        or evidence.get("repository") != pin["repository"]
        or evidence.get("origin") != origin or evidence.get("stored_origin") != origin
        or evidence.get("revision") != pin["revision"] or evidence.get("local_commit") != pin["revision"]
        or evidence.get("tree") != source["tree"] or evidence.get("holder_released") is not True
    ):
        _fail("native acquisition evidence differs from the pinned origin/commit/tree")
    admission = evidence.get("admission")
    if (
        not isinstance(admission, dict) or not isinstance(admission.get("pid"), int)
        or admission["pid"] <= 0
        or admission.get("repository") != "ActiveInferenceInstitute/Parr_et_al_2022_ActInf_Textbook"
        or not isinstance(admission.get("working_copy"), str)
        or not Path(admission["working_copy"]).is_absolute() or not admission.get("acquired_at")
    ):
        _fail("native acquisition has no actual consumer repository admission")
    identity_document = _json(ordinary_path(root, acquisition["identity"]).read_bytes(), "mapped identity evidence")
    identity = identity_document.get("identity", identity_document)
    if (
        not isinstance(identity, dict) or not isinstance(identity.get("login"), str) or not identity["login"]
        or identity.get("mechanism") != "token" or identity != evidence.get("identity")
    ):
        _fail("native acquisition has no matching mapped token identity evidence")
    actions = evidence.get("actions")
    if not isinstance(actions, list) or not actions:
        _fail("native acquisition has no actual Git actions")
    network_actions = [item for item in actions if isinstance(item, dict) and item.get("network") is True]
    if not network_actions or any(
        item.get("returncode") != 0 or not isinstance(item.get("slot"), int) or item["slot"] < 0
        for item in network_actions
    ):
        _fail("native acquisition has failed or unbudgeted Git network actions")
    operation = acquisition["method"].removeprefix("git-")
    if not any(
        isinstance(item.get("argv"), list) and operation in item["argv"] and origin in item["argv"]
        for item in network_actions
    ):
        _fail("native acquisition method/origin does not match its actual Git action")
    checkout = ordinary_path(root, source["path"], directory=True)
    git_directory = ordinary_path(checkout, ".git", directory=True)
    for relative in ("commondir", "objects/info/alternates", "objects/info/http-alternates", "modules"):
        if (git_directory / relative).exists():
            _fail("prepared Git source is borrowed or contains submodules")
    if Path(os.fsdecode(_git(checkout, "rev-parse", "--absolute-git-dir")).strip()).resolve() != git_directory:
        _fail("prepared Git source uses an external Git directory")
    if _git(checkout, "config", "--local", "--get-all", "remote.origin.url").decode().splitlines() != [origin]:
        _fail("prepared Git source has a different actual origin")
    if (
        _git(checkout, "config", "--local", "--get-regexp", r"^(extensions\.partialclone|remote\..*\.(promisor|partialclonefilter))$", missing=True)
        or any((git_directory / "objects" / "pack").glob("*.promisor"))
    ):
        _fail("prepared Git source is a partial/promisor clone")
    if _git(checkout, "rev-parse", "--verify", "HEAD").decode().strip() != pin["revision"]:
        _fail("prepared Git source HEAD differs from the original commit")
    if _git(checkout, "rev-parse", "HEAD^{tree}").decode().strip() != source["tree"]:
        _fail("prepared Git source tree differs from the authenticated tree")
    commit = _git(checkout, "cat-file", "commit", pin["revision"])
    if hashlib.sha1(f"commit {len(commit)}\0".encode() + commit).hexdigest() != pin["revision"]:
        _fail("prepared Git commit object is corrupt")
    tracked = set()
    trees = {source["tree"]}
    blobs = set()
    for record in _git(checkout, "ls-tree", "-r", "-t", "-z", "--full-tree", pin["revision"]).split(b"\0"):
        if not record:
            continue
        header, raw_path = record.split(b"\t", 1)
        mode, kind, blob = header.split()
        relative = _relative(raw_path.decode("utf-8"))
        if mode == b"040000" and kind == b"tree":
            trees.add(blob.decode())
            continue
        blobs.add(blob.decode())
        if mode not in (b"100644", b"100755") or kind != b"blob" or relative == ".gitmodules":
            _fail("prepared Git tree contains symlinks, submodules or unsupported entries")
        path = ordinary_path(checkout, relative)
        content_digest = hashlib.sha1(f"blob {path.stat().st_size}\0".encode())
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1 << 20), b""):
                content_digest.update(block)
        if content_digest.hexdigest() != blob.decode():
            _fail(f"prepared Git working file differs from its pinned blob: {relative}")
        if bool(path.stat().st_mode & 0o111) != (mode == b"100755"):
            _fail(f"prepared Git working file mode differs: {relative}")
        tracked.add(relative)
    # A depth-one native acquisition suffices only with every pinned-tree object
    # actually local. No lazy fetch or borrowed object store is permitted.
    identities = sorted(trees | blobs)
    present = _git(
        checkout, "cat-file", "--batch-check=%(objectname) %(objecttype)",
        data="".join(identity + "\n" for identity in identities).encode(),
    ).decode().splitlines()
    if present != [identity + (" tree" if identity in trees else " blob") for identity in identities]:
        _fail("prepared Git source is missing a pinned-tree object")
    tree_objects = io.BytesIO(_git(
        checkout, "cat-file", "--batch",
        data="".join(identity + "\n" for identity in sorted(trees)).encode(),
    ))
    for identity in sorted(trees):
        header = tree_objects.readline().rstrip(b"\n").split()
        if len(header) != 3 or header[:2] != [identity.encode(), b"tree"]:
            _fail("prepared Git tree object is unavailable")
        payload = tree_objects.read(int(header[2]))
        if tree_objects.read(1) != b"\n" or hashlib.sha1(f"tree {len(payload)}\0".encode() + payload).hexdigest() != identity:
            _fail("prepared Git tree object identity is corrupt")
    actual = set()
    for directory, directories, names in os.walk(checkout):
        if Path(directory) == checkout:
            directories[:] = [name for name in directories if name != ".git"]
        actual.update((Path(directory) / name).relative_to(checkout).as_posix() for name in names)
    if tracked != actual:
        _fail("prepared Git working-tree inventory differs from the pinned tree")
    ordinary_path(checkout, "pyproject.toml")
    ordinary_path(checkout, EXEMPLAR)
    return checkout


def canonical_name(value: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[A-Za-z0-9]+(?:[-_.][A-Za-z0-9]+)*", value) is None:
        _fail("invalid distribution name")
    return re.sub(r"[-_.]+", "-", value).lower()


def _wheel_metadata(path: Path):
    try:
        with zipfile.ZipFile(path) as archive:
            metadata = []
            seen = set()
            for member in archive.infolist():
                relative = _relative(member.filename.rstrip("/"))
                if relative in seen or stat.S_ISLNK(member.external_attr >> 16):
                    _fail("wheel contains duplicate or symlink entries")
                seen.add(relative)
                if not member.is_dir() and re.fullmatch(r"[^/]+\.dist-info/METADATA", relative):
                    metadata.append(member.filename)
            if len(metadata) != 1:
                _fail("wheel must have exactly one distribution METADATA")
            return email.parser.BytesParser().parsebytes(archive.read(metadata[0]))
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        raise OfflineError(f"cannot inspect wheel {path.name}: {error}") from error


def _check_wheels(root: Path, records) -> dict[str, dict]:
    if not isinstance(records, list) or not records:
        _fail("bundle requires a complete nonempty wheel lock")
    wheels = {}
    for record in records:
        _fields(record, {"name", "version", "path", "sha256", "registry"}, "wheel")
        name = canonical_name(record["name"])
        version = record["version"]
        if name != record["name"] or name in wheels or name == DISTRIBUTION:
            _fail("wheel names must be unique canonical dependencies, never a GNN wheel")
        if not isinstance(version, str) or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.!+_-]*", version) is None:
            _fail("wheel version is not an exact locked version")
        path = ordinary_path(root, record["path"])
        if path.parent != root / "wheelhouse" or path.suffix != ".whl":
            _fail("locked wheels must be directly inside the exact wheelhouse")
        if sha256_file(path) != _digest(record["sha256"], "wheel SHA-256"):
            _fail(f"wheel digest differs: {path.name}")
        metadata = _wheel_metadata(path)
        if (
            len(metadata.get_all("Name", [])) != 1 or len(metadata.get_all("Version", [])) != 1
            or canonical_name(metadata["Name"]) != name or metadata["Version"] != version
        ):
            _fail(f"wheel METADATA differs from lock: {path.name}")
        registry = _json(ordinary_path(root, record["registry"]).read_bytes(), "PyPI response")
        info = registry.get("info", {})
        if not isinstance(info, dict) or canonical_name(info.get("name")) != name or info.get("version") != version:
            _fail("PyPI response name/version differs from the wheel lock")
        artifacts = registry.get("urls")
        if not isinstance(artifacts, list):
            _fail("PyPI response has no version artifact list")
        matches = [item for item in artifacts if isinstance(item, dict) and item.get("filename") == path.name]
        if len(matches) != 1:
            _fail("PyPI response does not uniquely advertise the locked wheel")
        artifact = matches[0]
        url = urllib.parse.urlsplit(artifact.get("url", ""))
        if (
            artifact.get("digests", {}).get("sha256") != record["sha256"]
            or artifact.get("packagetype") != "bdist_wheel" or artifact.get("yanked") is not False
            or url.scheme != "https" or url.netloc != "files.pythonhosted.org"
            or not url.path.startswith("/packages/") or url.query or url.fragment
            or urllib.parse.unquote(url.path.rsplit("/", 1)[-1]) != path.name
        ):
            _fail("wheel lacks its exact external registry artifact/hash binding")
        wheels[name] = record
    if not {"defusedxml", "psutil", "pyyaml", "packaging", "pip"}.issubset(wheels):
        _fail("wheel closure omits original checker prerequisites, packaging or installer pip")
    if {path.name for path in (root / "wheelhouse").iterdir()} != {Path(item["path"]).name for item in records}:
        _fail("wheelhouse contains files outside the exact wheel lock")
    return wheels


def runtime_fingerprint(executable: str) -> dict:
    """Inspect the actual selected interpreter without importing project packages."""
    program = (
        "import hashlib,json,pathlib,platform,sys,sysconfig; "
        "print(json.dumps(dict(implementation=sys.implementation.name,"
        "python='.'.join(map(str,sys.version_info[:3])),cache_tag=sys.implementation.cache_tag,"
        "platform=sysconfig.get_platform(),machine=platform.machine(),"
        "executable_sha256=hashlib.sha256(pathlib.Path(sys.executable).resolve().read_bytes()).hexdigest())))"
    )
    try:
        completed = subprocess.run(
            [executable, "-I", "-S", "-B", "-c", program], stdin=subprocess.DEVNULL,
            capture_output=True, check=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise OfflineError("cannot identify the selected offline interpreter") from error
    return _fields(_json(completed.stdout, "interpreter fingerprint"), RUNTIME_FIELDS, "runtime")


class Bundle:
    def __init__(self, root: Path, manifest: dict, digest: str, source: Path, wheels: dict):
        self.root = root
        self.manifest = manifest
        self.digest = digest
        self.source = source
        self.wheels = wheels
        self.wheelhouse = root / "wheelhouse"
        self.pyproject = ordinary_path(source, "pyproject.toml").read_bytes()
        self.exemplar = ordinary_path(source, EXEMPLAR).read_bytes()
        self.package_manifest = ordinary_path(root, manifest["package_manifest"]).read_bytes()
        self.bootstrap = ordinary_path(root, manifest["bootstrap"])

    def check_runtime(self, executable: str):
        if runtime_fingerprint(executable) != self.manifest["runtime"]:
            _fail("selected interpreter differs from the authenticated bundle runtime")

    def check_unchanged(self):
        if sha256_file(ordinary_path(self.root, "manifest.json")) != self.digest:
            _fail("bundle manifest changed during the gate")
        if _inventory(self.root, omit_manifest=True) != self.manifest["files"]:
            _fail("bundle resources changed during the gate")

    def requirements(self, *, hashes: bool) -> str:
        return "".join(
            f"{name}=={item['version']}" + (f" --hash=sha256:{item['sha256']}" if hashes else "") + "\n"
            for name, item in sorted(self.wheels.items())
        )


def load_bundle(directory: str | Path, expected_sha256: str, pin: dict) -> Bundle:
    """Authenticate all prepared resources before reading project declarations."""
    _digest(expected_sha256, "externally expected manifest SHA-256")
    root = Path(directory)
    if not root.is_absolute() or not root.is_dir() or root.is_symlink() or root.resolve() != root:
        _fail("offline bundle must be an absolute, canonical, symlink-free directory")
    try:
        manifest_bytes = ordinary_path(root, "manifest.json").read_bytes()
        if hashlib.sha256(manifest_bytes).hexdigest() != expected_sha256:
            _fail("bundle manifest digest differs from the externally expected SHA-256")
        manifest = _fields(
            _json(manifest_bytes, "bundle manifest"),
            {"schema", "pin", "source", "package_manifest", "bootstrap", "runtime", "installer", "wheels", "files"},
            "bundle manifest",
        )
        if manifest["schema"] != SCHEMA:
            _fail("unsupported offline bundle schema")
        expected_pin = {key: pin[key] for key in ("repository", "revision", "tag")}
        if manifest["pin"] != expected_pin:
            _fail("offline bundle pin differs from the original pin")
        files = manifest["files"]
        if not isinstance(files, dict) or not files or "manifest.json" in files:
            _fail("bundle requires an exact nonempty file inventory excluding manifest.json")
        for relative, digest in files.items():
            _relative(relative)
            _digest(digest, f"file SHA-256 for {relative}")
        if _inventory(root, omit_manifest=True) != files:
            _fail("bundle file digest/inventory mismatch")
        source = _check_source(root, manifest["source"], pin)
        source_manifest_path = ordinary_path(root, manifest["package_manifest"])
        if sha256_file(source_manifest_path) != PACKAGE_MANIFEST_SHA256:
            _fail("package manifest differs from its independently trusted SHA-256")
        package = _json(source_manifest_path.read_bytes(), "trusted package manifest")
        if package.get("commit") != pin["revision"] or not isinstance(package.get("files"), dict) or not package["files"]:
            _fail("trusted package manifest does not cover the pinned package")
        prefix = manifest["source"]["path"] + "/"
        package_files = {path[len(prefix):]: digest for path, digest in files.items() if path.startswith(prefix + "src/gnn/")}
        if package_files != package["files"]:
            _fail("installable Git source differs from the independently trusted package inventory")
        if sha256_file(ordinary_path(root, manifest["bootstrap"])) != BOOTSTRAP_SHA256:
            _fail("bootstrap differs from its independently trusted SHA-256")
        runtime = _fields(manifest["runtime"], RUNTIME_FIELDS, "runtime")
        if any(not isinstance(value, str) or not value for value in runtime.values()) or runtime["implementation"] != "cpython":
            _fail("offline runtime fingerprint is malformed or not CPython")
        _digest(runtime["executable_sha256"], "runtime executable SHA-256")
        wheels = _check_wheels(root, manifest["wheels"])
        installer = _fields(manifest["installer"], {"prefix", "pip_version"}, "installer")
        if not isinstance(installer["prefix"], str) or not Path(installer["prefix"]).is_absolute():
            _fail("installer prefix must be an explicit absolute task-owned virtual environment")
        if installer["pip_version"] != wheels["pip"]["version"]:
            _fail("installer pip version differs from the externally locked pip wheel")
        return Bundle(root, manifest, expected_sha256, source, wheels)
    except (OSError, UnicodeError, KeyError, TypeError, zipfile.BadZipFile) as error:
        raise OfflineError(f"cannot authenticate offline bundle: {error}") from error


def from_environment(pin: dict) -> Bundle | None:
    names = ("GNN_OFFLINE_BUNDLE", "GNN_OFFLINE_MANIFEST_SHA256")
    if not any(name in os.environ for name in names):
        return None
    if not all(os.environ.get(name) for name in names):
        _fail("GNN_OFFLINE_BUNDLE and GNN_OFFLINE_MANIFEST_SHA256 must both be nonempty")
    return load_bundle(os.environ[names[0]], os.environ[names[1]], pin)


def _installed_wheel_content(target: Path, root: Path, record: dict):
    """Bind installed libraries/metadata to the externally hashed wheel payload."""
    bound_files = set()
    with zipfile.ZipFile(ordinary_path(root, record["path"])) as archive:
        for member in archive.infolist():
            if member.is_dir():
                continue
            relative = _relative(member.filename)
            parts = PurePosixPath(relative).parts
            if parts[0].endswith(".data"):
                # Scripts/headers/data are relocated by pip, not Python import roots.
                if len(parts) < 3 or parts[1] not in ("purelib", "platlib", "scripts", "headers", "data"):
                    _fail("wheel has an unsupported installation layout")
                if parts[1] not in ("purelib", "platlib"):
                    continue
                relative = PurePosixPath(*parts[2:]).as_posix()
            if relative.endswith(".dist-info/RECORD"):
                continue  # pip legitimately rewrites its installation record.
            installed = ordinary_path(target, relative)
            if sha256_file(installed) != hashlib.sha256(archive.read(member)).hexdigest():
                _fail(f"installed dependency content differs from locked wheel: {relative}")
            bound_files.add(installed)
    return bound_files


def installer_command(
    executable: str, *, root: Path, runtime: dict, installer: dict,
    pip_wheel: dict, bytecode_root: Path,
) -> list[str]:
    """Bind authenticated runtime/pip records before executing the genuine pip CLI."""
    if runtime_fingerprint(executable) != runtime:
        _fail("selected interpreter differs from the authenticated bundle runtime")
    prefix = Path(installer["prefix"])
    if not prefix.is_dir() or prefix.is_symlink() or prefix.resolve() != prefix:
        _fail("installer virtual environment is not a canonical ordinary directory")
    if Path(executable).absolute().parent != prefix / "bin":
        _fail("selected interpreter is outside the task-owned installer environment")
    configuration = ordinary_path(prefix, "pyvenv.cfg").read_text(encoding="utf-8")
    settings = dict(
        (key.strip().lower(), value.strip().lower())
        for line in configuration.splitlines() if "=" in line
        for key, value in [line.split("=", 1)]
    )
    if settings.get("include-system-site-packages") != "false":
        _fail("installer virtual environment may borrow system site packages")
    version = runtime["python"].split(".")
    library = ordinary_path(prefix, f"lib/python{'.'.join(version[:2])}/site-packages", directory=True)
    if pip_wheel["name"] != "pip" or installer["pip_version"] != pip_wheel["version"]:
        _fail("installer pip version differs from the externally locked pip wheel")
    wheel = ordinary_path(root, pip_wheel["path"])
    if sha256_file(wheel) != _digest(pip_wheel["sha256"], "wheel SHA-256"):
        _fail(f"wheel digest differs: {wheel.name}")
    bound_files = _installed_wheel_content(library, root, pip_wheel)
    actual_library = {library / relative for relative in _inventory(library, hashes=False)}
    generated_metadata = {
        path.parent / name
        for path in bound_files if path.name == "METADATA" and path.parent.name.endswith(".dist-info")
        for name in ("RECORD", "INSTALLER", "REQUESTED", "direct_url.json")
    }
    if not actual_library.issubset(bound_files | generated_metadata):
        _fail("installer search root contains files outside its locked pip distribution")
    pip_files = {library / "pip" / relative for relative in _inventory(library / "pip", hashes=False)}
    if pip_files != {path for path in bound_files if path.is_relative_to(library / "pip")}:
        _fail("installer pip contains code outside its externally locked wheel")
    metadata = list(importlib.metadata.distributions(path=[str(library)]))
    installed_pip = [item for item in metadata if canonical_name(item.metadata["Name"]) == "pip"]
    if len(installed_pip) != 1 or installed_pip[0].version != installer["pip_version"]:
        _fail("installer pip metadata differs from its externally locked wheel")
    if not bytecode_root.is_dir() or any(bytecode_root.iterdir()):
        _fail("installer requires a fresh empty task-owned bytecode search root")
    # -S prevents .pth/sitecustomize execution. A fresh cache root also prevents
    # borrowing old .pyc files; -B leaves that root empty. This is the real pip CLI.
    program = (
        "import runpy,sys; sys.pycache_prefix=sys.argv.pop(1); "
        "sys.path.insert(0,sys.argv.pop(1)); runpy.run_module('pip',run_name='__main__')"
    )
    return [executable, "-I", "-S", "-B", "-c", program, str(bytecode_root), str(library)]


def validate_installed(target: Path, bundle: Bundle) -> tuple[dict, set[Path]]:
    """Validate real metadata/content without importing GNN or trusting site paths."""
    if not target.is_absolute() or not target.is_dir() or target.is_symlink() or target.resolve() != target:
        _fail("installed target is not a canonical ordinary directory")
    # Inventory first: never inspect metadata through a redirected target child.
    _inventory(target, hashes=False)
    expected = {name: item["version"] for name, item in bundle.wheels.items()}
    expected[DISTRIBUTION] = bundle.manifest["pin"]["tag"].removeprefix("v")
    distributions = {}
    for distribution in importlib.metadata.distributions(path=[str(target)]):
        name = canonical_name(distribution.metadata["Name"])
        if name in distributions or name not in expected or distribution.version != expected[name]:
            _fail("installed distribution inventory/version differs from the authenticated lock")
        metadata_paths = [item for item in distribution.files or () if str(item).endswith(".dist-info/METADATA")]
        if len(metadata_paths) != 1:
            _fail("installed distribution has no unique file-backed METADATA")
        metadata_path = Path(distribution.locate_file(metadata_paths[0]))
        if not metadata_path.is_relative_to(target) or metadata_path.parent.parent != target:
            _fail("installed distribution metadata is outside the fresh target")
        ordinary_path(target, metadata_path.relative_to(target).as_posix())
        distributions[name] = distribution
    if set(distributions) != set(expected):
        _fail("fresh target is missing locked distributions")
    validate_vcs_origin(target, bundle, distributions[DISTRIBUTION])
    package = _json(bundle.package_manifest, "trusted package manifest")
    bound_files = {target / relative.removeprefix("src/") for relative in package["files"]}
    for record in bundle.wheels.values():
        bound_files.update(_installed_wheel_content(target, bundle.root, record))
    return distributions, bound_files


def validate_vcs_origin(target: Path, bundle: Bundle, distribution):
    """Check actual local-VCS metadata; this alone is never a conformance verdict."""
    text = distribution.read_text("direct_url.json")
    if text is None:
        _fail("installed GNN has no genuine PEP 610 VCS metadata")
    origin = _json(text.encode("utf-8"), "installed direct_url.json")
    if origin != {
        "url": bundle.source.as_uri(),
        "vcs_info": {"vcs": "git", "commit_id": bundle.manifest["pin"]["revision"], "requested_revision": bundle.manifest["pin"]["revision"]},
    }:
        _fail("installed GNN PEP 610 local URL/VCS commit differs from the prepared source")
    located = Path(distribution.locate_file("gnn/__init__.py"))
    if located != target / "gnn" / "__init__.py":
        _fail("installed GNN module root differs from its fresh distribution target")
    ordinary_path(target, "gnn/__init__.py")


def _dependency_closure(bundle: Bundle, distributions: dict):
    # packaging is itself byte-checked against its registry-bound wheel before import.
    from packaging.requirements import Requirement
    from packaging.version import Version

    def require(text: str, label: str, extra: str = ""):
        try:
            requirement = Requirement(text)
            if requirement.marker is not None and not requirement.marker.evaluate({"extra": extra}):
                return None
            name = canonical_name(requirement.name)
            if requirement.url is not None or name not in distributions:
                _fail(f"{label} dependency is not in the exact installed wheel closure: {text}")
            if Version(distributions[name].version) not in requirement.specifier:
                _fail(f"{label} dependency version does not satisfy the original declaration: {text}")
            return name, requirement.extras
        except ValueError as error:
            raise OfflineError(f"cannot interpret original {label} dependency {text!r}: {error}") from error

    try:
        project = tomllib.loads(bundle.pyproject.decode("utf-8"))
        declarations = project["project"]["dependencies"]
        build = project["build-system"]["requires"]
    except (KeyError, UnicodeError, ValueError) as error:
        raise OfflineError(f"pinned pyproject has no supported declared build/runtime dependencies: {error}") from error
    if not isinstance(declarations, list) or not isinstance(build, list) or not build:
        _fail("original build/runtime dependency declarations are malformed")
    pending = [(text, "original runtime", "") for text in declarations]
    pending += [(text, "isolated build", "") for text in build]
    pending += [(name, "locked distribution", "") for name in distributions]
    visited = set()
    while pending:
        text, label, extra = pending.pop()
        admitted = require(text, label, extra)
        if admitted is None:
            continue
        name, extras = admitted
        for selected_extra in {"", *extras}:
            key = (name, selected_extra)
            if key in visited:
                continue
            visited.add(key)
            pending.extend((item, name, selected_extra) for item in distributions[name].requires or ())


def _module_origins(target: Path, bound_files: set[Path], allowed_files: set[Path], standard_roots: tuple[Path, ...]):
    for name, module in tuple(sys.modules.items()):
        spec = getattr(module, "__spec__", None)
        origin = getattr(spec, "origin", None)
        filename = getattr(module, "__file__", None)
        if origin in ("built-in", "frozen"):
            continue
        for value in (origin, filename):
            if value is None:
                continue
            path = Path(value).resolve()
            if path in allowed_files or path in bound_files:
                continue
            if any(path.is_relative_to(root) for root in standard_roots) and not any(
                part in ("site-packages", "dist-packages") for part in path.parts
            ):
                continue
            _fail(f"imported module escaped the isolated target/stdlib: {name}")
        if origin is None:
            for value in getattr(module, "__path__", ()):
                path = Path(value).resolve()
                if path.is_relative_to(target):
                    if not any(item.is_relative_to(path) for item in bound_files):
                        _fail(f"namespace module has no authenticated wheel/package files: {name}")
                elif not any(path.is_relative_to(root) for root in standard_roots):
                    _fail(f"namespace module escaped the isolated target/stdlib: {name}")


@contextlib.contextmanager
def qualified_install(target: str, bundle: Bundle, pin_path: Path):
    """Guard the fresh installed package around the ORIGINAL imports and verdicts."""
    if not sys.flags.isolated or not sys.flags.no_site:
        _fail("offline verification requires a fresh isolated no-site interpreter")
    if any(name == "gnn" or name.startswith("gnn.") for name in sys.modules):
        _fail("offline qualification must start before any GNN import")
    bundle.check_runtime(sys.executable)
    path = Path(target)
    standard_roots = tuple({
        Path(sysconfig.get_path("stdlib")).resolve(),
        Path(sysconfig.get_path("platstdlib")).resolve(),
        *(Path(item).resolve() for item in sys.path if item and (item.endswith(".zip") or Path(item).name == "lib-dynload")),
    })
    sys.path[:] = [str(path), *[
        item for item in sys.path if item and any(Path(item).resolve() == root for root in standard_roots)
    ]]
    distributions, bound_files = validate_installed(path, bundle)
    _dependency_closure(bundle, distributions)
    name = "_textbook_trusted_gnn_bootstrap"
    spec = importlib.util.spec_from_file_location(name, bundle.bootstrap)
    if spec is None or spec.loader is None:
        _fail("cannot load authenticated bootstrap")
    bootstrap = importlib.util.module_from_spec(spec)
    sys.modules[name] = bootstrap
    spec.loader.exec_module(bootstrap)
    pin = bundle.manifest["pin"]
    importer_pin = bootstrap.ImporterPin(
        path=pin_path, commit=pin["revision"], tag=pin["tag"], repository=pin["repository"],
        schema="gnn-importer-pin/v1",
    )
    allowed_files = {Path(__file__).resolve(), pin_path.parent.parent / "scripts" / "check_gnn_conformance.py", bundle.bootstrap}
    # Do not ask the bootstrap's installed-origin normalizer to attest a local URL.
    # Our exact PEP 610 check binds the genuine file URL and VCS revision; its
    # explicit-source mode guards the freshly INSTALLED package bytes.
    with bootstrap.qualified_source(
        importer_pin, manifest=bundle.package_manifest, manifest_sha256=PACKAGE_MANIFEST_SHA256,
        package_root=path / "gnn", origin_mode="source",
    ) as receipt:
        yield receipt
        validate_installed(path, bundle)
        _module_origins(path, bound_files, allowed_files, standard_roots)
    if receipt.get("ok") is not True or receipt.get("imports_verified") is not True:
        _fail("trusted bootstrap did not complete its installed-content import guard")
    bundle.check_unchanged()
