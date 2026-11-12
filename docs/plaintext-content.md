# Plaintext textbook content

`TextbookContent/PlainText/` holds machine-readable plaintext extractions of the
open-access textbook, cleaned from the PDF of record. The files are **generated,
not authored** — do not hand-edit them.

## Files

| File | Source |
| --- | --- |
| `1-ActInf22.txt` | Chapter 1 and the front matter |
| `2-ActInf22.txt` … `10-ActInf22.txt` | Chapters 2–10 |
| `Appendix_A-ActInf22.txt` | Appendix A |
| `Appendix_B-ActInf22.txt` | Appendix B |
| `Appendix_C-ActInf22.txt` | Appendix C |
| `Notes-ActInf22.txt` | The book's endnotes |

The table above is the complete list; [`_generated/GATES.md`](_generated/GATES.md)
records the current count and per-arm wall time.

## How they are generated

[`../scripts/clean_plaintext.py`](../scripts/clean_plaintext.py) is the
deterministic cleaner. It removes three classes of PDF-extraction noise —
MIT Press download footers, isolated page-number lines, and very long unwrapped
prose lines — while preserving standalone equation and header lines.

```bash
python3 scripts/clean_plaintext.py           # report only, no writes (default)
python3 scripts/clean_plaintext.py --apply   # rewrite the files in place
```

To regenerate from scratch, re-extract the text from
[`../ActInf_Textbook_2022.pdf`](../ActInf_Textbook_2022.pdf) and run the cleaner
with `--apply`.

## Integrity invariant

The cleaner preserves the total non-whitespace character count exactly, except
for characters belonging to the footer/page-number lines it removes. Its report
prints, for every file, the observed and expected counts and asserts they match;
`./run.sh plaintext` (and the CI job of the same arm) runs the report-only
invocation as a gate (see [validation.md](validation.md)).

## Why there is no `README.md` inside `TextbookContent/`

`TextbookContent/` is build output. The repository convention (see
[`../AGENTS.md`](../AGENTS.md)) is that folder guidance lives in this document
rather than inside the generated tree, and the cleaner globs
`PlainText/*.txt`, so no documentation file belongs there.
