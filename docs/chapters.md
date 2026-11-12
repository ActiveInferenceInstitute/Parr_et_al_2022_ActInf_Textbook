# Chapters — computational notes

`Chapters/` holds the reading group's computational notes for the textbook. They
are authored (unlike the generated plaintext) and are meant to be opened and run
interactively.

## Contents

| File | What it is | How to run |
| --- | --- | --- |
| [`VFE.jl`](../Chapters/VFE.jl) | [Pluto.jl](https://plutojl.org) notebook: a Variational Free Energy Simulator over one binary hidden state and one binary observation, with sliders for the prior and likelihood. Dependencies are pinned in the notebook's embedded manifest (Julia 1.7.3). | `julia -e 'using Pluto; Pluto.run()'`, then load `Chapters/VFE.jl`. |
| [`test_vfe.jl`](../Chapters/test_vfe.jl) | Dependency-free Julia regression suite for the simulator's mathematics: the exact posterior is normalized, the variational free energy is minimised at the exact posterior, inference lowers free energy below the prior, and F is finite on the interior. | `julia Chapters/test_vfe.jl` |
| [`03_blanket.ipynb`](../Chapters/03_blanket.ipynb) | Standard Jupyter notebook (Python 3 kernel, standard library only) with study notes for Chapter 3, *The High Road to Active Inference*: Markov blankets in a Bayesian network, surprise minimisation, and the variational free energy. | `jupyter notebook Chapters/03_blanket.ipynb` |

## The model the simulator demonstrates

`VFE.jl` implements static perception: one binary hidden state, one binary
observation, a likelihood, and a posterior over the hidden state. The notebook
defines `F[Q, y] = D_KL[Q(x) || P(x|y)] - ln P(y)`. The Julia regression suite
re-implements that model deterministically — no Pluto, no `@bind` — and asserts
its mathematical properties. The assertion count and the arm's wall time are
measured in [`_generated/GATES.md`](_generated/GATES.md); run it with
`./run.sh vfe`.

## Notes for contributors

- `test_vfe.jl` mirrors `VFE.jl` and must stay in step with it; change both
  together.
- The Pluto notebook is interactive and is deliberately not executed in CI, and
  it is deliberately not converted to a Generalized Notation Notation (GNN)
  document — see [`../REVIEW_LOG_2026-11-01.md`](../REVIEW_LOG_2026-11-01.md)
  and [`../TODO.md`](../TODO.md) J1. Do not make either change without a request
  that asks for exactly that.
- The notebook's three code cells are executed by hand; their assertions should
  pass.
