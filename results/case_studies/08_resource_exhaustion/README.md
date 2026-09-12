# Resource exhaustion

## 1. Definition

Checking reports that a configured recursion-depth, heartbeat, time or memory limit has been reached. The report establishes that verification encountered a resource limit under that configuration. It neither certifies the proof as correct nor establishes that a larger budget would make it pass; other errors may coexist.

## 2. Case study

**Model:** Goedel-Prover-V2-32B · **Benchmark:** miniF2F · **Candidate:** `mathd_numbertheory_451_g10`. This is the case used for this category in thesis Table 6.1.

The theorem concerns integers in 2010–2019 that are sums of the four divisors of some natural number. In one branch the candidate derives m ≤ 2010, enumerates m with `interval_cases`, unfolds `Nat.divisors` and applies numerical tactics across the resulting branches.

**Statement from the final model candidate:**

```lean
theorem mathd_numbertheory_451 (S : Finset ℕ)
    (h₀ :
      ∀ n : ℕ,
        n ∈ S ↔
          2010 ≤ n ∧ n ≤ 2019 ∧ ∃ m, (Nat.divisors m).card = 4 ∧ (∑ p in Nat.divisors m, p) = n) :
    (∑ k in S, k) = 2016 := by
```

**Compiler evidence:** `maximum recursion depth has been reached` at submitted-code position `126:33`. The saved verification record contains 2 errors.

Read the [verbatim code excerpt and full diagnostic](case_excerpt.md), the [complete original model output](model_output.txt), or the [verification record and source fingerprints](verification.json).

## 3. Explanation

The code exposes a broad finite search followed by repeated divisor evaluation. With only the bound m ≤ 2010 on a natural number, the range can contain 2011 values. The stored compiler complaint is `maximum recursion depth has been reached`; its reported position is on the following `(try contradiction)` within the same tactic chain, rather than directly on the `interval_cases` token.

This supports identifying the surrounding enumeration/evaluation strategy as the relevant context for the resource failure. The saved log is not a profiler, so it does not isolate which internal recursive operation consumed the depth budget. The record also contains an `unsolved goals` message elsewhere in the proof.

The resource category must therefore be interpreted together with the code and verification configuration. Neither the mathematical correctness of the whole candidate nor success after increasing `maxRecDepth` was established by this record, and no changed-budget rerun is claimed here.
