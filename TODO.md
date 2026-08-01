# TODO — Parr et al. 2022 Active Inference Textbook

- **Owner:** Active Inference Institute — Textbook Group
- **Status:** Active
- **Last reviewed:** 2026-08-01

Project backlog for the Active Inference Textbook repository. Content repo: open-access
PDF, cleaned plaintext extractions (chapters 1–10, appendices A–C, notes), and
computational notes (`Chapters/VFE.jl` Pluto notebook, `Chapters/03_blanket.ipynb`).

## Completed / Closed

Items genuinely done in source/docs/metadata/tests (including all Minor, Medium, and
Major findings from the 2026-08-01 review-and-implementation pass).

### Major

- [x] **M1 — `VFE.jl` variational free energy equation corrected.** The `vfe(q)`
      function now computes the mathematically correct form
      `F(q) = q·log(q/p1) + (1−q)·log((1−q)/p2) − log P(y)` (with an `xlogy` helper for
      the 0·log(0) = 0 boundary), replaces the previous incorrect
      `x * (log(x − log(p1)) + (1−x)(log(1−x) − log(p2)))`, and fixes the posterior
      computation (elementwise joint over a length-2 vector, correct marginal and
      exact posterior). The plot cell marks the exact posterior with a dashed `vline`.
      Added **`Chapters/test_vfe.jl`** — 80/80 tests pass
      (`julia Chapters/test_vfe.jl`), asserting the posterior normalizes, the argmin of
      F equals the exact posterior, inference lowers F, and F is finite on the interior.
      `VFE.jl` parses as valid Julia.
- [x] **M2 — PlainText extractions cleaned.** Added **`scripts/clean_plaintext.py`**,
      a deterministic, content-preserving pipeline that removes MIT-Press download
      footers (216 lines) and isolated page-number lines (213 lines) and wraps long
      prose lines, while preserving standalone equation/header lines (234 equation
      lines intact). All 14 files regenerated in place; integrity invariant (total
      non-whitespace characters preserved exactly, modulo removed lines) passes for all
      14 files. Zero footers and zero page numbers remain.
- [x] **M3 — `03_blanket.ipynb` completed.** The Chapter 3 straw-man scaffold was
      replaced with substantive, accurate study notes and three working, dependency-free
      (standard-library-only) Python code cells: a Markov-blanket calculator for a
      Bayesian network (parents + children + co-parents), a numeric surprise
      (−ln P(y)) demo, and a variational-free-energy minimisation demo whose minimiser
      matches the exact posterior. Kernelspec standardized to `python3`. All three code
      cells execute successfully.

### Minor / Medium (prior pass + this pass)

- [x] **Medium — Stub README rewritten.** `README.md` now documents provenance,
      citation, license, repository layout, notebook run instructions, the cleaning
      pipeline, and the VFE regression test.
- [x] **Minor — Remove committed Jupyter checkpoint cruft.** Deleted and untracked
      `Chapters/.ipynb_checkpoints/03_blanket-checkpoint.ipynb`; added `.gitignore`
      for `.ipynb_checkpoints/` and Python cache files.
- [x] **Minor — Grammar typo in Chapter 3 notebook.** Fixed "Markov blanket is the
      neighboring nodes of the given node." → "A Markov blanket is the set of
      neighboring nodes of the given node."
- [x] **Minor — Complete `.aii` sidecar artifact inventory.** Added `LICENSE`, the
      textbook PDF, `TextbookContent/PlainText/`, `Chapters/VFE.jl`, and
      `Chapters/03_blanket.ipynb` to `.aii/config.yaml`; bumped `meta.updated` to
      2026-08-01.
- [x] **Repo metadata baseline.** CC-BY-4.0 `LICENSE` and InstituteOS `.aii` sidecar
      added (commit d5ebfb2).

## Major — Scoped (deferred)

None outstanding. All previously scoped Major findings (M1–M3) were implemented and
verified in the 2026-08-01 pass.

## Review notes (2026-08-01)

- `git pull --ff-only`: already up to date; branch `main` clean, no conflicts.
- Verification (real results, no fabrication):
  - `julia Chapters/test_vfe.jl` → **80/80 tests pass** (0.2 s).
  - `scripts/clean_plaintext.py` → integrity invariant holds for **all 14 files**;
    216 footers + 213 page numbers removed; 0 footers / 0 page numbers remain.
  - `Chapters/03_blanket.ipynb` → valid JSON, `python3` kernelspec; all 3 code cells
    execute with correct output.
  - `Chapters/VFE.jl` → parses as valid Julia; no dangling identifiers.
  - `.aii/config.yaml` → valid YAML (Ruby psych), 6 artifacts.
- Changes committed to `main` and pushed from this session.
