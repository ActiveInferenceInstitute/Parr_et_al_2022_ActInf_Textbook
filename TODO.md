# Documentation TODO — Parr et al. 2022 Active Inference Textbook

**Last reviewed:** 2026-11-16

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
- [x] **M9 — Composable gate entry point with measured arms.** Replace the
  duplicated CI command bodies with one `run.sh` whose arms CI calls unchanged;
  extract the inline GNN conformance script into `scripts/check_gnn_conformance.py`
  (the pin file is the only source of its values); add the `lint` and `docs`
  arms; record per-arm wall time in a generated document. Paths: `run.sh`,
  `scripts/lint_sources.py`, `scripts/check_docs.py`,
  `scripts/check_gnn_conformance.py`, `scripts/gate_report.py`,
  `.github/workflows/ci.yml`, `docs/validation.md`, `docs/_generated/GATES.md`.
  **Completed in `edcab43` (#8)**; the measurements were regenerated on the
  committed tree in `1b0b86a` (#9).
- [x] **M10 — Flat documentation index.** Add `docs/documentation-index.md`,
  link it from the hub, and make the `docs` arm fail when a page is missing from
  the index or a relative link does not resolve. Paths:
  `docs/documentation-index.md`, `docs/README.md`, `scripts/check_docs.py`.
  **Completed in `edcab43` (#8).**
- [x] **M8 — Signpost the Institute's model-specification material and run the
  gates in CI.** Add a related-resources section to the README with the GNN
  syntax reference and the course and category-theory lessons for the model
  class the simulator demonstrates, run the plaintext integrity check and the
  Julia regression suite on every push and pull request, complete the sidecar
  artifact inventory, and record the pass. Paths: `README.md`,
  `.github/workflows/ci.yml`, `.aii/config.yaml`, `REVIEW_LOG_2026-11-01.md`.
  **Completed in `0f9e41d` and `2e16c21`** (merged in #1 and #4).
- [x] **M11 — Adopt the canonical GNN importer pin schema.** Declare
  `gnn-importer-pin/v1` and record the adoption date so the estate reader stops
  reporting `pin-schema-unversioned`. Path: `.github/gnn-pin.json`.
  **Completed in `067e3c9` (#7).**
- [x] **M12 — Adopt the Education contract.** Declare `education-contract/v1`,
  copy the lead schema byte-identically, and transcribe each numbered plaintext
  chapter and each computational notebook as a unit with objectives, a source
  path, and nine advisory reading-order edges. Paths: `education-contract.json`,
  `specs/education/schema.json`, `specs/education/parr-2022.json`, `README.md`.
  **Completed in `37b999c` (#10).** The lead checker accepts the bundle
  (`OK -- 12 unit(s), 9 edge(s), 0 term(s)`) and lists this member as
  `adopted 1 bundle(s)`.
- [x] **M13 — Resolve sidecar document paths the way the validator reads them.**
  The `docs` list is resolved relative to `.aii`, so project-root pages now carry
  a `../` prefix and the two `.aii/docs` pages are listed. Paths:
  `.aii/config.yaml`, `.aii/docs/INTEGRATION.md`. **Completed in `3977a98`
  (#11).**
- [x] **M14 — Wire the GNN unit tests into the gate.** The unit tests merged
  with the fail-closed type check (#13) were manual-only: no `run.sh` arm and no
  CI job ran them, so a broken unit test left `./run.sh fast` and `./run.sh full`
  green. Add the `tests` arm
  (`python3 -m unittest scripts.test_check_gnn_conformance`), include it in
  `fast` and `full`, and run it in the `python arms` CI job. Paths: `run.sh`,
  `.github/workflows/ci.yml`, `docs/validation.md`, `README.md`, `AGENTS.md`,
  `CONTRIBUTING.md`, `docs/README.md`, `.github/GNN.md`,
  `docs/_generated/GATES.md`. **Completed in #14.**

## Major

- [ ] **J1 — Documentation site overhaul.** Deferred: a pass-3 documentation
  tree now exists in `docs/` (index, plaintext, chapters, validation), but it is
  plain Markdown. A hosted documentation site would still add maintenance
  without a verified need.

## Bounded qualification — 2026-11-13

- [x] **T1 — Conservative cleaner.** Ambiguous mathematical lines, retained
  character order, report-only preservation and explicit-file apply controls
  passed. The observed unclosed-read warning was repaired; no corpus regeneration.
- [ ] **T2 — Shared VFE model and interactive acceptance.** Shared Julia boundary
  tests passed, including impossible observations. Pluto is absent from the
  prepared runtime; actual notebook rendering remains outstanding.
- [x] **T3 — GNN admission controls.** Tracked-file identity, duplicate basenames,
  fail-closed verdicts and numeric interpreter constraints passed protocol tests.
  These do not replace real pinned-upstream/installed-runtime qualification.
- [x] **T4 — Markdown destinations.** Real-file and parser controls passed;
  remote links, fragments and full-renderer equivalence are not claimed.
- [x] **T5 — Actual education consumer.** Explicit-root producer controls and the
  actual member CLI passed with adopted state and no issues. No validator fork,
  sibling-layout inference or installed fallback. Hosted producer delivery remains open.

M1–M14 above remain dated history. No generated measurements or release evidence
were renewed by this focused qualification.

## Open / deferred

- J1 remains deferred for the reason above: `docs/` is plain Markdown and
  `./run.sh docs` checks its links and index coverage, but there is no hosted
  site.
- There is no `types` arm and no style linter: the repository ships nothing that
  would consume either, so `./run.sh lint` stops at syntax and JSON validity.
- `Chapters/VFE.jl` is deliberately **not** converted to a GNN document: it is
  an interactive Pluto.jl notebook and a specification would remove the
  interactivity the reading group uses. See `REVIEW_LOG_2026-11-01.md`. Do not
  convert it without a request that asks for exactly that.
- Hosted evidence is bound to an actual immutable head: the original software
  candidate `de129d861325f1c80bebd4148a91b9657b380376` in
  [PR #15](https://github.com/ActiveInferenceInstitute/Parr_et_al_2022_ActInf_Textbook/pull/15)
  passed all six named hosted checks on 2026-11-16, including pinned GNN,
  Python arms and VFE. Earlier billing negatives remain historical evidence;
  neither they nor that success decide later heads or Pluto visual acceptance.
- Main [PR #16](https://github.com/ActiveInferenceInstitute/Parr_et_al_2022_ActInf_Textbook/pull/16)
  moved the importer to `v5.1.0` at
  `75c834bd8519dc7b5adc4d24f16bf393cfd1ecdf`, preserving its `OWNER/REPO`
  and `revision` schema. This continuation retains that published owner decision.
  The original `e323329` source's full fresh-install `v5.0.3` baseline passed;
  its receipt retains the original pin and does not qualify the new pin or head.
  Current offline resources must match the independent `v5.1.0` manifest and
  complete installable source; qualification still executes the original fresh
  VCS installation and parse/syntax/type checks. No package-only source guard,
  prior installed parser or older hosted result substitutes for that arm.
- The education bundle's glossary is empty, and the lead checker reports
  `0 term(s)`: `specs/education/parr-2022.json` carries no controlled
  vocabulary, which `README.md` records as a deliberate limit of this
  migration. It does not block bundle emission; authoring terms is curriculum
  work owned by the `courses` content authors.
- The education arm now validates this actual member through an explicitly
  selected qualified `COURSES_ROOT`; its real consumer proof passed locally.
  CI delivery of that qualified producer remains operationally unqualified.
- `inferactively-pymdp` has nothing to pin here: the repository ships no
  `requirements.txt`, `pyproject.toml`, or `setup.py`, and every script under
  `scripts/` imports only the standard library.
- Keep J1 and TD1–TD8 boundaries: no types/style arm, GNN conversion,
  notebook-in-CI change, hosted billing claim, unrequested pin migration,
  glossary invention, pymdp dependency or corpus regeneration.
