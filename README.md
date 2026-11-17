# Parr et al. 2022 — Active Inference Textbook

Study materials and extracted plaintext for the Active Inference Institute's reading
group based on:

> Parr, T., Pezzulo, G., & Friston, K. J. (2022). *Active Inference: The Free
> Energy Principle in Mind, Brain, and Behavior*. MIT Press.
> ISBN 978-0-262-36997-8.

## About

This repository is curated by the Active Inference Institute's Textbook Group. It
collects the original open-access PDF, machine-readable plaintext extractions of its
chapters and appendices, and computational notes (Julia / Jupyter) produced by the
reading group.

## Documentation

- [`docs/README.md`](docs/README.md) — documentation hub and reading order.
  - [`docs/documentation-index.md`](docs/documentation-index.md) — flat index of every long-lived document.
  - [`docs/plaintext-content.md`](docs/plaintext-content.md) — the generated plaintext tree and its integrity invariant.
  - [`docs/chapters.md`](docs/chapters.md) — the computational notes and how to run them.
  - [`docs/validation.md`](docs/validation.md) — the `./run.sh` arms and the CI jobs that call them.
  - [`docs/_generated/GATES.md`](docs/_generated/GATES.md) — generated per-arm wall time and gate facts.
- [`AGENTS.md`](AGENTS.md) — guidance for automated agents.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — contribution scope and verification commands.
- [`TODO.md`](TODO.md) — dated documentation backlog and review log.
- [`CITATION.cff`](CITATION.cff) — machine-readable citation metadata.

## Repository layout

```
ActInf_Textbook_2022.pdf            — the open-access textbook PDF (MIT Press)
TextbookContent/PlainText/          — cleaned plaintext of the textbook:
  1-ActInf22.txt .. 10-ActInf22.txt   … chapters 1–10 (file 1 also holds the front matter)
  Appendix_A/B/C-ActInf22.txt        … appendices A–C
  Notes-ActInf22.txt                 … the book's endnotes
Chapters/
  README.md                          — folder guide for the computational notes
  VFE.jl                             — Pluto.jl notebook: Variational Free Energy Simulator
  vfe_model.jl                       — shared VFEModel used by the notebook and tests
  test_vfe.jl                        — Julia regression tests for the VFE simulator
  03_blanket.ipynb                   — Chapter 3 (The High Road) Jupyter notes
docs/                                — repository documentation (hub: docs/README.md,
                                       flat index: docs/documentation-index.md)
scripts/
  clean_plaintext.py                 — reproducible PlainText cleaning pipeline
  test_clean_plaintext.py            — conservative cleaner regressions
  lint_sources.py                    — `./run.sh lint` arm: Python compiles, JSON parses
  check_docs.py                      — `./run.sh docs` arm: relative links and docs index
  test_check_docs.py                 — Markdown destination and real-file regressions
  check_education.py                 — explicit-root courses producer adapter
  test_check_education.py            — admission and real producer/member controls
  check_gnn_conformance.py           — `./run.sh gnn` arm: pinned GNN parser conformance
  test_check_gnn_conformance.py      — `./run.sh tests` arm: unit tests for the GNN arm's fail-closed type check and receipt labels
  gate_report.py                     — `./run.sh report` arm: writes docs/_generated/GATES.md
run.sh                               — single gate entry point; CI calls its arms
.aii/config.yaml                     — InstituteOS sidecar metadata manifest
.github/workflows/ci.yml             — CI: calls the ./run.sh arms (lint, tests, docs,
                                       plaintext, vfe, gnn)
CONTRIBUTING.md                      — contribution scope and verification commands
CITATION.cff                         — machine-readable citation metadata
LICENSE                              — CC-BY-4.0
TODO.md                              — project backlog and review log
REVIEW_LOG_<date>.md                 — dated documentation review logs (2026-08-02, 2026-11-01)
```

The plaintext chapters are cleaned with `scripts/clean_plaintext.py` (MIT-Press
download footers and explicitly labelled `Page N` / `Page N of M` lines removed,
long prose lines wrapped; ambiguous bare numbers and Roman numerals are retained).
To regenerate, re-extract from the PDF and run `python3 scripts/clean_plaintext.py --apply`
(the default invocation is report-only; `--apply` writes the cleaned files in place).

## Running the computational notebooks

