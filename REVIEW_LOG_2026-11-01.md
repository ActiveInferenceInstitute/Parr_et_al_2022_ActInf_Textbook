# Documentation review log — 2026-11-01

## Scope

Reviewed the repository root, `README.md`, `TODO.md`, `CONTRIBUTING.md`,
`CITATION.cff`, `.aii/config.yaml`, `scripts/clean_plaintext.py`,
`Chapters/VFE.jl`, `Chapters/test_vfe.jl`, and the 14 plaintext files under
`TextbookContent/PlainText/`. The 2026-08-02 pass had already corrected the
README inventory, the cleaner's options, and the Chapter 3 notebook. This pass
adds the Institute's cross-repository signposting and machine verification of
the two documented gates.

## Findings

- Minor: the README described the repository's own files but never pointed at
  the Institute's model-specification material. The binary perception model the
  VFE simulator demonstrates now has a documented home in Generalized Notation
  Notation, and the repository neither linked it nor recorded that it had been
  considered.
- Medium: the two checks the README and `CONTRIBUTING.md` require —
  `python3 scripts/clean_plaintext.py` and `julia Chapters/test_vfe.jl` — ran
  only by hand. Nothing verified them on a push or pull request.
- Minor: `.aii/config.yaml` predated `CONTRIBUTING.md`, `CITATION.cff`,
  `TODO.md`, and the review logs, so its artifact inventory did not cover the
  repository's own documentation.
- Major: unchanged from the 2026-08-02 pass — a documentation site is still not
  justified for a small source-and-study-materials repository.

## Verification performed

- `python3 scripts/clean_plaintext.py`: 14/14 integrity checks passed. The
  default mode is report-only and wrote no files.
- `julia Chapters/test_vfe.jl`: 80/80 tests passed (Julia 1.13.3).
- `git ls-files`: the plaintext inventory, the notebooks, the scripts, and the
  new workflow are all either job needs; neither job requires a secret, a
  token, or an external service, and neither modifies the checkout.
- Every external link added in this pass was resolved in its own repository
  before being committed: `courses/course_development/gnn/01_gnn_syntax/models/static_perception.md`,
  `ActiveInferenceCategoryTheory/gnn/learner_perception_model.md`, and the GNN
  syntax guide `docs/gnn/gnn_syntax.md` all exist on their repository's `main`.

## Decisions

- `Chapters/VFE.jl` stays an interactive Pluto.jl notebook and is deliberately
  **not** rewritten as a GNN document. Its purpose is to let a reader move a
  slider and watch the free energy change; a specification would remove exactly
  that interactivity. The model class it demonstrates is a linked GNN exemplar
  instead. Do not convert it later without a request that asks for that.
- CI covers the two documented gates only. It does not execute the Pluto
  notebook and does not regenerate the plaintext, which needs the PDF and stays
  a reviewed manual step.
