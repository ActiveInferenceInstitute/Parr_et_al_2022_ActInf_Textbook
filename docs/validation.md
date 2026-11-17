# Validation

[`../run.sh`](../run.sh) is the gate registry. `./run.sh --list` prints each exact
command; [CI](../.github/workflows/ci.yml) calls its configured arms unchanged.
On GitVault, project execution requires `execute --classification test`.

```bash
./run.sh --list
./run.sh fast
COURSES_ROOT=/absolute/path/to/qualified/courses ./run.sh education
COURSES_ROOT=/absolute/path/to/qualified/courses ./run.sh full
```

## Arms and boundaries

| Arm | Scope |
| --- | --- |
| `lint` | Tracked Python syntax and JSON/notebook parsing; no style/type-checker claim. |
| `tests` | Hermetic cleaner, GNN protocol, Markdown and education-admission regressions. |
| `plaintext` | Report-only integrity checks on the existing extracted corpus; no writes. |
| `docs` | Markdown destination parsing, existing relative files and documentation-index coverage. |
| `education` | Real producer/member controls followed by the actual member CLI; explicit qualified `COURSES_ROOT` required. |
| `vfe` | Shared `VFEModel`, including supported boundaries and impossible observations; no Pluto runtime. |
| `gnn` | Separately provisioned pinned upstream parser and actual tracked sketches, or the explicitly labelled upstream-exemplar baseline. |

`fast` contains lint, tests, plaintext and docs. `full` additionally requires the
education producer, Julia and GNN prerequisites. There is no `types` arm or
notebook-in-CI requirement.

## Actual education consumer

[`check_education.py`](../scripts/check_education.py) accepts `--courses-root` or
`COURSES_ROOT`, and an optional `--member-checkout`. It loads the selected source
package and authentic registry member, requires the explicit `repo_root` API, and
calls `check_member(None, spec, canonical_schema=..., repo_root=member_checkout)`.
There is no installed/sibling fallback, schema fork or generated curriculum.

The producer validates the pointer, byte-identical schema, all declared bundles,
containment and semantic rules. Pending, malformed and invalid members fail;
none is silently skipped. The receipt contains both roots, identity, bundles,
adoption state and diagnostics. The actual checkout passed with an adopted,
issue-free receipt in the 2026-11-13 bounded qualification.

## Cleaner and Markdown checks

The cleaner removes recognized MIT Press footers and explicit positive-decimal
`Page N` / `Page N of M` lines. Bare numbers, `x`, `i`, `iv`, mixed notation and
ordinary page mentions remain content. Report-only mode preserves input bytes;
`--apply` is an explicit reviewed regeneration step. Character-count equality
alone cannot establish mathematical fidelity. See [plaintext](plaintext-content.md).

The Markdown checker handles titled/angle destinations, balanced parentheses,
escapes, references/continuations, percent/entity decoding, fences and inline code.
It checks real local files; it is not a full Markdown renderer, remote-link checker
or fragment validator.

## Shared model and visual limit

[`vfe_model.jl`](../Chapters/vfe_model.jl) is used by both the notebook and tests.
Impossible observations return no posterior and infinite free energy, without
epsilon smoothing or a posterior plot. The bounded Julia suite passed on 1.13.3;
this does not qualify the notebook's embedded Julia 1.7.3 environment. Pluto is
absent from the prepared runtime, so interactive visual acceptance remains open.

## GNN and CI limits

The unchanged pin and exact conformance scope are in [the GNN pointer](../.github/GNN.md).
Only tracked `*.gnn.md` files enter repository-sketch admission; missing/replaced
tracked files fail, duplicate basenames stage independently, and only literal
`True` is a successful type verdict. Numeric Python constraints retain patch
precision and supported compatible-release semantics; unknown syntax fails closed.
Protocol fixtures do not qualify a real upstream installation.

The original `gnn` arm now has an explicit content-bound offline resource path;
with neither offline variable set it keeps its original online behavior. Authorized
setup acquires the unchanged pin as an installable native Git checkout and the
complete registry-hashed build/runtime wheel closure into new task-owned paths.
Setup is not a test or installation verdict. The exact bundle schema and setup
boundary are in [the GNN pointer](../.github/GNN.md#explicit-prepared-offline-resources).

After final source freeze and independent review, native offline test admission
may run the same `./run.sh gnn` with `GNN_OFFLINE_BUNDLE`,
`GNN_OFFLINE_MANIFEST_SHA256` (an independently reviewed external digest), and
`GNN_PIN_PYTHON` naming its compatible task-owned installer. Missing pairs,
digest/pin/path/symlink/origin/commit/runtime/dependency mismatches fail closed.
The checker still parses the actual pinned `requires-python`, selects an
interpreter, and genuinely performs a fresh isolated-build local Git VCS pip
installation with all declared dependencies. No installed-source reuse,
package-only export, GNN wheel, ambient site package or old `--verify` shortcut
accepts the arm. Exact local PEP 610 origin and installed bytes are checked;
the externally trusted bootstrap guards the original parsing, syntax and
literal-`True` type verdicts. The exemplar is the authenticated pinned byte
sequence, not a network fetch or substituted parser.

Native offline runs retain the new installation under
`GITVAULT_EXECUTION_OUTPUT`; the receipt names
`offline-resources.installed-target`. An additional focused
`python3 -m unittest scripts.test_gnn_offline` control run requires both bundle
variables and `GNN_OFFLINE_TEST_TARGET` pointing to that genuine retained target.
It errors if resources are absent and mutates only separate copies. Its real
negative controls cover manifest/wheel digests, relative escape and symlinks,
actual Git origin/HEAD, runtime binding, installed PEP 610 URL/commit and module
containment. They neither replace nor independently accept the original arm.
The existing hermetic GNN protocol fixtures remain in `./run.sh tests`.

CI's Python job calls lint/tests/docs/plaintext, its Julia job calls vfe, and its
GNN job calls gnn. CI does not yet deliver a qualified `COURSES_ROOT`; local
education acceptance is not hosted CI evidence. This offline implementation
change ran no acquisition, installer, test, build, formatter, linter or gate.
Prior original-GNN and Pluto UI holds remain open until their actual acceptance;
source code, prepared resources and focused controls alone cannot waive them.
Hosted billing, pin migration, glossary authoring and documentation-site policy
remain owner-held.

Generated [`_generated/GATES.md`](_generated/GATES.md) is historical until
`./run.sh report` measures the required final source/runtime. Never edit its
numbers by hand. No corpus, generated timing, full-gate or release renewal is claimed.
