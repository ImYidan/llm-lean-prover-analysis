# Unresolved name: case excerpt

Source: [amc12a_2021_p12_g29 — complete model output](model_output.txt). Line ranges below are one-based and refer to that unmodified text file. Compiler positions refer to the submitted code in [verification.json](verification.json), not to model-output lines.

## Relation to the thesis case

Table 6.1 shortens the polynomial expression with an ellipsis and changes the displayed notation. This file gives the complete original existential claim and the actual invocation.

The code quotations below are verbatim selections from the final candidate in the saved model response. No variable renaming, symbol substitution or internal ellipsis has been applied. Separate blocks mark separate source ranges; intervening material remains available in the full response.

## Statement — model-output lines 1076–1078

```lean
theorem amc12a_2021_p12 (a b c d : ℝ) (f : ℂ → ℂ)
    (h₀ : ∀ z, f z = z ^ 6 - 10 * z ^ 5 + a * z ^ 4 + b * z ^ 3 + c * z ^ 2 + d * z + 16)
    (h₁ : ∀ z, f z = 0 → z.im = 0 ∧ 0 < z.re ∧ ↑(Int.floor z.re) = z.re) : b = -88 := by
```

## Code — model-output lines 1084–1087

```lean
        have h₅ : ∃ (z : ℂ), z ^ 6 - 10 * z ^ 5 + a * z ^ 4 + b * z ^ 3 + c * z ^ 2 + d * z + 16 = 0 := by
          -- Use the fact that ℂ is algebraically closed to find a root of the polynomial
          apply exists_root
          intro h
```

## Complete selected diagnostic

Saved error index `0` (zero-based); position `15:16` in the submitted code. The entire saved `data` field follows.

```text
unknown identifier 'exists_root'
```

The sibling `verification.json` retains the complete selected candidate verification record, including all other errors, their original order and positions.
