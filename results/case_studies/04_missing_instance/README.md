# Missing instance

## 1. Definition

Elaboration requires a type-class instance that synthesis cannot supply. The instance may be unavailable, out of scope or blocked by unresolved type information. An unintended inferred type can also request an instance that should never have been needed. The category describes the failed instance obligation, not a diagnosis that an import is missing.

## 2. Case study

**Model:** Goedel-Prover-V2-32B · **Benchmark:** miniF2F · **Candidate:** `amc12a_2021_p14_g9`. This is the case used for this category in thesis Table 6.1.

The candidate manipulates finite sums involving logarithms. On the right side of a `calc` equality, it writes an untyped `Finset.Icc 1 20` whose bound variable occurs as `(k : ℝ)`.

**Statement from the final model candidate:**

```lean
theorem amc12a_2021_p14 :
    ((∑ k in Finset.Icc 1 20, Real.logb (5 ^ k) (3 ^ k ^ 2)) *
        ∑ k in Finset.Icc 1 100, Real.logb (9 ^ k) (25 ^ k)) = 21000 := by
```

**Compiler evidence:** `failed to synthesize` at submitted-code position `52:71`. The saved verification record contains 11 errors.

Read the [verbatim code excerpt and full diagnostic](case_excerpt.md), the [complete original model output](model_output.txt), or the [verification record and source fingerprints](verification.json).

## 3. Explanation

Here the summation index has not been constrained to natural numbers. The annotation `(k : ℝ)` permits inference of a real-valued index, so constructing this `Finset.Icc` requires `LocallyFiniteOrder ℝ`. The diagnostic reports exactly that missing instance.

Under the usual real-number order, bounded real intervals are not finite, so the requested locally finite order is inappropriate. The explanation is the unintended index type; adding an import would not supply the intended finite natural-number interval. Explicitly giving the interval endpoints natural-number type would distinguish the natural index from its coercion into a real-valued summand.

The same candidate emits further instance and tactic diagnostics. The case illustrates one local synthesis failure and does not imply that all other elaboration obligations succeeded. No full-proof repair is claimed.
