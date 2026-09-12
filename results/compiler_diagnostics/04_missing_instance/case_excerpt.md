# Missing instance: case excerpt

Source: [amc12a_2021_p14_g9 — complete model output](model_output.txt). Line ranges below are one-based and refer to that unmodified text file. Compiler positions refer to the submitted code in [verification.json](verification.json), not to model-output lines.

## Relation to the thesis case

The paper shows only the right-hand summation and renders its binder in compact notation. The verbatim excerpt restores the containing equality and the following proof steps.

The code quotations below are verbatim selections from the final candidate in the saved model response. No variable renaming, symbol substitution or internal ellipsis has been applied. Separate blocks mark separate source ranges; intervening material remains available in the full response.

## Statement — model-output lines 129–131

```lean
theorem amc12a_2021_p14 :
    ((∑ k in Finset.Icc 1 20, Real.logb (5 ^ k) (3 ^ k ^ 2)) *
        ∑ k in Finset.Icc 1 100, Real.logb (9 ^ k) (25 ^ k)) = 21000 := by
```

## Code — model-output lines 175–179

```lean
    calc
      (∑ k in Finset.Icc 1 20, Real.logb (5 ^ k) (3 ^ k ^ 2)) = ∑ k in Finset.Icc 1 20, ((k : ℝ) * (Real.log 3 / Real.log 5)) := by
        apply Finset.sum_congr rfl
        intro k hk
        rw [h₁₁ k hk]
```

## Complete selected diagnostic

Saved error index `0` (zero-based); position `52:71` in the submitted code. The entire saved `data` field follows.

```text
failed to synthesize
  LocallyFiniteOrder ℝ
use `set_option diagnostics true` to get diagnostic information
```

The sibling `verification.json` retains the complete selected candidate verification record, including all other errors, their original order and positions.
