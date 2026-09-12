# Termination failure

## 1. Definition

Lean cannot establish termination of a recursive declaration. It may fail to identify a structurally decreasing argument, infer a well-founded measure or discharge the associated decrease obligation. This diagnostic does not by itself prove that a definition diverges; it records failure to justify termination for the submitted declaration.

## 2. Case study

**Model:** Kimina-Prover-Distill-8B · **Benchmark:** FATE-M · **Candidate:** `FATE-M_006_g23`. This is the case used for this category in thesis Table 6.1.

The theorem says that a homomorphism between finite groups of coprime orders is trivial. While proving `MonoidHom.eq_id_of_card_gcd_eq_one`, the candidate calls `MonoidHom.eq_id_of_card_gcd_eq_one` to obtain exactly the result it is trying to prove.

**Statement from the final model candidate:**

```lean
theorem MonoidHom.eq_id_of_card_gcd_eq_one {G H: Type*} [Finite H] [Finite G][Group G] [Group H]
    (h : (Nat.card H).gcd (Nat.card G) = 1) (f : G →* H) : ∀ p : G , f p = 1 := by
```

**Compiler evidence:** `fail to show termination for` at submitted-code position `5:8`. The saved verification record contains 1 errors.

Read the [verbatim code excerpt and full diagnostic](case_excerpt.md), the [complete original model output](model_output.txt), or the [verification record and source fingerprints](verification.json).

## 3. Explanation

The current theorem name appears in its own proof. The diagnostic treats this as recursive use and lists unchanged parameters, including the groups and the homomorphism. It reports that it cannot infer structural recursion or find a decreasing measure.

In this fragment the attempted call supplies the same mathematical problem again. It does not provide a smaller instance whose result could justify the original one. The need for termination checking comes from that self-reference, rather than from a requirement that the mathematical group-theoretic proof use recursion.

The candidate has one saved error. Removing the self-call would still leave a proof obligation; no replacement proof is supplied or claimed to pass. This case is from Kimina on FATE-M, whereas the other seven cases are from Goedel-32B on miniF2F. The different source is stated explicitly and does not support a comparison of model frequencies.
