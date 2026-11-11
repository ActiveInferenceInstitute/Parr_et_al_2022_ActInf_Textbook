# Parr et al. 2022 — documentation

Index of the documentation for the Active Inference Institute Textbook Group's
materials for the open-access textbook:

> Parr, T., Pezzulo, G., & Friston, K. J. (2022). *Active Inference: The Free
> Energy Principle in Mind, Brain, and Behavior*. MIT Press.
> ISBN 978-0-262-36997-8 · open-access edition
> [doi:10.7551/mitpress/12441.001.0001](https://doi.org/10.7551/mitpress/12441.001.0001).

| Document | Use it for |
| --- | --- |
| [Plaintext content](plaintext-content.md) | How `TextbookContent/PlainText/` is laid out, how it is generated, and its integrity invariant. |
| [Chapters](chapters.md) | The reading group's computational notes: `VFE.jl`, `test_vfe.jl`, and `03_blanket.ipynb`. |
| [Validation](validation.md) | The runnable gates (plaintext integrity and the Julia VFE regression) and what CI runs. |

## Status

Working materials, not a published product:

- The **plaintext extractions** and the **VFE simulator** regenerate from the
  PDF of record and run offline today; both gates pass (see
  [validation.md](validation.md)).
- The **Pluto notebook is interactive** and is not executed in CI; open it with
  a local Julia + Pluto install.
- The repository deliberately has **no documentation site** (see
  [`../TODO.md`](../TODO.md) J1). This `docs/` tree is plain Markdown.

## Related

- [Repository README](../README.md) — inventory, run commands, and provenance.
- [Agent guidance](../AGENTS.md) — ground rules for automated contributors.
- [Contributing](../CONTRIBUTING.md) — scope, licensing, and verification.
- [Citation metadata](../CITATION.cff) — machine-readable citation record.
