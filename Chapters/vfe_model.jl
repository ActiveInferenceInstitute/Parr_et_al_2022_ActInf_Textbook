module VFEModel

export infer_observation, xlogy, vfe

"""Infer the notebook's observed y = 1 without inventing mass for impossible data."""
function infer_observation(prior, likelihood)
    observation = [1, 0]
    likelihood_of_observation = likelihood * observation
    joint_probability = vec(prior) .* vec(likelihood_of_observation)
    marginal_probability = sum(joint_probability)
    posterior = iszero(marginal_probability) ? nothing : joint_probability / marginal_probability
    return (; joint_probability, marginal_probability, posterior)
end

"""Return x * log(x / y), with a zero-mass term equal to zero even when y is zero."""
xlogy(x, y) = iszero(x) ? zero(x) : x * log(x / y)

"""Binary variational free energy sum_x Q(x) log(Q(x) / P(x, y)).

For positive evidence this equals KL[Q || P(x | y)] - log P(y). A positive
variational mass outside joint support gives Inf; zero evidence therefore gives
Inf for every q, while the exact posterior remains undefined (nothing).
"""
function vfe(q, joint_probability)
    0 <= q <= 1 || throw(DomainError(q, "q must be a probability"))
    return xlogy(q, joint_probability[1]) + xlogy(1 - q, joint_probability[2])
end

end
