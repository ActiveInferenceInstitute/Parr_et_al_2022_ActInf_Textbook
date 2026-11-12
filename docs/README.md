# Parr et al. 2022 — documentation

Index of the documentation for the Active Inference Institute Textbook Group's
materials for the open-access textbook:

> Parr, T., Pezzulo, G., & Friston, K. J. (2022). *Active Inference: The Free
> Energy Principle in Mind, Brain, and Behavior*. MIT Press.
> ISBN 978-0-262-36997-8 · open-access edition
> [doi:10.7551/mitpress/12441.001.0001](https://doi.org/10.7551/mitpress/12441.001.0001).

Start with [`documentation-index.md`](documentation-index.md) — the flat index of
every long-lived document, kept current by the `docs` gate.

| Document | Use it for |
| --- | --- |
| [Documentation index](documentation-index.md) | Every long-lived document, in one list. |
| [Validation](validation.md) | The `./run.sh` arms, what each proves, and the CI jobs that call them. |
| [Gate measurements](_generated/GATES.md) | Generated: per-arm wall time and gate facts (`./run.sh report`). |
| [Plaintext content](plaintext-content.md) | How `TextbookContent/PlainText/` is laid out, how it is generated, and its integrity invariant. |
| [Chapters](chapters.md) | The reading group's computational notes: `VFE.jl`, `test_vfe.jl`, and `03_blanket.ipynb`. |

## Running the gates

```bash
./run.sh --list   # every arm and its exact command
./run.sh fast     # lint + tests + plaintext + docs
./run.sh full     # every arm
```

## Status

Working materials, not a published product:

- The **plaintext extractions** and the **VFE simulator** regenerate from the
  PDF of record and run offline today; every offline arm passes (see
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
