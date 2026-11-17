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

```bash
./run.sh --list   # every arm and its exact command
./run.sh fast     # lint + tests + plaintext + docs
COURSES_ROOT=/absolute/path/to/qualified/courses ./run.sh full
```

The education arm needs the actual qualified courses source and is excluded from
hermetic `fast`. CI does not yet deliver that producer; local bounded evidence
is not a green hosted workflow or full-gate result. See [validation](docs/validation.md).

The cleaner's default mode reports its integrity checks without writing files.
Use `python3 scripts/clean_plaintext.py --apply` only when regenerating the
cleaned plaintext files; ambiguous bare page numbers remain content. No corpus
regeneration was part of bounded qualification. The Julia suite uses the same
`vfe_model.jl` as the notebook; Pluto visual acceptance remains separate.

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
