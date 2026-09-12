# Type mismatch

## 1. Definition

During elaboration or type checking, Lean cannot make a term satisfy the type or form required by its context. This includes inferred-versus-expected type disagreements, invalid applications, unsuitable coercions and related notation, implicit-argument or universe failures. The fixed operational mapping also places a small set of kernel-evaluation and code-generation diagnostics here; its exact boundaries are defined by the mapping rules.

## 2. Case study

**Model:** Goedel-Prover-V2-32B · **Benchmark:** miniF2F · **Candidate:** `amc12b_2002_p4_g24`. This is the case used for this category in thesis Table 6.1.

The hypothesis uses the rational-construction notation `/.`, but the candidate proves an identity using ordinary division `/`. After rewriting its local goal with that identity, it attempts to close the goal with `exact h₁`.

**Statement from the final model candidate:**

```lean
theorem amc12b_2002_p4 (n : ℕ) (h₀ : 0 < n) (h₁ : (1 /. 2 + 1 /. 3 + 1 /. 7 + 1 /. ↑n).den = 1) : n = 42 := by
```

**Compiler evidence:** `type mismatch` at submitted-code position `21:6`. The saved verification record contains 5 errors.

Read the [verbatim code excerpt and full diagnostic](case_excerpt.md), the [complete original model output](model_output.txt), or the [verification record and source fingerprints](verification.json).

## 3. Explanation

The full payload displays both propositions: `h₁` concerns the denominator of an expression written with `Rat.divInt` (`/.`), while the expected proposition contains ordinary rational division (`/`). At this use site Lean does not accept the types as definitionally equal, so `exact h₁` is rejected.

Mathematical equality is not enough for this application of `exact`; a representation bridge must be made available to the checker. The checked Mathlib snapshot contains `Rat.divInt_eq_div` in `Mathlib/Data/Rat/Defs.lean:522`, which relates the two constructions. Applying such a bridge also requires handling the relevant casts and rewritten expression.

This supports a local representation-mismatch explanation. It does not establish that the candidate's other proof steps are correct: the saved record contains five errors, and no modified proof was reverified here.
