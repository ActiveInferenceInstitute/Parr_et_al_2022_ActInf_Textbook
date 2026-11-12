# GNN conformance

`gnn conformance (pinned)` is the `gnn-conformance` job in
[`workflows/ci.yml`](workflows/ci.yml). It runs one command, `./run.sh gnn`,
which is [`../scripts/check_gnn_conformance.py`](../scripts/check_gnn_conformance.py).

The arm reads [`gnn-pin.json`](gnn-pin.json), which pins
`ActiveInferenceInstitute/Generalized_Notation_Notation` at `v5.0.3`
(`8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1`) under schema
`gnn-importer-pin/v1`. The pin file is the only place those values appear: the
workflow and the script hold no copy of the tag or revision, so bumping the pin
is a one-file change.

What the arm parses:

1. every `*.gnn.md` sketch in the repository — each must parse and pass the
   syntax validator, and the parser's type checker must accept the set;
2. when the repository declares no sketch yet (as now), the pinned upstream
   `input/gnn_files/basics/static_perception.md` exemplar at the pin's revision.

It also verifies that the installed parser's version equals the pin's tag. The
type checker returns `True` when every file validates, `2` when files are
invalid or none were found, and `False` on a hard failure; only `True` passes.
The printed receipt names what was checked: `scope` `repository sketches` with
`result` `repository-content-passed`, or `scope` `pinned GNN exemplar baseline`
with `result` `pinned-exemplar-baseline-passed`. The result is a pipeline and pin conformance baseline, not a claim that this
repository already contains a model. The arm needs network access and a CPython
that satisfies the pinned package's `requires-python` (`>=3.11,<3.15`, read from
the pinned revision); see [`../docs/validation.md`](../docs/validation.md).

The script's unit tests are the `tests` arm, `./run.sh tests`. They replace the
parser with fixed-result modules, so they need neither network nor the pinned
install, and they assert that a type-checker result other than `True` exits 1 and
that the receipt labels its source.
