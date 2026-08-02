# Documentation TODO — Parr et al. 2022 Active Inference Textbook

**Last reviewed:** 2026-08-02

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

## Major

- [ ] **J1 — Documentation site overhaul.** Deferred: this repository has no
  `docs/` site and is a small source-and-study-materials repository; a new site
  would add maintenance without a verified need.

## Open / deferred

- J1 remains deferred for the reason above. No other findings are intentionally
  left open after this pass.
