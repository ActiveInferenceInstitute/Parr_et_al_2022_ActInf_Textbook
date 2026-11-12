# GNN baseline gate

`gnn baseline (pinned)` is defined in `.github/workflows/ci.yml` and reads
`.github/gnn-pin.json`, which pins
`ActiveInferenceInstitute/Generalized_Notation_Notation` at `v5.0.3`
(`8f293d9ba810e6eda5c09842d9c7ed9ffa5f92c1`).

The job verifies the pin and the installed parser, then parses, syntax-checks
and type-checks GNN's own pinned `input/gnn_files/basics/static_perception.md`
exemplar. This repository ships no `*.gnn.md` model, so the job checks no
repository content: it is a pipeline and pin baseline, not a content
conformance check.
