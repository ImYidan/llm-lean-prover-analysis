# Mathematical reasoning errors

This collection documents three manually defined categories used in the thesis's mathematical-reasoning analysis (§6.3.1). Each category follows **definition → case study → mathematical explanation**, with the complete original model response and a separate verbatim excerpt. All three examples are Goedel-Prover-V2-32B candidates on miniF2F.

## Category index

| Category | Definition | Candidate |
|---|---|---|
| [Insufficient proof strategy](01_insufficient_proof_strategy/README.md) | The proposed steps lack the mathematical structure needed to establish the target, such as an induction invariant or quantitative tail bound. | `induction_pord1p1on2powklt5on2_g7` |
| [False intermediate claim](02_false_intermediate_claim/README.md) | An asserted intermediate statement is false under its assumptions, as shown by calculation or counterexample. | `mathd_numbertheory_764_g15` |
| [Invalid inference](03_invalid_inference/README.md) | The conclusion of a particular step does not follow from the premises used, even when those premises are valid. | `imo_1984_p6_g20` |

## Interpretation and category boundaries

These labels concern mathematical reasoning, not the eight observable [compiler diagnostic categories](../compiler_diagnostics/README.md). A Lean error, an unfinished proof, or uncertain prose alone does not establish a mathematical defect. Each explanation identifies a specific deficient step and supplies an independent mathematical check.

The insufficient-strategy case demonstrates why its proposed induction hypothesis cannot close the next step, then supplies a finite-prefix and tail bound. The false-claim case falsifies a reciprocal identity modulo 7 and derives the correct telescoping sum. The invalid-inference case gives a counterexample to the displayed implication without claiming a counterexample to the original theorem.

The categories distinguish the focus of the analysis: missing mathematical control, a false asserted statement, and an invalid implication. They are not necessarily exclusive at candidate level. One response can contain multiple errors or both viable and inadequate approaches. These examples do not constitute an exhaustive annotation of the corpus, and no category frequencies are inferred from them.

**Self-correction is retained.** In the false-claim example, the model later identifies and corrects its sign error. This is a local false claim during the response, not a claim that the final plan retained that error. The insufficient-strategy excerpt concerns a selected late plan; it does not imply every earlier approach was invalid. The invalid-inference excerpt includes both the model's doubt and its later repetition of the step.

## Files and provenance

| File in each category | Content |
|---|---|
| `README.md` | Definition, identified example, original theorem statement, and mathematical explanation. Analyst-supplied derivations are distinguished from the model's text. |
| `model_output.txt` | The complete decoded source `model_output` string, without edits or an added newline. All saved reasoning, attempts, code blocks and corrections remain. |
| `case_excerpt.md` | Verbatim source ranges, inclusive one-based line numbers, and context explaining selection. |
| `verification.json` | Original verification record, input statement, generation-side extracted code, source filenames and SHA-256 fingerprints, record indices, output/excerpt hashes, and problem-level run scope. |

Responses come from `full_records.json` and are paired by candidate ID with `code_compilation_repl.json`. Generation and verification record indices are zero-based and need not agree. Output/excerpt hashes use UTF-8 bytes; excerpt hashes include the source's existing line endings. The original full-run artifacts remain external; the selected responses and verification records are included here.

All three problems have zero successful candidates among 32 under the saved strict verdict (`pass`, `complete`, and no `sorries`). They are therefore within the published unsolved-problem scope, but the cases are qualitative selections. The model output, extracted code, and submitted code are separate artifacts. Compiler positions refer to the submitted code in `verification_record.code`; excerpt positions refer to `model_output.txt`. The compiler diagnostics are preserved as execution context, not as automatic mathematical labels.

The mathematical explanations have been checked through exact calculations and derivations. No repaired full Lean proof is claimed for these cases. The separate [plan-to-code collection](../plan_to_code_errors/README.md) tests three local translation mechanisms on different mathematical problems.
