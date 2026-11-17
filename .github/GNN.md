# GNN conformance

`gnn conformance (pinned)` is the `gnn-conformance` job in
[`workflows/ci.yml`](workflows/ci.yml). It runs one command, `./run.sh gnn`,
which is [`../scripts/check_gnn_conformance.py`](../scripts/check_gnn_conformance.py).

The arm reads [`gnn-pin.json`](gnn-pin.json), which pins
`ActiveInferenceInstitute/Generalized_Notation_Notation` at `v5.1.0`
(`75c834bd8519dc7b5adc4d24f16bf393cfd1ecdf`) under schema
`gnn-importer-pin/v1`. The pin file supplies the online and offline checker;
an offline bundle must match it exactly and cannot override it.

What the arm parses:

1. every tracked `*.gnn.md` sketch — missing/replaced tracked files fail,
   duplicate basenames stage separately, and each must parse, pass syntax
   validation and receive a literal `True` type verdict;
2. when the repository declares no sketch yet (as now), the pinned upstream
   `input/gnn_files/basics/static_perception.md` exemplar at the pin's revision.

It also verifies that the installed parser's version equals the pin's tag. The
type checker returns `True` when every file validates, `2` when files are
invalid or none were found, and `False` on a hard failure; only `True` passes.
The printed receipt names what was checked: `scope` `repository sketches` with
`result` `repository-content-passed`, or `scope` `pinned GNN exemplar baseline`
with `result` `pinned-exemplar-baseline-passed`. The result is a pipeline and pin conformance baseline, not a claim that this
repository already contains a model. The default online arm needs network access
and a CPython that satisfies the pinned package's `requires-python`
(`>=3.11,<3.15`, read from the pinned revision).

The script's unit tests are the `tests` arm, `./run.sh tests`. They replace the
parser with fixed-result modules, so they need neither network nor the pinned
install, and they assert that a type-checker result other than `True` exits 1 and
that the receipt labels its source.

The receipt names every checked document. Python admission preserves numeric
patch precision and supported `~=` semantics and rejects unknown constraint
syntax before provisioning.
Historical protocol-only controls passed, but they are not installed-origin
proof for another pin or head. The original fresh-install arm must qualify
the actual final source and current pin; older receipts retain their own scope.

## Explicit prepared offline resources

The same `./run.sh gnn` arm accepts **both** `GNN_OFFLINE_BUNDLE` (an absolute
bundle directory) and `GNN_OFFLINE_MANIFEST_SHA256` (the independently reviewed
SHA-256 of its `manifest.json`). Supplying only one, or an empty value, fails.
Neither variable means the original online acquisition path. There is no
automatic cache, installed-package or package-only-source fallback.

Acquisition is a separate, authorized setup operation. It must retain the actual
native Git acquisition admission and mapped-identity evidence, the unchanged
upstream HTTPS origin, and a complete independent installable checkout at the
pin. Review that provenance and all bundle bytes before supplying the external
manifest digest to the offline gate. A bundle generating its own expected
digest, or an origin rewritten to disguise another source, is not provenance.
Setup does not run or qualify the GNN arm.

### Bundle protocol: `gnn-offline-bundle/v1`

`manifest.json` is UTF-8 JSON with exactly these top-level fields:

```json
{
  "schema": "gnn-offline-bundle/v1",
  "pin": {"repository": "OWNER/REPO", "revision": "40-hex", "tag": "vVERSION"},
  "source": {
    "path": "source",
    "origin": "https://github.com/OWNER/REPO.git",
    "commit": "40-hex",
    "tree": "40-hex",
    "acquisition": {
      "method": "git-clone",
      "origin": "https://github.com/OWNER/REPO.git",
      "commit": "40-hex",
      "tree": "40-hex",
      "admission": "proof/native-acquisition.json",
      "identity": "proof/mapped-identity.json"
    }
  },
  "package_manifest": "proof/v5.1.0-source-manifest.json",
  "bootstrap": "proof/gnn_bootstrap.py",
  "runtime": {
    "implementation": "cpython",
    "python": "major.minor.patch",
    "cache_tag": "cpython-XYZ",
    "platform": "sysconfig.get_platform()",
    "machine": "platform.machine()",
    "executable_sha256": "64-hex"
  },
  "installer": {
    "prefix": "/absolute/task-owned/.gnn-env/fresh-installer",
    "pip_version": "exact-locked-pip-version"
  },
  "wheels": [
    {
      "name": "canonical-distribution-name",
      "version": "exact-version",
      "path": "wheelhouse/exact-file.whl",
      "sha256": "64-hex",
      "registry": "proof/pypi/name-version.json"
    }
  ],
  "files": {"every/regular/bundle-file-except-manifest.json": "64-hex"}
}
```

