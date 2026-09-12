# Eight-category case studies

Each category follows the same reading order: **definition → case study → explanation**. The eight candidates are the examples used in thesis Table 6.1. Seven come from Goedel-Prover-V2-32B on miniF2F; the termination example comes from Kimina-Prover-Distill-8B on FATE-M.

A case illustrates a selected diagnostic within a candidate. It does not assign an exclusive primary label to that candidate, and it does not change the full eight-category statistics. Multiple categories can occur in the same verification record.

## Category index

| Category | Definition | Case candidate |
|---|---|---|
| [Syntax error](01_syntax_error/README.md) | Lean cannot parse the text at the reported position. | `mathd_algebra_125_g30` (miniF2F) |
| [Unresolved name](02_unresolved_name/README.md) | A referenced name cannot be resolved uniquely in the available environment; the mapping also covers related name conflicts. | `amc12a_2021_p12_g29` (miniF2F) |
| [Type mismatch](03_type_mismatch/README.md) | A term does not satisfy its expected type or elaboration requirements. | `amc12b_2002_p4_g24` (miniF2F) |
| [Missing instance](04_missing_instance/README.md) | Lean cannot synthesize a required type-class instance. | `amc12a_2021_p14_g9` (miniF2F) |
| [Tactic failure](05_tactic_failure/README.md) | A recognized tactic cannot perform its requested operation in the current proof state. | `induction_pord1p1on2powklt5on2_g27` (miniF2F) |
| [Unsolved goals](06_unsolved_goals/README.md) | A proof or local tactic block finishes with goals still open. | `amc12a_2003_p23_g8` (miniF2F) |
| [Termination failure](07_termination_failure/README.md) | Lean cannot justify termination of a recursive declaration. | `FATE-M_006_g23` (FATE-M) |
| [Resource exhaustion](08_resource_exhaustion/README.md) | Checking encounters a configured recursion, heartbeat, time or memory limit. | `mathd_numbertheory_451_g10` (miniF2F) |

The Syntax error example is a failed candidate from a problem solved by 22 of its 32 candidates. It is therefore outside the published Pass@32-unsolved-problem statistics and is included here only as the thesis's qualitative illustration. The other seven examples come from problems with zero successes in their corresponding 32-candidate runs. Each `verification.json` records this scope distinction. Adding these case-study documents does not change the statistical tables.

## Files in each category directory

| File | Purpose |
|---|---|
| `README.md` | Definition, identified case and explanation, including the limits of what the diagnostic establishes. |
| `model_output.txt` | The complete decoded `model_output` string, including all saved prose, reasoning and code blocks, written without edits or an added newline. |
| `case_excerpt.md` | Verbatim ranges from the final model candidate, the complete selected diagnostic and a note explaining how the thesis shortened its presentation. |
| `verification.json` | Original verification record, generation-side extracted code and input statement, source artifact fingerprints and record indices, selected diagnostic index, and hashes/line ranges for the original output and excerpts. |

## Evidence and scope

The Goedel outputs are extracted from `full_records.json` and paired by candidate ID with `code_compilation_repl.json`. The Kimina output is extracted from `generation.jsonl` and paired with `verification.jsonl`. Generation and verification records can occur in different orders: pairing uses the candidate identifier, not a shared row number. The exact source filenames, SHA-256 fingerprints and zero-based indices are recorded per case.

The model response, generation-side extracted code and verifier submission are different artifacts. In these records the harness changes headers and removes material such as comments during extraction/submission. Compiler line numbers therefore refer to the saved submitted code (`verification_record.code` for Goedel; `verification_record.lean_messages.verified_code` for Kimina). Excerpt line numbers refer to `model_output.txt`. The original benchmark input may contain a `sorry` placeholder; it is labelled as input and is separate from the generated candidate.

The thesis uses abbreviated expressions, presentation variables and typesetting substitutions. `case_excerpt.md` identifies these differences and supplies the corresponding raw passage. In particular, the Unsolved goals candidate contains a follow-up `simpa` and a type-mismatch diagnostic that the paper's compact illustration does not display.

Definitions describe observed compiler symptoms. Explanations distinguish the saved diagnostic from conclusions supported by the code, local library signatures or explicit arithmetic. They do not establish a successful repair, a unique global root cause, or model-wide frequency patterns. No Lean recompilation or repaired-proof evaluation was performed when preparing this package; the historical verifier records are preserved as evidence.

The mathematical checks used in the two counterexamples are elementary: the product through n = 2 is 15/8, for which multiplication by 3/2 exceeds 5/2; and 625 divides the product of 1! through 9! but not 146313216000. The name-resolution and rational-representation explanations refer to the checked Mathlib revision `2f65ba7f1a9144b20c8e7358513548e317d26de1` and give the source file/line in the corresponding case.

The full source runs remain external experiment artifacts. Only the eight selected responses and their supporting verification records are included here.
