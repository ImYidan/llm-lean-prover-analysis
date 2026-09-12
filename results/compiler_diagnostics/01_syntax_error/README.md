# Syntax error

## 1. Definition

Lean cannot parse the submitted text at the reported position under the active syntax. Typical forms include malformed delimiters, indentation, incomplete constructs and invalid type-ascription syntax. This is a local parsing complaint; other parts of the same submission may also produce diagnostics.

## 2. Case study

**Model:** Goedel-Prover-V2-32B · **Benchmark:** miniF2F · **Candidate:** `mathd_algebra_125_g30`. This is the case used for this category in thesis Table 6.1.

**Scope:** This candidate failed, but 22 of the 32 candidates for this problem succeeded. It is a qualitative illustration from the thesis and is outside the published Pass@32-unsolved-problem statistical scope.

The theorem encodes an age problem over natural numbers and integers. The candidate tries to rewrite the father's age using `5 * x` and then reason in integers. Its inner `have` contains the chained annotation `(5 * x : ℕ : ℤ)`.

**Statement from the final model candidate:**

```lean
theorem mathd_algebra_125 (x y : ℕ) (h₀ : 0 < x ∧ 0 < y) (h₁ : 5 * x = y)
    (h₂ : ↑x - (3 : ℤ) + (y - (3 : ℤ)) = 30) : x = 6 := by
```

**Compiler evidence:** `unexpected token ':'; expected ')'` at submitted-code position `8:35`. The saved verification record contains 3 errors.

Read the [verbatim code excerpt and full diagnostic](case_excerpt.md), the [complete original model output](model_output.txt), or the [verification record and source fingerprints](verification.json).

## 3. Explanation

A type ascription has the form `(e : T)`. The second colon in `(5 * x : ℕ : ℤ)` is not a second permitted annotation inside the same parentheses. The preceding line already contains the nested form `((5 * x : ℕ) : ℤ)`, which makes the intended natural-to-integer conversion visible in the output itself.

The saved verifier record contains three errors: this parser complaint and two `unsolved goals` reports on the enclosing `have` blocks. Their positions and nesting support reading them as connected symptoms of this fragment. They are still separate diagnostics in the all-error inventory.

The local syntax can be expressed with nested parentheses, but this case package does not claim that changing this fragment makes the entire proof pass. The diagnostic establishes a syntactic defect, not whether the mathematical argument is correct.
