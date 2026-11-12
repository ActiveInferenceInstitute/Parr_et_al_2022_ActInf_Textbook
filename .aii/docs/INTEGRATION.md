# InstituteOS integration — Parr_et_al_2022_ActInf_Textbook

## Identity

| Field | Value |
| --- | --- |
| Repository | `ActiveInferenceInstitute/Parr_et_al_2022_ActInf_Textbook` |
| Affiliation | `institute` |
| Category | `education` |
| Status | `active` |
| Maturity | `released` |
| Steward | Active Inference Institute |
| Default branch | `main` |
| Current release | — |
| License | `CC-BY-4.0` |
| Citation | Active Inference Institute — Parr_et_al_2022_ActInf_Textbook. |

## Federation

| Setting | Value |
| --- | --- |
| Dashboard mode | `repos` |
| Analytics | `true` |
| Dashboard | `true` |
| Sync policy | `pull` |
| Registries | — |
| Tags | parr, 2022, actinf, textbook, julia |

## Ecosystem relations

| Repository | Relation | Note |
| --- | --- | --- |
| `ActiveInferenceInstitute/InstituteOS` | `referenced-by` | Federated via the InstituteOS .aii manifest. |
| `ActiveInferenceInstitute/Active_Inference_Ontology` | `references` | Uses Active Inference Ontology terms. |
| `ActiveInferenceInstitute/ActiveInferenceJournal` | `referenced-by` | Featured in Institute materials. |
| `ActiveInferenceInstitute/Generalized_Notation_Notation` | `references` | Related-resources signposting only; this repository declares no GNN document. |

## Key artifacts

| Path | Kind | Description |
| --- | --- | --- |
| `README.md` | `doc` | Repository overview. |
| `LICENSE` | `doc` | CC-BY-4.0 license for repository content. |
| `ActInf_Textbook_2022.pdf` | `doc` | Open-access textbook PDF (Parr, Pezzulo & Friston 2022, MIT Press). |
| `TextbookContent/PlainText/` | `data` | Plaintext extractions of chapters 1-10, appendices A-C, and notes. |
| `Chapters/VFE.jl` | `code` | Pluto.jl notebook - Variational Free Energy Simulator. |
| `Chapters/test_vfe.jl` | `test` | Julia regression tests for the VFE simulator. |
| `Chapters/03_blanket.ipynb` | `notebook` | Chapter 3 (Markov blankets) Jupyter notes. |
| `scripts/clean_plaintext.py` | `tool` | Deterministic PlainText cleaning pipeline (footers/page numbers). |
| `run.sh` | `tool` | Single gate entry point; the CI workflow calls its arms. |
| `scripts/lint_sources.py` | `tool` | Lint arm - tracked Python compiles, tracked JSON/notebooks parse. |
| `scripts/check_docs.py` | `tool` | Docs arm - relative links resolve and docs/ pages are indexed. |
| `scripts/check_gnn_conformance.py` | `tool` | GNN arm - pinned parser conformance read from .github/gnn-pin.json. |
| `scripts/gate_report.py` | `tool` | Report arm - writes docs/_generated/GATES.md with measured wall times. |
| `docs` | `doc` | Documentation hub, flat index, and topic guides (plaintext content, chapters, validation). |
| `.github/workflows/ci.yml` | `code` | CI workflow calling the ./run.sh arms (lint, docs, plaintext, vfe, gnn). |
| `CONTRIBUTING.md` | `doc` | Contribution scope, conventions, and verification commands. |
| `CITATION.cff` | `doc` | Machine-readable citation metadata for the textbook and this repository. |
| `TODO.md` | `doc` | Dated documentation backlog with open and deferred items. |
| `AGENTS.md` | `doc` | Agent guidance. |
| `REVIEW_LOG_2026-08-02.md` | `doc` | Repository artifact. |
| `REVIEW_LOG_2026-11-01.md` | `doc` | Repository artifact. |

## Portable tasks

| Task | Command | Working directory | Description |
| --- | --- | --- | --- |
| `inventory` | `git ls-files` | `.` | List tracked files. |

## Validation

```bash
python -m aii_platform.aii_sidecar.validate <repo> --completeness
python -m aii_platform.aii_sidecar docs <repo> --overwrite
python -m aii_platform.aii_sidecar.run <repo> --list
```

The sidecar is valid when `validate` prints `OK` and reports no missing artifact,
manifest, link, or declared-doc path. Completeness is a curation target, not a
runtime requirement.

## Data boundary

This sidecar carries metadata only. It does not grant execution permission, does not
replace the repository's own documentation, and must not be used to move private
content into a public repository. Task execution is limited to trusted checkouts.
