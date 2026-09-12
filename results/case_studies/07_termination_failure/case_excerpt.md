# Termination failure: case excerpt

Source: [FATE-M_006_g23 — complete model output](model_output.txt). Line ranges below are one-based and refer to that unmodified text file. Compiler positions refer to the submitted code in [verification.json](verification.json), not to model-output lines.

## Relation to the thesis case

The paper line-wraps the qualified theorem name and abbreviates the termination report. The raw model response contains earlier draft code as well as its final fenced candidate; this excerpt is from the final code block, and the full response preserves all earlier material.

The code quotations below are verbatim selections from the final candidate in the saved model response. No variable renaming, symbol substitution or internal ellipsis has been applied. Separate blocks mark separate source ranges; intervening material remains available in the full response.

## Statement — model-output lines 147–148

```lean
theorem MonoidHom.eq_id_of_card_gcd_eq_one {G H: Type*} [Finite H] [Finite G][Group G] [Group H]
    (h : (Nat.card H).gcd (Nat.card G) = 1) (f : G →* H) : ∀ p : G , f p = 1 := by
```

## Code — model-output lines 149–156

```lean
  intro p
  have h2 : Nat.Coprime (Nat.card H) (Nat.card G) := by 
    rw [Nat.coprime_iff_gcd_eq_one]
    exact h
  have h3 : ∀ p : G, f p = 1 := by
    apply MonoidHom.eq_id_of_card_gcd_eq_one h2 f
  specialize h3 p
  exact h3
```

## Complete selected diagnostic

Saved error index `0` (zero-based); position `5:8` in the submitted code. The entire saved `data` field follows.

```text
fail to show termination for
  MonoidHom.eq_id_of_card_gcd_eq_one
with errors
failed to infer structural recursion:
Not considering parameter G of MonoidHom.eq_id_of_card_gcd_eq_one:
  it is unchanged in the recursive calls
Not considering parameter H of MonoidHom.eq_id_of_card_gcd_eq_one:
  it is unchanged in the recursive calls
Not considering parameter #3 of MonoidHom.eq_id_of_card_gcd_eq_one:
  it is unchanged in the recursive calls
Not considering parameter #4 of MonoidHom.eq_id_of_card_gcd_eq_one:
  it is unchanged in the recursive calls
Not considering parameter #5 of MonoidHom.eq_id_of_card_gcd_eq_one:
  it is unchanged in the recursive calls
Not considering parameter #6 of MonoidHom.eq_id_of_card_gcd_eq_one:
  it is unchanged in the recursive calls
Not considering parameter h of MonoidHom.eq_id_of_card_gcd_eq_one:
  its type Eq is an inductive family and indices are not variables
    (Nat.card H).gcd (Nat.card G) = 1
Not considering parameter f of MonoidHom.eq_id_of_card_gcd_eq_one:
  it is unchanged in the recursive calls
Not considering parameter p of MonoidHom.eq_id_of_card_gcd_eq_one:
  its type is not an inductive
no parameters suitable for structural recursion

Could not find a decreasing measure.
The basic measures relate at each recursive call as follows:
(<, ≤, =: relation proved, ? all proofs failed, _: no proof attempted)
           
1) 12:10-49
Please use `termination_by` to specify a decreasing measure.
```

The sibling `verification.json` retains the complete selected candidate verification record, including all other errors, their original order and positions.
