# `Chapters/` — reading group computational notes

Authored study material for the textbook, in contrast to the generated plaintext
in [`../TextbookContent/`](../TextbookContent/). Overview and run instructions
are in [`../docs/chapters.md`](../docs/chapters.md).

| File | What it is |
| --- | --- |
| [`VFE.jl`](VFE.jl) | Pluto.jl notebook: Variational Free Energy Simulator (binary hidden state and observation). Open with `julia -e 'using Pluto; Pluto.run()'`. |
| [`vfe_model.jl`](vfe_model.jl) | Shared `VFEModel` used by the notebook and tests, including impossible-observation handling. |
| [`test_vfe.jl`](test_vfe.jl) | Julia regression suite for the simulator's mathematics. Run with `julia Chapters/test_vfe.jl`. |
| [`03_blanket.ipynb`](03_blanket.ipynb) | Jupyter notebook (Python 3, standard library only) with Chapter 3 study notes: Markov blankets, surprise minimisation, and variational free energy. |

Keep both callers on the shared model. Impossible observations have no posterior
and infinite free energy, not an epsilon-smoothed plot. The headless model passed
bounded qualification, but Pluto is unavailable in the prepared runtime and the
interactive surface remains unaccepted. The notebook is not executed in CI or
converted to GNN; see [chapters](../docs/chapters.md) and [TODO](../TODO.md).
