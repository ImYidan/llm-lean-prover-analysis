# Unresolved name

## 1. Definition

Lean cannot resolve a referenced name to an available local binding or declaration, cannot resolve a field name, or cannot choose uniquely among competing names. The fixed mapping also includes related declaration-name conflicts. A missing namespace qualifier and an unavailable library declaration can produce the same category; the category alone does not distinguish them.

## 2. Case study

**Model:** Goedel-Prover-V2-32B · **Benchmark:** miniF2F · **Candidate:** `amc12a_2021_p12_g29`. This is the case used for this category in thesis Table 6.1.

The statement constrains the roots of a degree-six complex expression and asks for its coefficient `b`. Inside an existential-root claim, the candidate invokes the unqualified name `exists_root`.

**Statement from the final model candidate:**

```lean
theorem amc12a_2021_p12 (a b c d : ℝ) (f : ℂ → ℂ)
    (h₀ : ∀ z, f z = z ^ 6 - 10 * z ^ 5 + a * z ^ 4 + b * z ^ 3 + c * z ^ 2 + d * z + 16)
    (h₁ : ∀ z, f z = 0 → z.im = 0 ∧ 0 < z.re ∧ ↑(Int.floor z.re) = z.re) : b = -88 := by
```

**Compiler evidence:** `unknown identifier 'exists_root'` at submitted-code position `15:16`. The saved verification record contains 4 errors.

Read the [verbatim code excerpt and full diagnostic](case_excerpt.md), the [complete original model output](model_output.txt), or the [verification record and source fingerprints](verification.json).

## 3. Explanation

The raw diagnostic directly establishes that `exists_root` is unresolved at this use site. In the checked Mathlib snapshot (`2f65ba7f1a9144b20c8e7358513548e317d26de1`), `Mathlib/Analysis/Complex/Polynomial.lean:34` declares `Complex.exists_root` inside `namespace Complex`. Its argument is a polynomial with positive degree, and its conclusion is an `IsRoot` proposition. The saved benchmark statement opens `BigOperators Real Nat Topology Rat`, which does not open the `Complex` namespace.

There is also a representation issue. The candidate's target is an equation over a complex expression, while the library result is stated for an object of type `Polynomial ℂ`. Accessing a qualified name would still require constructing the polynomial, establishing its degree condition and connecting polynomial evaluation to the expression.

The first observation is supplied by the compiler; the representation analysis follows from comparing the target and the library signature. No repaired candidate was compiled for this publication. This example does not justify treating every unresolved name as an invented Mathlib lemma: local scope and namespace mistakes belong to the same category.
