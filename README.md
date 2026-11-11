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

## Repository layout

```
ActInf_Textbook_2022.pdf            — the open-access textbook PDF (MIT Press)
TextbookContent/PlainText/          — cleaned plaintext of the textbook:
  1-ActInf22.txt .. 10-ActInf22.txt   … chapters 1–10 (file 1 also holds the front matter)
  Appendix_A/B/C-ActInf22.txt        … appendices A–C
  Notes-ActInf22.txt                 … the book's endnotes
Chapters/
  VFE.jl                             — Pluto.jl notebook: Variational Free Energy Simulator
  test_vfe.jl                        — Julia regression tests for the VFE simulator
  03_blanket.ipynb                   — Chapter 3 (The High Road) Jupyter notes
scripts/
  clean_plaintext.py                 — reproducible PlainText cleaning pipeline
.aii/config.yaml                     — InstituteOS sidecar metadata manifest
.github/workflows/ci.yml             — CI: plaintext integrity check, VFE regression tests,
                                       pinned GNN conformance baseline
CONTRIBUTING.md                      — contribution scope and verification commands
CITATION.cff                         — machine-readable citation metadata
LICENSE                              — CC-BY-4.0
TODO.md                              — project backlog and review log
REVIEW_LOG_<date>.md                 — dated documentation review logs (2026-08-02, 2026-11-01)
```

The plaintext chapters are cleaned with `scripts/clean_plaintext.py` (MIT-Press
download footers and isolated page-number lines removed, long prose lines wrapped;
standalone equation/header lines are preserved). To regenerate them from the raw
extraction, re-extract from the PDF and run `python3 scripts/clean_plaintext.py --apply`
(the default invocation is report-only; `--apply` writes the cleaned files in place).

## Running the computational notebooks

- `Chapters/VFE.jl` is a [Pluto.jl](https://plutojl.org) notebook. Open it with
  `julia -e 'using Pluto; Pluto.run()'` and load the file. Dependencies are pinned
  in the notebook's embedded manifest (Julia 1.7.3).
- Verify the simulator's math with `julia Chapters/test_vfe.jl` (asserts the free
  energy is minimised at the exact posterior across the slider range).
- `Chapters/03_blanket.ipynb` is a standard Jupyter notebook (Python 3 kernel), using
  only the standard library. Open with `jupyter notebook Chapters/03_blanket.ipynb`.

Both documented gates run in CI (`.github/workflows/ci.yml`):
`python3 scripts/clean_plaintext.py` for the plaintext integrity invariant and
`julia Chapters/test_vfe.jl` for the simulator's mathematics. The Pluto notebook
itself is interactive and is not executed in CI.

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
  — the format specification. That link follows the repository's `main` branch;
  this repository pins no GNN revision.
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
  PDF and cleaned with `scripts/clean_plaintext.py` (download footers and isolated
  page numbers removed; equation lines preserved). The cleaning is reproducible from
  the PDF source of record.
- **License:** this repository is released under CC-BY-4.0 (see `LICENSE`).
  The underlying textbook is published open access by MIT Press; consult the PDF for
  the book's own terms.
- **Cite the book:** Parr, T., Pezzulo, G., & Friston, K. J. (2022). *Active
  Inference: The Free Energy Principle in Mind, Brain, and Behavior*. MIT Press.
  Open-access edition: <https://doi.org/10.7551/mitpress/12441.001.0001>.

## The InstituteOS sidecar

`.aii/config.yaml` is the Active Inference Institute (InstituteOS) metadata manifest
for this repository (schema `instituteos.platform.aii_sidecar`). It records the
federated relationships, artifact inventory, and provenance for the Institute's
catalog.
