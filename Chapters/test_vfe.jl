#! /usr/bin/env julia
# Regression test for the Variational Free Energy Simulator (Chapters/VFE.jl).
#
# Re-implements the notebook's binary-state model deterministically (no Pluto, no
# @bind) and asserts the mathematical properties the simulator is supposed to show:
#   1. the exact posterior P(x|y) is normalized;
#   2. the variational free energy F(q) is minimized at q = P(x=1|y);
#   3. inference lowers the free energy below its value at the prior;
#   4. F is finite across the interior q ∈ (0,1) (no log-of-negative / NaN).
#
# Run:  julia Chapters/test_vfe.jl

using Test

# Full generative + inference model, matching Chapters/VFE.jl exactly.
function model(s, l)
    prior = [s, 1 - s]                                   # P(x)
    likelihood = [l 1 - l; 1 - l l]                      # P(y | x), rows = x, cols = y
    observation = [1, 0]                                 # observed y = 1 (one-hot)
    likelihood_of_observation = likelihood * observation # P(y = 1 | x)
    joint = prior .* vec(likelihood_of_observation)      # P(x, y)
    z = sum(joint)                                       # P(y)
    posterior = joint / z                                # P(x | y)
    return posterior, z
end

# x * log(x / y) with the 0 * log(0) = 0 convention.
xlogy(x, y) = x <= 0 ? zero(x) : x * log(x / y)

# Variational free energy at variational-posterior mass q = Q(x = 1):
#   F(q) = KL[Q(x) || P(x|y)] - log P(y).
function vfe(q, posterior, z)
    xlogy(q, posterior[1]) + xlogy(1 - q, posterior[2]) - log(z)
end

# Coarse grid argmin of F over the interior of q.
function argmin_vfe(posterior, z; step = 1e-3)
    qs = step:step:(1 - step)
    return qs[argmin([vfe(q, posterior, z) for q in qs])]
end

@testset "Variational Free Energy Simulator" begin
    # Sweep across the (prior, likelihood) slider ranges, avoiding the degenerate
    # s,l ∈ {0,1} boundary where the exact posterior mass can be exactly 0.
    for s in (0.05, 0.3, 0.5, 0.8, 0.95), l in (0.1, 0.35, 0.65, 0.9)
        posterior, z = model(s, l)

        @test isapprox(sum(posterior), 1.0; atol = 1e-12)      # normalized posterior

        qstar = argmin_vfe(posterior, z)
        @test isapprox(qstar, posterior[1]; atol = 5e-3)       # argmin == exact posterior

        # inference strictly lowers the free energy
        @test vfe(posterior[1], posterior, z) < vfe(s, posterior, z)

        # finite on the interior — no log-of-negative / NaN
        @test all(isfinite(vfe(q, posterior, z)) for q in 0.01:0.01:0.99)
    end
end
