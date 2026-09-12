# False intermediate claim: original excerpts

**Candidate:** `mathd_numbertheory_764_g15`. All source ranges below are one-based, inclusive lines in [model_output.txt](model_output.txt). Text inside each source block is verbatim; headings and provenance notes are editorial. Hashes cover the original range bytes, including existing line endings.

## Statement from the final candidate (lines 195–196)

```lean
theorem mathd_numbertheory_764 (p : ℕ) (h₀ : Nat.Prime p) (h₁ : 7 ≤ p) :
    (∑ k in Finset.Icc 1 (p - 2), (k : ZMod p)⁻¹ * ((k : ZMod p) + 1)⁻¹) = 2 := by
```

## Original model response (lines 15–39)

```text
2. **Telescoping Approach**: The term $k^{-1}(k+1)^{-1}$ can be rewritten as $(k+1 - k)k^{-1}(k+1)^{-1} = (k+1)^{-1} - k^{-1}$. However, this doesn't immediately give a telescoping sum because of the coefficient $(k+1 - k) = 1$. Let's check this carefully:
   $$
   (k+1)^{-1} - k^{-1} = (k+1 - k)(k^{-1}(k+1)^{-1}) = k^{-1}(k+1)^{-1}.
   $$
   So, indeed:
   $$
   k^{-1}(k+1)^{-1} = (k+1)^{-1} - k^{-1}.
   $$

3. **Telescoping Sum**: Using the above identity, the sum $S$ becomes:
   $$
   S = \sum_{k=1}^{p-2} \left( (k+1)^{-1} - k^{-1} \right) = (p-1)^{-1} - 1^{-1}.
   $$
   But $(p-1) \equiv -1 \pmod{p}$, so $(p-1)^{-1} \equiv -1 \pmod{p}$. Therefore:
   $$
   S \equiv -1 - 1 = -2 \equiv p - 2 \pmod{p}.
   $$
   **Wait a minute!** This doesn't match the expected result of $2$. Did I make a mistake?

   **Yes!** Actually, the sum is from $k = 1$ to $k = p-2$, so the telescoping gives:
   $$
   S = (2^{-1} - 1^{-1}) + (3^{-1} - 2^{-1}) + \cdots + ((p-1)^{-1} - (p-2)^{-1}) = (p-1)^{-1} - 1^{-1}.
   $$
   So the calculation was correct. But the expected answer in the problem is $2$, whereas I got $-2 \equiv p - 2$. Are these equal modulo $p$? Only if $p - 2 \equiv 2 \pmod{p}$, i.e., $p \mid 4$. But $p \geq 7$, so this is not the case unless $p = 2$, which it isn't. 

```

## Original model response (lines 79–121)

```text
**Where is the discrepancy?**

Ah! My telescoping was wrong. Actually:
$$
\sum_{k=1}^{p-2} ( (k+1)^{-1} - k^{-1} ) = (p-1)^{-1} - 1^{-1},
$$
but the sum is $\sum_{k=1}^{p-2} k^{-1}(k+1)^{-1}$, and $k^{-1}(k+1)^{-1} \neq (k+1)^{-1} - k^{-1}$. 

Let me re-examine that step:
$$
(k+1)^{-1} - k^{-1} = (k+1 - k)/(k(k+1)) = 1/(k(k+1)) = k^{-1}(k+1)^{-1}.
$$
No, this is correct in a field! Because $(k+1)^{-1} - k^{-1} = \frac{1}{k+1} - \frac{1}{k} = \frac{k - (k+1)}{k(k+1)} = \frac{-1}{k(k+1)} = -k^{-1}(k+1)^{-1}.$$

**Ah! The sign was wrong!** 

Actually:
$$
(k+1)^{-1} - k^{-1} = -k^{-1}(k+1)^{-1}.
$$
Thus:
$$
k^{-1}(k+1)^{-1} = -( (k+1)^{-1} - k^{-1} ) = k^{-1} - (k+1)^{-1}.
$$

Then the sum becomes:
$$
\sum_{k=1}^{p-2} (k^{-1} - (k+1)^{-1}) = 1^{-1} - (p-1)^{-1}.
$$

Now, $(p-1)^{-1} \equiv -1 \pmod{p}$, so:
$$
S \equiv 1 - (-1) = 2 \pmod{p}.
$$

This matches the manual calculation for $p=7$. 

**Conclusion**: The correct identity is $k^{-1}(k+1)^{-1} = k^{-1} - (k+1)^{-1}$ (in a field of characteristic not 2), and the telescoping gives $1 - (p-1)^{-1} \equiv 2 \pmod{p}$.

But wait, let me rederive the identity carefully:
$$
k^{-1} - (k+1)^{-1} = \frac{1}{k} - \frac{1}{k+1} = \frac{(k+1) - k}{k(k+1)} = \frac{1}{k(k+1)} = k^{-1}(k+1)^{-1}.
$$
```

## Original verification context

The complete historical verification record is in [verification.json](verification.json). Its compiler errors are separate from the mathematical evidence above; they do not establish the mathematical label.

## Context and selection

Both the original false identity and the later sign correction are reproduced. The correction at line 93 is part of the source response. A shortened presentation ending at the model's initial surprise must not be read as evidence that it never located the error.