`git-fetch` is the other allowed acquisition method. `admission` names the actual
retained `textbook-pinned-source-acquisition/v1` native receipt: the consumer
checks its actual origin/revision/tree, released consumer-repository admission,
mapped token identity and successful budget-slotted Git acquisition actions.
`identity` names that same receipt or its actual matching identity JSON record.
Neither path may name a synthetic success receipt.
The receipt must report completed full-project acquisition with no error.
Successful earlier Git actions do not turn a late producer failure into success.
Every bundle resource path is relative, normalized, contained and symlink-free.
`files` is the exact recursive regular-file inventory, including Git metadata,
wheels and evidence; extra files, symlinks and special files fail. The source
has an internal `.git` directory, no borrowed or partial/promisor object store,
gitlinks or submodules, and no modified/untracked working-tree files. An
exact-tag depth-one acquisition is sufficient only with the complete pinned
commit, every tree object and every needed blob actually present locally.
Its actual origin, HEAD, tree and every tracked file must agree with the
externally authenticated manifest and the original pin. In particular its
actual `pyproject.toml` and exemplar are required.

`package_manifest` must retain SHA-256
`43b33c0b2b40386afa3f306fec4cc13bc1fd7c3b570fbf11d5008bad5c8e6b51`:
its pinned commit and complete `src/gnn` inventory must match the installable
checkout. `bootstrap` must retain SHA-256
`f638d4c01fe7de31e43d793e59bf382d0c3d1a82f365c59238334a2b40adfb37`.
The authenticated bootstrap's `qualified_source` guard wraps the original
imports and verdicts on the freshly **installed** package and rechecks on exit.
Its explicit-source receipt keeps `vcs_verified=false`; exact HTTPS acquisition
and genuine local-VCS PEP 610 metadata are independently checked by the consumer.
The bootstrap is never an alternative installer/verifier. The package-only
export is not an install artifact.
These resources are published at immutable producer delivery
[`66d491f`](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation/tree/66d491f86895443cf588011cc6f40c37b8bae8fd/interop).
That resource-delivery commit is not the parser revision.


Each canonical wheel name appears once, with one exact version. Its retained
registry document is the actual `https://pypi.org/pypi/NAME/VERSION/json` response;
the response must identify that name/version and advertise the exact wheel
filename, SHA-256 and HTTPS `files.pythonhosted.org` artifact URL. The wheel's own
METADATA must match. The wheelhouse contains only these wheels and includes the
entire declared runtime **and isolated-build** closure, plus the original
`defusedxml`, `psutil`, `pyyaml` prerequisites, `packaging` for metadata validation
and the exact installer `pip` wheel. Incomplete or incompatible locks fail,
never borrow ambient packages. `installer.prefix` is a new task-owned venv
with system site packages disabled. Before executing pip, its actual library
and METADATA bytes must match the registry-bound locked pip wheel; unexpected
installer search-root files fail. A no-site loader runs the genuine pip CLI
with a fresh bytecode search root, not ambient `.pth`, packages or cached code.
Setup also uses no-site inspection and data-only pip metadata reads. It acquires
and authenticates the real registry-bound bootstrap pip wheel before any pip
execution, and uses the same authenticated loader for download, setup and sealing.
Unexpected bytecode is not exempt from the installer inventory: a bare `.pyc`
can override a standard-library module even with a fresh bytecode search root.
Setup and bootstrap disable pip configuration files before invoking isolated pip.
Setup also removes only the interpreter/destination selectors `PIP_PYTHON`,
`PIP_TARGET` and `PIP_PREFIX` before launch: pip's initial interpreter selection
can precede its command-specific `--isolated` policy. Interpreter and destination
are bound by authenticated, explicit command arguments instead. The original
installer and setup preserve the caller's declared task-owned `PIP_CACHE_DIR`
alongside the native cache, temporary-directory and guard bindings.

