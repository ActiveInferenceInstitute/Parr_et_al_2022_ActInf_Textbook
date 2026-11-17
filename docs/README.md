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
| [Chapters](chapters.md) | Computational notes, shared `vfe_model.jl`, regression boundaries and interactive acceptance. |

## Running the gates

```bash
./run.sh --list   # every arm and its exact command
./run.sh fast     # lint + tests + plaintext + docs
COURSES_ROOT=/absolute/path/to/qualified/courses ./run.sh full
```

## Status

Working materials, not a published product:

- Bounded cleaner, Markdown, GNN-protocol and real education-consumer controls
  passed locally, as did the shared Julia model. This is not a fresh full-gate run.
- The plaintext corpus and generated measurements were not regenerated.
- Pluto visual acceptance remains outstanding: the prepared Julia runtime does
  not contain Pluto. No package installation or notebook-in-CI change is implied.
- The repository deliberately has **no documentation site** (see
  [`../TODO.md`](../TODO.md) J1). This `docs/` tree is plain Markdown.

## Related

- [Repository README](../README.md) — inventory, run commands, and provenance.
- [Agent guidance](../AGENTS.md) — ground rules for automated contributors.
- [Contributing](../CONTRIBUTING.md) — scope, licensing, and verification.
- [Citation metadata](../CITATION.cff) — machine-readable citation record.
