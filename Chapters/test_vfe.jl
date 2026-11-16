#! /usr/bin/env julia
# Regression test for the Variational Free Energy Simulator (Chapters/VFE.jl).
#
# Imports the same pure computation used by Pluto, without loading the notebook,
# Plots, or its embedded environment. Covers interior and boundary supports,
# including impossible observations with no exact posterior.
#
# Run:  julia Chapters/test_vfe.jl

using Test

include(joinpath(@__DIR__, "vfe_model.jl"))
using .VFEModel

# Coarse grid argmin of F over the interior of q.
function argmin_vfe(joint; step = 1e-3)
    qs = step:step:(1 - step)
    return qs[argmin([vfe(q, joint) for q in qs])]
end

@testset "Variational Free Energy Simulator" begin
    for s in (0.05, 0.3, 0.5, 0.8, 0.95), l in (0.1, 0.35, 0.65, 0.9)
        inferred = infer_observation([s 1-s], [l 1-l; 1-l l])
        posterior = inferred.posterior
        joint = inferred.joint_probability
        z = inferred.marginal_probability
        expected_joint = [s * l, (1 - s) * (1 - l)]

        @test joint ≈ expected_joint
        @test z ≈ sum(expected_joint)
        @test isapprox(sum(posterior), 1.0; atol = 1e-12)
        @test posterior ≈ expected_joint / sum(expected_joint)
        @test isapprox(argmin_vfe(joint), posterior[1]; atol = 5e-3)
        @test isapprox(vfe(posterior[1], joint), -log(z); atol = 1e-12)
        @test vfe(posterior[1], joint) < vfe(s, joint)
        @test all(isfinite(vfe(q, joint)) for q in 0.01:0.01:0.99)
    end

    @testset "Boundary support and impossible observations" begin
        @test xlogy(0.0, 0.0) == 0.0
        @test xlogy(0.0, 0.5) == 0.0
        @test xlogy(0.5, 0.0) == Inf
        for s in (0.0, 0.5, 1.0), l in (0.0, 0.5, 1.0)
            inferred = infer_observation([s 1-s], [l 1-l; 1-l l])
            joint = inferred.joint_probability
            z = inferred.marginal_probability
            if (s, l) in ((0.0, 1.0), (1.0, 0.0))
                @test inferred.posterior === nothing
                @test z == 0.0
                @test joint == [0.0, 0.0]
                @test all(vfe(q, joint) == Inf for q in (0.0, 0.25, 0.5, 0.75, 1.0))
            else
                posterior = inferred.posterior
                @test isapprox(sum(posterior), 1.0; atol = 1e-12)
                @test all(posterior .>= 0.0)
                @test isapprox(vfe(posterior[1], joint), -log(z); atol = 1e-12)
                for (q, mass) in ((1.0, joint[1]), (0.0, joint[2]))
                    if iszero(mass)
                        @test vfe(q, joint) == Inf
                    else
                        @test vfe(q, joint) ≈ -log(mass)
                    end
                end
            end
        end
    end
end
