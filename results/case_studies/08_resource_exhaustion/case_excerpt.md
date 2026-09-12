# Resource exhaustion: case excerpt

Source: [mathd_numbertheory_451_g10 — complete model output](model_output.txt). Line ranges below are one-based and refer to that unmodified text file. Compiler positions refer to the submitted code in [verification.json](verification.json), not to model-output lines.

## Relation to the thesis case

The paper abbreviates the bound proof and tactic chain. The excerpt retains the complete local bound derivation and the following tactics, including the expression at the reported error position.

The code quotations below are verbatim selections from the final candidate in the saved model response. No variable renaming, symbol substitution or internal ellipsis has been applied. Separate blocks mark separate source ranges; intervening material remains available in the full response.

## Statement — model-output lines 583–588

```lean
theorem mathd_numbertheory_451 (S : Finset ℕ)
    (h₀ :
      ∀ n : ℕ,
        n ∈ S ↔
          2010 ≤ n ∧ n ≤ 2019 ∧ ∃ m, (Nat.divisors m).card = 4 ∧ (∑ p in Nat.divisors m, p) = n) :
    (∑ k in S, k) = 2016 := by
```

## Code — model-output lines 695–705

```lean
                          have h₂₄ : m ≤ 2010 := by
                            have h₂₅ : (∑ p in Nat.divisors m, p) = 2010 := by simp_all
                            have h₂₆ : m ∈ Nat.divisors m := by
                              apply Nat.mem_divisors.mpr
                              exact ⟨Nat.dvd_refl m, by omega⟩
                            have h₂₇ : m ≤ ∑ p in Nat.divisors m, p := by
                              apply Finset.single_le_sum (fun x _ => Nat.zero_le x) h₂₆
                            linarith
                          interval_cases m <;> norm_num [Nat.divisors] at h₂₂ h₂₃ ⊢ <;>
                            (try contradiction) <;>
                            (try omega)
```

## Complete selected diagnostic

Saved error index `0` (zero-based); position `126:33` in the submitted code. The entire saved `data` field follows.

```text
maximum recursion depth has been reached
use `set_option maxRecDepth <num>` to increase limit
use `set_option diagnostics true` to get diagnostic information
```

The sibling `verification.json` retains the complete selected candidate verification record, including all other errors, their original order and positions.
