# Documentation TODO — Parr et al. 2022 Active Inference Textbook

**Last reviewed:** 2026-11-01

This backlog records the 2026-08-02 documentation-deep review. Minor means a
small correction such as a typo, broken link, or formatting issue. Medium means
a stale section rewrite, documentation restructure, or missing practical guide.
Major means a large documentation-system overhaul, new documentation site, or
cross-cutting refactor.

## Minor

- [x] **M1 — README inventory and command corrections.** Update the repository
  tree and plaintext-cleaning command to match the checked-in files. Path:
  `README.md`. **Completed in `ee81c0d`.**
- [x] **M2 — Remove stale cleaner option.** Remove the documented but unsupported
  `--verify-only` option. Path: `scripts/clean_plaintext.py`. **Completed in
  `ee81c0d`.**
- [x] **M3 — Clean Chapter 3 notebook prose and link.** Remove draft residue and
  redundant text, correct grammar, and replace the stale pgmpy URL. Path:
  `Chapters/03_blanket.ipynb`. **Completed in `ee81c0d`.**

## Medium

- [x] **M4 — Add contributor guidance.** Document the repository's scope,
  verification commands, generated-text workflow, and licensing. Path:
  `CONTRIBUTING.md`. **Completed in `8ed6500`.**
- [x] **M5 — Add citation metadata.** Add a `CITATION.cff` grounded in the
  textbook citation and verified DOI. Path: `CITATION.cff`. **Completed in
  `8ed6500`.**
- [x] **M6 — Make the review backlog auditable.** Replace the previous review
  summary with dated Minor / Medium / Major sections and an explicit
  open/deferred list. Path: `TODO.md`. **Completed in `8ed6500`.**
- [x] **M7 — Record the review evidence.** Add a dated log of scope, findings,
  and real verification results. Path: `REVIEW_LOG_2026-08-02.md`.
  **Completed in `8ed6500`.**
- [x] **M8 — Signpost the Institute's model-specification material and run the
  gates in CI.** Add a related-resources section to the README with the GNN
  syntax reference and the course and category-theory lessons for the model
  class the simulator demonstrates, run the plaintext integrity check and the
  Julia regression suite on every push and pull request, complete the sidecar
  artifact inventory, and record the pass. Paths: `README.md`,
  `.github/workflows/ci.yml`, `.aii/config.yaml`, `REVIEW_LOG_2026-11-01.md`.
  **Completed in this change.**

## Major

- [ ] **J1 — Documentation site overhaul.** Deferred: a pass-3 documentation
  tree now exists in `docs/` (index, plaintext, chapters, validation), but it is
  plain Markdown. A hosted documentation site would still add maintenance
  without a verified need.

## Open / deferred

- J1 remains deferred for the reason above.
- `Chapters/VFE.jl` is deliberately **not** converted to a GNN document: it is
  an interactive Pluto.jl notebook and a specification would remove the
  interactivity the reading group uses. See `REVIEW_LOG_2026-11-01.md`. Do not
  convert it without a request that asks for exactly that.
- No other findings are intentionally left open after this pass.
