# Proof-Step Assembly Errors

## 1. Definition

The intended local mathematical identity and library fact are appropriate, but the proof steps are not arranged to match the current goal or hypotheses. Missing reassociation, orientation, normalization, or an intermediate bridge can prevent a tactic from applying. Establish the local mathematical step before interpreting the tactic failure.

## 2. Case study

**Model:** Goedel-Prover-V2-32B · **Benchmark:** miniF2F · **Candidate:** `algebra_sum1onsqrt2to1onsqrt10000lt198_g27`.

A square-root identity is applied before reassociating a product, so the rewrite pattern is absent from the goal.

**Statement from the final model candidate:**

```lean
theorem algebra_sum1onsqrt2to1onsqrt10000lt198 :
    (∑ k in Finset.Icc (2 : ℕ) 10000, 1 / Real.sqrt k) < 198 := by
```

Read the [complete original model output](model_output.txt), [verbatim excerpts with source lines](case_excerpt.md), and [original verification record and provenance](verification.json).

## 3. Mathematical and Lean explanation

The goal is $\sum_{k=2}^{10000}1/\sqrt{k}<198$. For $k\ge2$, both square roots below are positive and $\sqrt{k-1}<\sqrt{k}$. Rationalizing gives

$$2(\sqrt{k}-\sqrt{k-1})=\frac{2}{\sqrt{k}+\sqrt{k-1}}>\frac1{\sqrt{k}}.$$

Summing these strict inequalities over the nonempty interval telescopes:

$$\sum_{k=2}^{10000}\frac1{\sqrt{k}}<2(\sqrt{10000}-\sqrt1)=198.$$

This independently establishes the selected plan's mathematical route. Within its formalization, the model needs $2k=2\sqrt{k}\sqrt{k}$, which follows from $\sqrt{k}\sqrt{k}=k$ for $k\ge0$.

The chosen library fact, `Real.mul_self_sqrt`, expresses exactly the latter identity. But Lean parses `2 * Real.sqrt k * Real.sqrt k` as `(2 * Real.sqrt k) * Real.sqrt k`. Its syntax tree does not contain the subexpression `Real.sqrt k * Real.sqrt k`. The saved `rw` therefore reports that it cannot find the rewrite pattern. Availability of the fact is not the problem; the product needs reassociation first.

The corrected minimized step is:

```lean
example (k : ℕ) : (2 : ℝ) * k = 2 * Real.sqrt k * Real.sqrt k := by
  rw [mul_assoc, Real.mul_self_sqrt (Nat.cast_nonneg k)]
```

The first rewrite exposes `2 * (Real.sqrt k * Real.sqrt k)`; the second reduces the inner product to `k`. The nonnegativity argument is supplied explicitly. The before/after local checks are preserved in `verification.json`.

The compiler symptom is Tactic failure and the mechanism is Proof-Step Assembly Errors. Earlier exploratory prose includes a false equality at $k=1$, outside the selected plan's $k\ge2$ range. The original verifier also reports a later `omega` failure. Neither is removed from the evidence; successful verification of this isolated rewrite does not establish correctness of the complete response.
