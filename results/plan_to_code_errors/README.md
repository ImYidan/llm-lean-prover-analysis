# Plan-to-code errors

This collection documents three manually defined translation mechanisms used in the thesis's plan-to-code analysis (§6.3.2). Each category follows **definition → case study → mathematical and Lean explanation**. All three examples are Goedel-Prover-V2-32B candidates on miniF2F.

## Category index

| Category | Definition | Candidate |
|---|---|---|
| [Representation Errors](01_representation_errors/README.md) | A mathematical object is encoded with an unintended type, domain, coercion, or data representation. | `amc12a_2021_p14_g9` |
| [Library Application Errors](02_library_application_errors/README.md) | A valid local step is connected to the library through an unavailable name, incompatible arguments, or an unbridged predicate. | `amc12a_2003_p23_g0` |
| [Proof-Step Assembly Errors](03_proof_step_assembly_errors/README.md) | Appropriate facts are not arranged to match the current goal, for example because reassociation or another intermediate transformation is missing. | `algebra_sum1onsqrt2to1onsqrt10000lt198_g27` |

## Mathematical validity and translation mechanisms

Each example first establishes the intended **local mathematical step** independently. The logarithmic sums reduce to a finite natural-index sum and product 21000. Prime divisibility of a finite product reduces to divisibility of a factor. The reciprocal-square-root bound telescopes to 198, and its local identity uses the square of a square root.

The mechanism then describes how that step was expressed in Lean. This is a separate axis from [compiler diagnostic categories](../compiler_diagnostics/README.md): the selected representation defect emits Missing instance, the unavailable library name emits Unresolved name, and the unprepared rewrite emits Tactic failure. Those correspondences describe these examples, not a universal mapping from compiler labels to translation mechanisms.

Labels describe local mechanism incidence. They do not require a candidate to be free of all other mathematical or formal errors, and they are not necessarily exclusive. The library example contains other arithmetic mistakes; the assembly example has an incorrect exploratory aside outside its selected range. Their complete responses retain those details. The [mathematical reasoning collection](../mathematical_reasoning_errors/README.md) addresses mathematical defects explicitly and uses three different problems.

## Files and provenance

| File in each category | Content |
|---|---|
| `README.md` | Definition, identified example, mathematical derivation, Lean mechanism, and limits of the local correction. |
| `model_output.txt` | Complete decoded source response, including all saved informal reasoning, attempts and final code; no edits or added newline. |
| `case_excerpt.md` | Verbatim informal and formal passages with inclusive one-based source lines, plus the complete selected original diagnostic. |
| `verification.json` | Original verifier record, input statement and extracted code, source filenames/fingerprints/indices, output and excerpt hashes, problem scope, and analyst-written local Lean checks. |

Responses are extracted from `full_records.json` and paired by candidate ID with `code_compilation_repl.json`; their zero-based indices can differ. The complete run artifacts remain external. Hashes cover UTF-8 bytes, including original line endings. The selected outputs and all their saved compiler errors are included here.

All three problems have zero successful candidates among 32 under the strict saved verdict (`pass`, `complete`, and no `sorries`). Their selection supplies qualitative evidence, not translation-category frequency estimates, and does not change the statistical tables.

Compiler positions refer to the submitted code in `verification_record.code`; excerpt positions refer to `model_output.txt`. The input statement, generation-side extracted code and verifier submission are preserved separately because the harness transforms headers and comments.

## Local Lean validation

Seven analyst-written minimal checks were run in Lean **4.9.0-rc1** (commit `be6c4894e0a6`) with Mathlib revision **`2f65ba7f1a9144b20c8e7358513548e317d26de1`**. Code, command, stdout, stderr, exit status and source hash are saved under `local_checks` in each category's `verification.json`. These checks isolate local obligations; they do not rerun or repair the complete original candidates.

| Mechanism | Original local check | Intermediate check | Corrected local check |
|---|---|---|---|
| Representation | Untyped finite interval requests `LocallyFiniteOrder ℝ`; exit 1. | — | Explicit natural-number interval, real-valued summand, sum 210; exit 0. |
| Library application | `Finset.Prime.dvd_prod_iff` is unavailable; exit 1. | Correct declaration name with `Nat.Prime` argument still gives a type mismatch; exit 1. | `Prime.dvd_finset_prod_iff` with `hp.prime` and product function; exit 0. |
| Proof-step assembly | `rw` cannot find the square-root product in a left-associated expression; exit 1. | — | Reassociate with `mul_assoc`, then rewrite the square; exit 0. |

To reproduce a check in a workspace with those versions, save its `local_checks.checks[].source` string as a Lean file and run `lake env lean path/to/check.lean`, or pass the string to `lake env lean --stdin` as recorded. Failed controls are expected; they reproduce the identified local symptoms. A successful corrected control establishes only the stated minimized obligation. It does not establish that the complete candidate would pass verification.
