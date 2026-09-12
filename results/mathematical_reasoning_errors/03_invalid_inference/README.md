# Invalid inference

## 1. Definition

A conclusion does not follow from the premises used in a particular reasoning step, even when those premises are valid. An independent witness must show the failure of the displayed implication. This differs from locating a false standalone identity.

## 2. Case study

**Model:** Goedel-Prover-V2-32B · **Benchmark:** miniF2F · **Candidate:** `imo_1984_p6_g20`.

The response uses two comparisons with b to infer an unsupported comparison between a·2^t and a+2.

**Statement from the final model candidate:**

```lean
theorem imo_1984_p6 (a b c d k m : ℕ) (h₀ : 0 < a ∧ 0 < b ∧ 0 < c ∧ 0 < d)
    (h₁ : Odd a ∧ Odd b ∧ Odd c ∧ Odd d) (h₂ : a < b ∧ b < c ∧ c < d) (h₃ : a * d = b * c)
    (h₄ : a + d = 2 ^ k) (h₅ : b + c = 2 ^ m) : a = 1 := by
```

Read the [complete original model output](model_output.txt), [verbatim excerpts with source lines](case_excerpt.md), and [original verification record and provenance](verification.json).

## 3. Mathematical explanation

The problem assumes positive odd integers $a<b<c<d$, $ad=bc$, $a+d=2^k$, and $b+c=2^m$, and asks for $a=1$.

The premises preceding the defective step have a valid derivation. Since $(a-b)(a-c)>0$ and $ad=bc$,

$$a\bigl((a+d)-(b+c)\bigr)=(a-b)(a-c)>0.$$

Thus $2^k>2^m$, so $t=k-m\ge1$. Also,

$$a2^k-b2^m=a(a+d)-b(b+c)=a^2-b^2<0,$$

which gives $a2^t<b$ after division by $2^m>0$. Since $a$ and $b$ are distinct odd integers, $a+2\le b$.

The response then infers $a2^t<a+2$. This inference fails: from $x<b$ and $y\le b$, there is no determined ordering between $x$ and $y$. Take $a=3$, $t=1$, and $b=7$. Then $a2^t=6<7$ and $a+2=5\le7$, but $6<5$ is false.

This is a counterexample to the **displayed local implication**, not a tuple claimed to satisfy all hypotheses of the original theorem. It does not refute the theorem. It establishes that these two premises alone cannot justify the conclusion; a further restriction linking $b$ to $a+2$ would be needed.

The subsequent deduction $a(2^t-1)<2$, and hence $a=1$, rests on that unsupported step. The response questions it at lines 379–381, but repeats it at lines 429–458. Both the doubt and repetition are retained. The three saved compiler errors provide execution context; they are not used to infer this mathematical defect.
