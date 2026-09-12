# Unsolved goals

## 1. Definition

A proof or local tactic block finishes with one or more goals still open. This includes omitted branches, partial tactic progress and intermediate claims that the current argument cannot prove. It is a report of an outstanding obligation; it does not say whether that obligation is true, or whether an earlier tactic in the block also failed.

## 2. Case study

**Model:** Goedel-Prover-V2-32B · **Benchmark:** miniF2F · **Candidate:** `amc12a_2003_p23_g8`. This is the case used for this category in thesis Table 6.1.

The theorem counts square divisors of the product of 1! through 9!. The candidate introduces a claim that k² divides the constant 146313216000 and tries to obtain it from divisibility of the factorial product.

**Statement from the final model candidate:**

```lean
theorem amc12a_2003_p23 (S : Finset ℕ)
    (h₀ : ∀ k : ℕ, k ∈ S ↔ 0 < k ∧ (k * k : ℕ) ∣ ∏ i in Finset.Icc 1 9, i !) : S.card = 672 := by
```

**Compiler evidence:** `unsolved goals` at submitted-code position `18:51`. The saved verification record contains 5 errors.

Read the [verbatim code excerpt and full diagnostic](case_excerpt.md), the [complete original model output](model_output.txt), or the [verification record and source fingerprints](verification.json).

## 3. Explanation

The saved goal context shows the actual product as 1834933472251084800000, while the target still uses 146313216000. For k = 25, k² = 625 divides the actual product but does not divide the candidate's constant. Thus the proposed divisibility implication is false, independently of how much automation is used.

The raw block contains more than the paper's short `norm_num` illustration: it runs `norm_num [...] at h₅₁ ⊢` and then `<;> simpa [...] using h₅₁`. The verifier also records a type mismatch from that follow-up. The selected `unsolved goals` diagnostic belongs to the enclosing claim. Keeping the full block and all verifier errors avoids presenting this candidate as a clean example in which every preceding tactic completed successfully.

The open-goal message alone does not reveal the false constant; that conclusion requires reading the payload and checking the arithmetic. In other candidates an open goal may simply be an unfinished, valid obligation. This case does not claim that replacing the constant alone repairs the complete proof.
