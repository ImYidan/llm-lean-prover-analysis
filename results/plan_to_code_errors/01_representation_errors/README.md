# Representation Errors

## 1. Definition

A mathematical object is encoded using an unintended formal type, domain, coercion, or data representation. The intended local mathematical step is valid, but its encoding generates the wrong formal obligations. Diagnose the representation from the code and types, rather than treating every missing instance as this mechanism.

## 2. Case study

**Model:** Goedel-Prover-V2-32B · **Benchmark:** miniF2F · **Candidate:** `amc12a_2021_p14_g9`.

A finite sum intended to range over natural numbers receives a real-valued index because its interval endpoints are untyped.

**Statement from the final model candidate:**

```lean
theorem amc12a_2021_p14 :
    ((∑ k in Finset.Icc 1 20, Real.logb (5 ^ k) (3 ^ k ^ 2)) *
        ∑ k in Finset.Icc 1 100, Real.logb (9 ^ k) (25 ^ k)) = 21000 := by
```

Read the [complete original model output](model_output.txt), [verbatim excerpts with source lines](case_excerpt.md), and [original verification record and provenance](verification.json).

## 3. Mathematical and Lean explanation

The intended calculation is mathematically sound. For positive integer $k$,

$$\log_{5^k}(3^{k^2})=k\frac{\log3}{\log5},\qquad \log_{9^k}(25^k)=\frac{\log5}{\log3}.$$

Both cancellations are valid: $k>0$ and $\log3,\log5>0$. Hence the two sums equal $210\log3/\log5$ and $100\log5/\log3$, and their product is $21000$.

In the raw `calc` expression, the newly introduced right-hand sum uses `Finset.Icc 1 20` and `(k : ℝ)` without a natural-number constraint on the index. A type ascription is not automatically a cast from a previously fixed natural-number type. Here Lean infers a real interval and requests `LocallyFiniteOrder ℝ`. Under the usual order on the reals, a nontrivial interval contains infinitely many points; it cannot be enumerated as the intended finite interval.

The representation should specify a natural-number index and then coerce its value into the real summand. A minimized example is:

```lean
example : (∑ k in Finset.Icc (1 : ℕ) 20, (k : ℝ)) = 210 := by
  norm_num [Finset.sum_Icc_succ_top]
```

The local checks in `verification.json` compare the untyped sum with this explicit natural-index version. They isolate the representation obligation; the original response has eleven saved errors and this does not certify a complete repair.

The compiler symptom is [Missing instance](../../compiler_diagnostics/04_missing_instance/README.md). The translation mechanism is Representation Errors. These are two descriptions of the same local event at different analytical levels, so they should not be combined into one exclusive category list.
