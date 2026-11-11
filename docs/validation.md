# Validation

Two gates cover this repository. Both run offline and need no network.

## Plaintext integrity

```bash
python3 scripts/clean_plaintext.py
```

Report-only (the default) checks the non-whitespace integrity invariant across
all 14 `TextbookContent/PlainText/*.txt` files and prints the observed and
expected counts. `--apply` rewrites the files in place; see
[plaintext-content.md](plaintext-content.md).

## VFE regression

```bash
julia Chapters/test_vfe.jl
```

Asserts the mathematical properties of the Variational Free Energy Simulator.
It re-implements the model from `Chapters/VFE.jl` and needs only Julia's
standard `Test` library. See [chapters.md](chapters.md).

## What CI runs

[`.github/workflows/ci.yml`](../.github/workflows/ci.yml) runs both gates on
pushes to `main` and on pull requests targeting `main`, plus a pinned GNN
conformance baseline. The interactive Pluto notebook is **not** executed in CI.

## Other checks

- The repository has no documentation-site build and no Markdown link gate; the
  documents are plain Markdown.
- `/security-review`-style and packaging checks do not apply: there is no
  installable package, no dependency manifest to lint, and no build step.
