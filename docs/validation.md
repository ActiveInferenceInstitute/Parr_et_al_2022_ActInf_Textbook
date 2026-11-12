# Validation

One entry point covers this repository: `./run.sh`. It exposes separately
runnable arms, and [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)
calls those arms instead of repeating their commands — a local arm and its CI
job execute the same command line.

```bash
./run.sh --list   # every arm and its exact command
./run.sh fast     # lint + plaintext + docs (no Julia, no network)
./run.sh full     # every arm
./run.sh report   # rewrite docs/_generated/GATES.md with measured wall times
```

## Arms

| Arm | Exact command | What it proves | CI job key / display name |
| --- | --- | --- | --- |
| `lint` | `python3 scripts/lint_sources.py` | Every tracked Python file compiles; every tracked `.json`/`.ipynb` parses. | `plaintext` / `python arms (lint, docs, plaintext)` |
| `plaintext` | `python3 scripts/clean_plaintext.py` | The non-whitespace integrity invariant holds across `TextbookContent/PlainText/*.txt`; nothing is written. | `plaintext` / `python arms (lint, docs, plaintext)` |
| `docs` | `python3 scripts/check_docs.py` | Every relative link in tracked Markdown resolves; every page under `docs/` is reachable from [`documentation-index.md`](documentation-index.md), and the hub links that index. | `plaintext` / `python arms (lint, docs, plaintext)` |
| `vfe` | `julia Chapters/test_vfe.jl` | The VFE simulator's mathematics: normalized posterior, free energy minimised at the exact posterior, inference lowers it, finiteness on the interior. | `vfe` / `VFE regression tests` |
| `gnn` | `python3 scripts/check_gnn_conformance.py` | The pinned GNN parser installs at the pin's revision, its version equals the pin's tag, and every repository `*.gnn.md` sketch — or the pinned upstream exemplar when there is none — parses and type-checks (the type checker must return exactly `True`); the receipt's `scope`/`result` distinguish repository content from the pinned-exemplar baseline. | `gnn-conformance` / `gnn conformance (pinned)` |

There is no `types` arm: the repository ships no type checker and nothing that
would consume one. `lint` deliberately stops at syntax and JSON validity for the
same reason — there is no style linter to run.

Measured wall time per arm, the plaintext file count and the VFE assertion count
live in [`_generated/GATES.md`](_generated/GATES.md), which `./run.sh report`
rewrites; do not hand-edit those numbers.

## Plaintext integrity

[`../scripts/clean_plaintext.py`](../scripts/clean_plaintext.py) in its default
report-only mode prints, for every file, the observed and expected
non-whitespace counts and asserts they match. `--apply` rewrites the files in
place instead; see [plaintext-content.md](plaintext-content.md).

## VFE regression

[`../Chapters/test_vfe.jl`](../Chapters/test_vfe.jl) re-implements the model from
`Chapters/VFE.jl` deterministically (no Pluto, no `@bind`) and needs only
Julia's standard `Test` library. See [chapters.md](chapters.md).

## GNN conformance

The pin is [`.github/gnn-pin.json`](../.github/gnn-pin.json), schema
`gnn-importer-pin/v1`: repository
`ActiveInferenceInstitute/Generalized_Notation_Notation`, tag `v5.0.3`, revision
`8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1`, recorded `2026-11-12`. The script
reads that file and repeats none of its values, so bumping the pin is a
one-file change.

What the job parses is recorded in [`../.github/GNN.md`](../.github/GNN.md):
every `*.gnn.md` in the repository, or — when the repository declares no sketch,
as now — the pinned upstream `input/gnn_files/basics/static_perception.md`
exemplar. That is a pipeline and pin conformance baseline, not a claim that this
repository contains a model.

The arm needs network access (`pip` and `raw.githubusercontent.com`). It installs
the pinned parser into a throwaway directory, so the working environment is left
alone. The pinned package declares `requires-python = ">=3.11,<3.15"` in its own
`pyproject.toml`; the script reads that at the pinned revision and picks a
satisfying interpreter from `PATH` (`GNN_PIN_PYTHON` overrides the search). On a
host whose default `python3` is newer than that range it says which interpreter
it skipped and which one it used.

## What CI runs, and what it installs

- `plaintext` job — `./run.sh lint`, `./run.sh docs`, `./run.sh plaintext`. The
  arms are standard-library Python, so this job uses the runner's `python3` and
  has no setup or install step.
- `vfe` job — `./run.sh vfe`, with `julia-actions/setup-julia`.
- `gnn-conformance` job — `./run.sh gnn`, with `actions/setup-python` pinned to
  `3.12`; the arm installs the pinned parser itself.

Action pins used by the workflow: `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1`
(v7.0.1), `actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0`
(v7.1.0) and `julia-actions/setup-julia@da908477b5db94c10ffce8cfea9f2b3b9d5db687`
(v3.0.3). The workflow does **not** use the Institute composite action
`ActiveInferenceInstitute/.github/.github/actions/setup-python-uv@7159e67315330aac8e414aebae0ad1e999a41448`;
no arm needs `uv`, a lockfile or a virtual environment.

## Not covered

- `Chapters/VFE.jl` is an interactive Pluto.jl notebook with no headless entry
  point, so no arm executes it; `Chapters/test_vfe.jl` covers the same model.
- Regenerating the plaintext from the PDF stays a reviewed manual step.
- There is no documentation-site build (see [`../TODO.md`](../TODO.md) J1) and no
  Markdown linter; `./run.sh docs` is the documentation gate.
- There is no installable package, dependency manifest or manuscript directory,
  so packaging, dependency-lint and manuscript-render gates do not apply.
