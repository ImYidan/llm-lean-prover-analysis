# Syntax error: case excerpt

Source: [mathd_algebra_125_g30 — complete model output](model_output.txt). Line ranges below are one-based and refer to that unmodified text file. Compiler positions refer to the submitted code in [verification.json](verification.json), not to model-output lines.

## Relation to the thesis case

Table 6.1 abbreviates the inner declaration and rewrites Unicode types/subscripts for typesetting. The excerpt below retains the original spelling and its preceding, correctly nested cast.

The code quotations below are verbatim selections from the final candidate in the saved model response. No variable renaming, symbol substitution or internal ellipsis has been applied. Separate blocks mark separate source ranges; intervening material remains available in the full response.

## Statement — model-output lines 98–99

```lean
theorem mathd_algebra_125 (x y : ℕ) (h₀ : 0 < x ∧ 0 < y) (h₁ : 5 * x = y)
    (h₂ : ↑x - (3 : ℤ) + (y - (3 : ℤ)) = 30) : x = 6 := by
```

## Code — model-output lines 100–103

```lean
  have h₃ : (x : ℤ) - 3 + ((5 * x : ℕ) : ℤ) - 3 = 30 := by
    have h₃₁ : (y : ℤ) = (5 * x : ℕ : ℤ) := by
      norm_cast
      <;> simp [h₁]
```

## Complete selected diagnostic

Saved error index `0` (zero-based); position `8:35` in the submitted code. The entire saved `data` field follows.

```text
unexpected token ':'; expected ')'
```

The sibling `verification.json` retains the complete selected candidate verification record, including all other errors, their original order and positions.