- `Chapters/VFE.jl` is a [Pluto.jl](https://plutojl.org) notebook. Open it with
  `julia -e 'using Pluto; Pluto.run()'` and load the file. Dependencies are pinned
  in the notebook's embedded manifest (Julia 1.7.3).
- Verify the shared `VFEModel` with `./run.sh vfe`. Supported observations have
  normalized posteriors; impossible observations have no posterior and infinite
  free energy. Headless mathematics does not certify the Pluto surface.
- `Chapters/03_blanket.ipynb` is a standard Jupyter notebook (Python 3 kernel), using
  only the standard library. Open with `jupyter notebook Chapters/03_blanket.ipynb`.

Every gate is an arm of one entry point, `./run.sh`, and CI calls those same
arms (`.github/workflows/ci.yml`):

```bash
./run.sh --list   # every arm and its exact command
./run.sh fast     # lint + tests + plaintext + docs
COURSES_ROOT=/absolute/path/to/qualified/courses ./run.sh full
```

`plaintext` checks the integrity invariant; `tests` runs hermetic cleaner, GNN
protocol, Markdown and education-admission controls. `education` requires the
explicit qualified producer and checks this actual checkout; `vfe` tests the shared
model. `gnn` retains its separately provisioned pinned baseline (see `.github/GNN.md`).
The original 2026-11-13 bounded qualification did not run a full gate, install GNN,
regenerate the corpus or certify Pluto; the prepared Julia runtime has no Pluto.
Arm details are in
[`docs/validation.md`](docs/validation.md); measured wall times are in
[`docs/_generated/GATES.md`](docs/_generated/GATES.md). The Pluto notebook
itself is interactive and is not executed in CI.

### Preparing the original GNN arm for offline admission

The online default remains the original pinned acquisition and installation.
For offline native test admission, first acquire the exact pinned **installable
Git checkout** under authorized setup admission, retain genuine origin/admission
evidence, and inspect its immutable packaging hooks. A package-only source export
or an already installed parser is not a substitute. Create a new CPython 3.12
installer environment under `.gnn-env/`; never replace a shared or source-bound
runtime. Then prepare the complete declared runtime/build wheel closure:

```bash
python3 -I -S -B scripts/prepare_gnn_offline.py \
  --bundle "$GNN_ACQUISITION_ROOT" --source "$GNN_SOURCE_ROOT" \
  --python "$GNN_SETUP_PYTHON" --admission "$GNN_ACQUISITION_RECEIPT" \
  --identity "$GNN_IDENTITY_RECEIPT" --package-manifest "$GNN_SOURCE_MANIFEST" \
  --bootstrap "$GNN_BOOTSTRAP"
```

Setup acquires actual registry-advertised wheels and preserves their hashes,
the independently trusted source inventory for the current pin and reviewed bootstrap.
It inspects the installer with no-site startup, reads metadata as data and
authenticates pip against its actual registry-advertised wheel before executing
its genuine CLI. `.pth`/`sitecustomize` and incomplete acquisition receipts fail.
Its printed digest is only a candidate for **independent source/resource review**, not
self-issued acceptance. If a diagnosed setup completed acquisition and installer
preparation but stopped before freezing, explicit `--seal-prepared` validates the
retained exact records without repeating network or installation; changed or
missing resources fail rather than being overwritten. After independent review
freezes the expected digest, run the same original arm through native offline
test admission:

```bash
GNN_OFFLINE_BUNDLE="$GNN_ACQUISITION_ROOT" \
GNN_OFFLINE_MANIFEST_SHA256="$GNN_REVIEWED_MANIFEST_SHA256" ./run.sh gnn
```

The arm still checks `requires-python`, installs into a fresh target from the
genuine pinned local Git source with isolated build and all locked dependencies,
and performs its original parse, syntax and literal-`True` type checks. Missing,
changed or wrong-origin resources fail; no installed-package fallback is used.
See [the bundle protocol](.github/GNN.md) for exact inputs and scope. This path
does not execute scientific notebooks, regenerate content or accept Pluto's UI.


## Education contract

[`education-contract.json`](education-contract.json) declares adoption of the
[Education workflow contract](https://github.com/ActiveInferenceInstitute/courses/blob/main/docs/workflows/education.md)
owned by `courses`. [`specs/education/schema.json`](specs/education/schema.json)
is a byte-identical copy of that lead's schema;
[`specs/education/parr-2022.json`](specs/education/parr-2022.json) is an authored
transcription, not a new curriculum.

The bundle includes each numbered plaintext chapter and each computational
notebook. Appendices, endnotes, front matter, and the Julia regression script
are not separate chapter/notebook units. Titles retain the source wording
(without chapter-number prefixes). Objectives quote the chapters' stated aims,
joining extraction line breaks with spaces rather than inventing learner outcomes.
The bundle's provenance revision identifies the source material transcribed.

- Chapter objectives come from their introductions.
- The blanket notebook uses the aim in the introduction to
  [the high-road chapter](TextbookContent/PlainText/3-ActInf22.txt):
  “The chapter discloses the formal equivalence…” through
  “…Bayesian perspectives on adaptive systems.”
- The VFE notebook uses the aim in “From Bayesian Inference to Free Energy” in
  [the generative-models chapter](TextbookContent/PlainText/4-ActInf22.txt):
  “In this section, we recap…” through “…drawing inferences about the world.”
- Consecutive chapter edges follow “Structure of the Book” in
  [the overview](TextbookContent/PlainText/1-ActInf22.txt); each rationale quotes
  its next-chapter description. These are **soft**, advisory reading-order edges,
  not mandatory prerequisites: the book explicitly permits skipping its formal
  generative-models chapter. No notebook ordering or hard dependency is invented.
- The glossary is empty; this migration does not author a new term corpus.

Select the qualified lead checkout explicitly; no sibling layout, installed
package fallback, symlink arrangement, synchronization or local validator is used:

```bash
COURSES_ROOT=/absolute/path/to/qualified/courses ./run.sh education
```

The adapter loads the actual producer's registry and calls
`check_member(None, spec, canonical_schema=..., repo_root=member_checkout)`.
It checks the authentic member identity, pointer, byte-identical schema, every
declared bundle, containment and producer semantic rules. Missing, malformed,
pending or invalid members fail rather than skip. Its JSON receipt names both
source roots, declared bundles, adoption state and issues. The actual member
passed with `state=adopted`, `ok=true` and no issues in bounded local qualification.
Other members and the deliberately empty glossary are not authored here.

## Related resources

The VFE simulator implements a static-perception model: one binary hidden state,
one binary observation, a likelihood, and a posterior over the hidden state. The
Institute writes models of that class down in
[Generalized Notation Notation](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation)
(GNN), its plain-text specification format for generative models. This
repository teaches the model rather than specifying it, so nothing here is
declared in GNN today; these are the places to look when a model in this
repository, or in the book behind it, needs a written specification.

- [GNN syntax reference](https://github.com/ActiveInferenceInstitute/Generalized_Notation_Notation/blob/main/docs/gnn/gnn_syntax.md)
  — the format specification. That link follows the repository's `main` branch
  rather than a pinned revision; the separate CI conformance job pins its own
  GNN revision in [`.github/gnn-pin.json`](.github/gnn-pin.json).
- [GNN Syntax Track](https://github.com/ActiveInferenceInstitute/courses/tree/main/course_development/gnn/01_gnn_syntax)
  — its `models/static_perception.md` is the closest worked example to
  `Chapters/VFE.jl`: one hidden state, one observation, the same likelihood.
- [Map the model](https://github.com/ActiveInferenceInstitute/ActiveInferenceCategoryTheory/tree/main/gnn)
  — the category-theory lesson that reads such a model as a morphism;
  `learner_perception_model.md` is its perception example.
- [Active Inference Ontology](https://github.com/ActiveInferenceInstitute/Active_Inference_Ontology)
  — the controlled term set the GNN documents annotate.

The plaintext editions of *Active Inference: The Free Energy Principle in Mind,
Brain, and Behavior* remain the source of record for the mathematics in this
repository. A GNN document expresses a model in text; it does not replace the
book's derivations.

## Provenance and citation

- **Source text:** the plaintext files were extracted from the open-access textbook
  PDF and cleaned with the historical cleaner. The current conservative cleaner
  removes only recognized footers and explicit pagination; no corpus regeneration
  was performed during its qualification.
- **License:** this repository is released under CC-BY-4.0 (see `LICENSE`).
  The underlying textbook is published open access by MIT Press; consult the PDF for
  the book's own terms.
- **Cite the book:** Parr, T., Pezzulo, G., & Friston, K. J. (2022). *Active
  Inference: The Free Energy Principle in Mind, Brain, and Behavior*. MIT Press.
  Open-access edition: <https://doi.org/10.7551/mitpress/12441.001.0001>.

## The InstituteOS sidecar

`.aii/config.yaml` is the Active Inference Institute (InstituteOS) metadata manifest
for this repository (schema `aii_platform.aii_sidecar`, marker `aii-sidecar/v1`). It
records the federated relationships, artifact inventory, and provenance for the
Institute's catalog. The rendered companion is
[`.aii/docs/INTEGRATION.md`](.aii/docs/INTEGRATION.md).
