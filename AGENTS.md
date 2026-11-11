# Parr et al. 2022 — agent guidance

The repository is study material for the open-access textbook. Start with [README.md](README.md) for the inventory and run commands, and [CONTRIBUTING.md](CONTRIBUTING.md) for scope, licensing, and verification.

## Generated content

`TextbookContent/PlainText/*.txt` is generated, not authored. The 14 `.txt` files are cleaned extractions of the source PDF; `scripts/clean_plaintext.py` is the deterministic cleaner. Do not hand-edit these files. To regenerate, re-extract from the PDF and run:

```bash
python3 scripts/clean_plaintext.py --apply
```

The default invocation is report-only and checks the non-whitespace integrity invariant. Do not add a README or AGENTS file under `TextbookContent/`; that tree is the build output and the cleaner globs `PlainText/*.txt`. The tree is documented instead in [`docs/plaintext-content.md`](docs/plaintext-content.md).

## Where the documentation lives

- [`docs/README.md`](docs/README.md) is the documentation index; topic files are
  [`docs/plaintext-content.md`](docs/plaintext-content.md),
  [`docs/chapters.md`](docs/chapters.md), and
  [`docs/validation.md`](docs/validation.md).
- [`Chapters/README.md`](Chapters/README.md) is the folder guide for the
  computational notes.
- The root [`README.md`](README.md) holds the inventory, run commands, and
  provenance; [`CONTRIBUTING.md`](CONTRIBUTING.md) holds scope and licensing.
- This repository deliberately has no documentation site; `docs/` is plain
  Markdown (see [`TODO.md`](TODO.md) J1). Keep relative links valid.

## Authored content

- `Chapters/` holds the reading group's computational notes: `VFE.jl` (Pluto.jl), `test_vfe.jl` (Julia regression suite), and `03_blanket.ipynb` (Jupyter, Python standard library). The README documents how to open and run each.
- `scripts/clean_plaintext.py` is the only repository script. `CONTRIBUTING.md` documents its modes.
- `.aii/config.yaml` is the InstituteOS sidecar; `.github/workflows/ci.yml` runs the plaintext integrity check and the VFE regression suite on pushes to `main` and pull requests targeting `main`.

## Verification

Run the gates relevant to your change:

```bash
python3 scripts/clean_plaintext.py
julia Chapters/test_vfe.jl
```

The notebook's three code cells are executed by hand; its assertions should pass. Do not convert `VFE.jl` to a GNN document or execute the Pluto notebook in CI; both decisions are recorded in `REVIEW_LOG_2026-11-01.md`.

## Rules

- Keep changes grounded in the source book and in behavior verifiable from the repository.
- Do not add private material, credentials, or unrelated files.
- Update `README.md` or `CONTRIBUTING.md` when commands, paths, or outputs change.
- This repository deliberately has no documentation site; see `TODO.md` J1.
