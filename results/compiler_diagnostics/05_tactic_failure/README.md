# Tactic failure

## 1. Definition

A recognized tactic reports that it cannot perform the requested operation in the current proof state. Examples include failed automation, a rewrite with no matching occurrence, incompatible goal or case structure, and a tactic called after goals have closed. A tactic complaint is local; it does not certify that the entire surrounding submission has already passed parsing, elaboration and type checking.

## 2. Case study

**Model:** Goedel-Prover-V2-32B · **Benchmark:** miniF2F · **Candidate:** `induction_pord1p1on2powklt5on2_g27`. This is the case used for this category in thesis Table 6.1.

The candidate tries to prove a finite-product bound by induction. Writing P for the product through n, it uses the induction hypothesis P < 5/2, establishes P ≥ 0 and then asks `nlinarith` to prove the stronger local claim 3P/2 < 5/2.

**Statement from the final model candidate:**

```lean
theorem induction_pord1p1on2powklt5on2 (n : ℕ) (h₀ : 0 < n) :
    ∏ k in Finset.Icc 1 n, (1 + (1 : ℝ) / 2 ^ k) < 5 / 2 := by
```

**Compiler evidence:** `linarith failed to find a contradiction` at submitted-code position `47:14`. The saved verification record contains 1 errors.

Read the [verbatim code excerpt and full diagnostic](case_excerpt.md), the [complete original model output](model_output.txt), or the [verification record and source fingerprints](verification.json).

## 3. Explanation

The full diagnostic contains the induction bound, nonnegativity and the negated target `P * (3 / 2) ≥ 5 / 2`, with goal `False`. Those numerical constraints are consistent. For example, P = 15/8 gives P < 5/2 and P ≥ 0, but 3P/2 = 45/16 > 5/2. In fact P = 15/8 is the product through n = 2, so the deliberately weakened intermediate bound fails at a genuine product value.

The intended next product uses its actual extra factor; replacing that factor by the coarse bound 3/2 loses too much information. A proof may need a stronger invariant or a sharper estimate. The compiler output identifies the failed tactic, while the arithmetic counterexample explains why this local contradiction attempt cannot establish the displayed claim.

The source invocation is `nlinarith`, even though its diagnostic begins `linarith failed to find a contradiction`. This candidate has one saved error. That observation does not turn the diagnostic into a general measure of tactic quality or establish a successful replacement proof.
