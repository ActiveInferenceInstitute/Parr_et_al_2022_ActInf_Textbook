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

- `Chapters/` holds `VFE.jl`, the shared `vfe_model.jl`, its Julia regression suite,
  and the standard-library Jupyter notes. Headless tests do not accept Pluto's UI.
- `scripts/` holds the cleaner, Markdown/GNN checks and explicit-root education
  adapter with focused regressions. Use `./run.sh --list` for the exact registry.
- `.aii/config.yaml` is the InstituteOS sidecar; `.github/workflows/ci.yml` calls the `./run.sh` arms — `lint`, `tests`, `docs`, `plaintext`, `vfe` and the pinned `gnn` conformance check (see `.github/GNN.md`) — on pushes to `main` and pull requests targeting `main`.

## Verification

Run the gates relevant to your change through the single entry point:

```bash
./run.sh --list   # every arm and its exact command
./run.sh fast     # lint + tests + plaintext + docs
COURSES_ROOT=/absolute/path/to/qualified/courses ./run.sh full
```

`education` is a separately runnable real producer/member arm and is not in
hermetic `fast`. Select an already qualified courses checkout; never substitute
an installed validator or infer a sibling layout. CI does not yet supply that
qualified producer. GitVault commands require governed test admission.

`docs/validation.md` is the arm reference, and CI calls these same arms. Never
hand-edit a number that `./run.sh report` writes into
`docs/_generated/GATES.md`.

The notebook's three code cells are executed by hand; its assertions should pass. Do not convert `VFE.jl` to a GNN document or execute the Pluto notebook in CI; both decisions are recorded in `REVIEW_LOG_2026-11-01.md`.

## Rules

- Keep changes grounded in the source book and in behavior verifiable from the repository.
- Do not add private material, credentials, or unrelated files.
- Update `README.md` or `CONTRIBUTING.md` when commands, paths, or outputs change.
- This repository deliberately has no documentation site; see `TODO.md` J1.
