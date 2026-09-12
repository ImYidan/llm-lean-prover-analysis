# Type mismatch: case excerpt

Source: [amc12b_2002_p4_g24 — complete model output](model_output.txt). Line ranges below are one-based and refer to that unmodified text file. Compiler positions refer to the submitted code in [verification.json](verification.json), not to model-output lines.

## Relation to the thesis case

The paper presents the final `rw`/`exact` pair and abbreviates the diagnostic with ellipses. The first excerpt below restores the earlier identity that makes the representation change visible; the second is the failing use of `h₁`.

The code quotations below are verbatim selections from the final candidate in the saved model response. No variable renaming, symbol substitution or internal ellipsis has been applied. Separate blocks mark separate source ranges; intervening material remains available in the full response.

## Statement — model-output lines 147–147

```lean
theorem amc12b_2002_p4 (n : ℕ) (h₀ : 0 < n) (h₁ : (1 /. 2 + 1 /. 3 + 1 /. 7 + 1 /. ↑n).den = 1) : n = 42 := by
```

## Code — model-output lines 149–151

```lean
    have h₃ : (1 / (2 : ℚ) + 1 / (3 : ℚ) + 1 / (7 : ℚ) + 1 / (n : ℚ)) = (41 * n + 42 : ℚ) / (42 * n : ℚ) := by
      have h₄ : (n : ℚ) ≠ 0 := by positivity
      field_simp [h₄]
```

## Code — model-output lines 161–163

```lean
    have h₄ : ((41 * n + 42 : ℚ) / (42 * n : ℚ)).den = 1 := by
      rw [← h₃]
      exact h₁
```

## Complete selected diagnostic

Saved error index `0` (zero-based); position `21:6` in the submitted code. The entire saved `data` field follows.

```text
type mismatch
  h₁
has type
  (1 /. 2 + 1 /. 3 + 1 /. 7 + 1 /. ↑n).den = 1 : Prop
but is expected to have type
  (1 / 2 + 1 / 3 + 1 / 7 + 1 / ↑n).den = 1 : Prop
```

The sibling `verification.json` retains the complete selected candidate verification record, including all other errors, their original order and positions.
