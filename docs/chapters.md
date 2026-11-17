# Chapters — computational notes

`Chapters/` holds the reading group's computational notes for the textbook. They
are authored (unlike the generated plaintext) and are meant to be opened and run
interactively.

## Contents

| File | What it is | How to run |
| --- | --- | --- |
| [`VFE.jl`](../Chapters/VFE.jl) | [Pluto.jl](https://plutojl.org) notebook: a Variational Free Energy Simulator over one binary hidden state and one binary observation, with sliders for the prior and likelihood. Dependencies are pinned in the notebook's embedded manifest (Julia 1.7.3). | `julia -e 'using Pluto; Pluto.run()'`, then load `Chapters/VFE.jl`. |
| [`vfe_model.jl`](../Chapters/vfe_model.jl) | Shared `VFEModel`: `infer_observation`, `xlogy` and `vfe`, used by notebook and regression suite. | Loaded by both callers; no independent formula copy. |
| [`test_vfe.jl`](../Chapters/test_vfe.jl) | Dependency-free Julia regression suite for the simulator's mathematics: the exact posterior is normalized, the variational free energy is minimised at the exact posterior, inference lowers free energy below the prior, and F is finite on the interior. | `julia Chapters/test_vfe.jl` |
| [`03_blanket.ipynb`](../Chapters/03_blanket.ipynb) | Standard Jupyter notebook (Python 3 kernel, standard library only) with study notes for Chapter 3, *The High Road to Active Inference*: Markov blankets in a Bayesian network, surprise minimisation, and the variational free energy. | `jupyter notebook Chapters/03_blanket.ipynb` |

## The model the simulator demonstrates

`VFE.jl` implements static perception: one binary hidden state, one binary
observation, a likelihood, and a posterior over the hidden state. The notebook
defines `F[Q, y] = D_KL[Q(x) || P(x|y)] - ln P(y)`. Both callers use
`vfe_model.jl`. Supported observations retain normalized posteriors and valid
boundary behavior. Impossible observations `(s,l)=(0,1)` and `(1,0)` have no
posterior and infinite free energy; the notebook does not plot a fabricated
posterior or smooth the case with epsilon. Run the headless model with `./run.sh vfe`.

The bounded Julia suite passed, but Pluto is absent from the prepared runtime.
Actual notebook rendering and slider behavior remain unaccepted; headless
mathematics is not visual evidence. Generated measurements remain historical.

## Notes for contributors

- Change the shared `vfe_model.jl` contract and its real boundary tests together;
  do not reintroduce a separate formula copy in either caller.
- The Pluto notebook is interactive and is deliberately not executed in CI, and
  it is deliberately not converted to a Generalized Notation Notation (GNN)
  document — see [`../REVIEW_LOG_2026-11-01.md`](../REVIEW_LOG_2026-11-01.md)
  and [`../TODO.md`](../TODO.md) J1. Do not make either change without a request
  that asks for exactly that.
- The notebook's three code cells are executed by hand; their assertions should
  pass.
