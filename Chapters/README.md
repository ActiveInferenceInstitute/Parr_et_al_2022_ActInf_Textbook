# `Chapters/` — reading group computational notes

Authored study material for the textbook, in contrast to the generated plaintext
in [`../TextbookContent/`](../TextbookContent/). Overview and run instructions
are in [`../docs/chapters.md`](../docs/chapters.md).

| File | What it is |
| --- | --- |
| [`VFE.jl`](VFE.jl) | Pluto.jl notebook: Variational Free Energy Simulator (binary hidden state and observation). Open with `julia -e 'using Pluto; Pluto.run()'`. |
| [`test_vfe.jl`](test_vfe.jl) | Julia regression suite for the simulator's mathematics. Run with `julia Chapters/test_vfe.jl`. |
| [`03_blanket.ipynb`](03_blanket.ipynb) | Jupyter notebook (Python 3, standard library only) with Chapter 3 study notes: Markov blankets, surprise minimisation, and variational free energy. |

Keep `test_vfe.jl` in step with `VFE.jl`. The Pluto notebook is interactive and
is not executed in CI, and it is not converted to a Generalized Notation
Notation document; see [`../docs/chapters.md`](../docs/chapters.md) and
[`../TODO.md`](../TODO.md) J1.
