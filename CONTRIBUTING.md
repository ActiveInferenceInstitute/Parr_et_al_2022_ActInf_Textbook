# Contributing

Thank you for improving the Active Inference Textbook repository.

## Scope

This repository contains the open-access textbook PDF, cleaned plaintext
extractions, study notebooks, and the small reproducibility scripts and tests
that support them. Contributions should stay grounded in the source book and
in behavior that can be verified from the repository.

## Before opening a change

1. Read `README.md` and the relevant source file or notebook.
2. Keep generated plaintext changes reproducible: update or run
   `scripts/clean_plaintext.py` rather than editing extracted chapters by hand.
3. Do not add private material, credentials, or unrelated files.
4. For documentation or metadata changes, check relative links and paths.

## Verification

Run the checks relevant to your change:

```text
python3 scripts/clean_plaintext.py
julia Chapters/test_vfe.jl
```

The cleaner's default mode reports its integrity checks without writing files.
Use `python3 scripts/clean_plaintext.py --apply` only when regenerating the
cleaned plaintext files. The Julia test exercises the binary variational free
energy model without requiring Pluto.

For `Chapters/03_blanket.ipynb`, execute its three code cells in a Python 3
kernel and confirm that the assertions pass. The notebook uses only Python's
standard library.

## Pull requests

Describe what changed, why it is grounded in the repository, and which checks
were run. Keep commits focused; use a conventional prefix such as `docs:`,
`fix:`, or `test:` where practical.

## Licensing

By contributing, you agree that your contribution is made available under the
repository's CC BY 4.0 license. See `LICENSE` for the license text.
