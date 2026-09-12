# Proof-Step Assembly Errors: original excerpts

**Candidate:** `algebra_sum1onsqrt2to1onsqrt10000lt198_g27`. All source ranges below are one-based, inclusive lines in [model_output.txt](model_output.txt). Text inside each source block is verbatim; headings and provenance notes are editorial. Hashes cover the original range bytes, including existing line endings.

## Statement from the final candidate (lines 155–156)

```lean
theorem algebra_sum1onsqrt2to1onsqrt10000lt198 :
    (∑ k in Finset.Icc (2 : ℕ) 10000, 1 / Real.sqrt k) < 198 := by
```

## Original model response (lines 126–137)

```text
### Abstract Proof Plan

1. **Prove the Key Inequality**: For every integer `k ≥ 2`, show that `1 / √k < 2(√k - √(k - 1))`.
   - Rewrite the inequality as `2√(k(k-1)) < 2k - 1`.
   - Prove that `k(k-1) < (k - 1/2)²` by expanding and simplifying to `0 < 1/4`.
   - Take square roots and multiply by 2 to get the desired inequality.

2. **Sum the Inequalities**: Sum the inequalities from `k = 2` to `10000`.
   - The RHS telescopes to `2(√10000 - √1) = 198`.
   - Conclude that the sum is strictly less than 198.

### Lean Proof with `have` Statements
```

## Original model response (lines 213–218)

```text
        calc
          1 < 2 * (k : ℝ) - 2 * Real.sqrt k * Real.sqrt (k - 1 : ℝ) := h₁₃
          _ = 2 * Real.sqrt k * Real.sqrt k - 2 * Real.sqrt k * Real.sqrt (k - 1 : ℝ) := by
            rw [Real.mul_self_sqrt (by positivity : 0 ≤ (k : ℝ))]
            <;> ring_nf
          _ = 2 * Real.sqrt k * (Real.sqrt k - Real.sqrt (k - 1 : ℝ)) := by ring
```

## Original verifier diagnostic 0 (not model output)

Position refers to the submitted code in `verification_record.code`. All original errors are retained in [verification.json](verification.json).

```json
{
  "severity": "error",
  "pos": {
    "line": 66,
    "column": 16
  },
  "endPos": {
    "line": 66,
    "column": 64
  },
  "data": "tactic 'rewrite' failed, did not find instance of the pattern in the target expression\n  √↑k * √↑k\nk : ℕ\nhk : 2 ≤ k\nh₁ : ↑k ≥ 2\nh₂ : ↑k - 1 ≥ 1\nh₃ : 0 < √↑k\nh₄ : 0 < √(↑k - 1)\nh₅ : 0 < √↑k * √(↑k - 1)\nh₆ : 2 * √↑k * √(↑k - 1) < 2 * ↑k - 1\nh₈ : 0 < √↑k\nh₉ : 0 < √(↑k - 1)\nh₁₀ : 0 < √↑k * √(↑k - 1)\nh₁₁ : 2 * √↑k * √(↑k - 1) < 2 * ↑k - 1\nh₁₂ h₁₃ : 1 < 2 * ↑k - 2 * √↑k * √(↑k - 1)\n⊢ 2 * ↑k - 2 * √↑k * √(↑k - 1) = 2 * √↑k * √↑k - 2 * √↑k * √(↑k - 1)"
}
```

## Context and selection

The selected plan is for k≥2. The exact calc step and failing rw are retained. Earlier exploratory assertions and the later independent omega failure remain in the full output and verification record.