The stdlib-only helper API is `scripts.gnn_offline.load_bundle(directory,
expected_sha256, pin) -> Bundle`, `from_environment(pin) -> Bundle | None`,
and `runtime_fingerprint(executable) -> dict`. The fingerprint contains exactly
the six `runtime` fields above. The setup builder must use this single protocol;
the consumer does not acquire or generate expected source attestations.
Offline interpreter discovery also uses `-I -S -B` before qualification: neither
`.pth` imports nor `sitecustomize.py` may execute during a version probe. The
existing online discovery behavior is unchanged.

Use the separately authorized setup builder described in the root README;
freeze and independently review its native acquisition evidence, source tree,
wheel closure and manifest before selecting its digest. For the native gate's
payload environment, set:

```bash
GNN_OFFLINE_BUNDLE=/absolute/task-owned/prepared-bundle
GNN_OFFLINE_MANIFEST_SHA256=externally_reviewed_64_hex_digest
GNN_PIN_PYTHON=/absolute/task-owned/.gnn-env/fresh-installer/bin/python
```

Then use the **original** `./run.sh gnn` payload under native offline test
admission. These assignments neither perform setup nor grant gate admission.

### Original gate, offline installation

The checker still parses the authenticated upstream `requires-python`, selects
a compatible interpreter, and creates a new temporary pip target. It installs
the complete hash-locked wheel set, then genuinely builds/installs
`git+file://LOCAL_CHECKOUT@ORIGINAL_COMMIT` with dependencies and build isolation,
`--no-index`, the exact wheelhouse and no cache. No GNN wheel or `--no-deps`
shortcut replaces that VCS installation. The verifier checks actual PEP 610
local URL/VCS commit metadata, locked installed versions, dependency closure,
installed wheel library bytes and module containment under that fresh target.
An isolated, no-site child calls the original parse/syntax/literal-`True`
verification and uses the authenticated exemplar bytes instead of HTTPS.
Direct offline `--verify` is refused: it cannot bypass fresh installation.
Receipt document selection and result/scope semantics are unchanged.
Under native execution the offline arm allocates a new target inside
`GITVAULT_EXECUTION_OUTPUT` and retains it without reuse or later mutation as
installation evidence. The receipt's `offline-resources.installed-target`
names it; `retained-installation` is true. Without native output, temporary
cleanup is unchanged. The online path always retains its original cleanup.
Native output also retains `<installed-target-name>-installer-environments.jsonl`:
one completed observation for each original pip child (locked wheels, then pinned
VCS), with its actual PID/return code and cache/config/temporary bindings. Native
guard values are compared with the caller and only the comparison and names are
recorded, never secret values. Both successful records are required to establish
the original installer's environment preservation; setup-child observations do
not substitute for them. Launch or observation-write failures remain failures.

After setup, final freeze and independent review, run the original arm through
native `execute --classification test` offline admission. Do not run tests under
`with-repo`, change a sandbox/profile/shared runtime, or equate setup success
with install-consumer acceptance. Explicitly run `python3 -m unittest
scripts.test_gnn_offline scripts.test_prepare_gnn_offline` with the two bundle variables and
`GNN_OFFLINE_TEST_TARGET` naming the genuine retained target from the original
arm. Missing prerequisites error, never skip. The controls mutate only separate
temporary copies/fixtures, never that installation or native evidence, and do
not accept a positive conformance gate. Neither they nor this source change
claim a full GNN verdict, scientific/corpus replay or Pluto UI acceptance.
