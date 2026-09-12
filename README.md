# LLM Lean Prover Analysis

Analysis code for the [LLM Lean prover experiments](https://github.com/ImYidan/llm-lean-prover-evaluation).

## Raw compiler-error inventory

Use `scan_raw_errors.py` to extract Lean error messages from saved verification results before assigning the eight error categories. The script preserves diagnostic text and counts distinct, verbatim first lines. It does not mask identifiers or merge messages into templates.

The study uses **all candidates belonging to problems that remain unsolved at Pass@32**. A problem enters the analysis only if none of its candidates passes verification. Failed candidates from a problem with a successful candidate are outside this scope.

Supply the complete Pass@32 verification artifact for one model and benchmark, including successful candidates. The scanner determines solved status from the supplied records; it does not verify that the input contains a complete 32-candidate run. The summary therefore reports problems unsolved *in the input*. With partial inputs, this need not equal the study's Pass@32 scope.

## Run

Requires Python 3.10 or later, with no third-party dependencies. Download verification results separately and provide their paths:

```bash
python3 scan_raw_errors.py \
  --input /path/to/code_compilation_repl.json \
  --input-format standard-json \
  --model Goedel-32B \
  --benchmark miniF2F \
  --output-dir outputs/goedel32b/minif2f
```

Repeat the command for each model and benchmark. For an analysis with a problem exclusion list, append:

```bash
  --exclude-problems /path/to/excluded_problems.json
```

The exclusion file accepts a JSON list of problem-name strings or objects with `name` or `problem_id`. Exclusions apply before solved/unsolved selection. Missing exclusions raise an error unless you pass `--allow-missing-exclusions`; the summary records the requested, applied and missing counts.

## Input formats

These adapters read the historical verification artifacts used for the error analysis. Choose the format from the file's structure, not its extension alone.

| `--input-format` | Structure and identifying fields | Successful candidate |
|---|---|---|
| `standard-json` | JSON list; `name` contains the problem name plus `_gN`; `compilation_result.errors` contains diagnostic objects with `severity`, `data` and optional `pos` | `compilation_result.pass` and `complete` are true, with no `sorries` |
| `kimina-jsonl` | One candidate per line; `name` identifies the problem and `problem_id` identifies the candidate; `error` joins messages as `[line:column] message \|\| [line:column] message` | `success` is true |
| `pythagoras-minif2f-json` | JSON list with one object per problem; `name`, `num_samples` (or `n`, default 32), and `proof_verification_result_1` through `_N` | Same rule as `standard-json` |
| `pythagoras-jsonl` | One candidate per line; `problem_id`, `sample_idx`, and `error` containing Lean CLI output | `success` is true |

Goedel-32B, Goedel-8B and DeepSeek use `standard-json`. For the two JSONL formats, `success` may be a boolean or its string representation. The scanner trusts the verifier's success field and does not recheck proofs.

Problem identity follows each artifact's fields. In particular, historical Kimina ProofNet rows share 181 origin names across 186 statement rows, whereas Pythagoras ProofNet uses 186 statement IDs. This retains the grouping used by the corresponding error-analysis results.

## Outputs and counting

Each command writes three files in `--output-dir`, replacing previous files with the same names:

| File | Contents |
|---|---|
| `raw_errors.jsonl` | One row for each parsed error diagnostic, including repeated messages: problem/sample IDs, source record index, diagnostic index, line/column, full available message, verbatim first line, and `counted` flag |
| `raw_error_counts.csv` | First-line frequencies, descending by count; columns: `rank`, `count`, `ratio`, `raw_error_head` |
| `summary.json` | Input filename and SHA-256, scope, candidate/problem counts, exclusions, diagnostic counts and parsing limitations |

`source_record_index` is zero-based: the input array index or nonblank JSONL record index. For nested Pythagoras miniF2F, it refers to the problem object; the sample ID identifies its numbered verification result. `diagnostic_index` is zero-based among the errors retained by the adapter for that candidate.

The default frequency key is **(candidate record, source line, source column, raw message first line)**. Repeated reports at the same position in one candidate count once; reports at different positions count separately. All parsed reports remain in `raw_errors.jsonl`, including those with `counted: false`. When positions are absent, identical heads in that candidate share the `(null, null)` position.

To count every parsed diagnostic in the frequency table, add `--count-rule raw`. `ratio` is a percentage of the counted occurrences, expressed from 0 to 100. The summary records both the diagnostic total before deduplication and the counted total. Neither rule selects just the first diagnostic of each candidate.

The first line is the parsed message text before its line ending. Names, punctuation and case remain unchanged. The Kimina adapter removes position markers and their following whitespace before extracting the message, as in the historical analysis. Multiline context stays in the JSONL `message` field. No eight-category labels or normalized templates are produced at this stage.

## Diagnostic coverage

- Structured REPL adapters retain only entries with `severity: error` and string `data`; warnings are outside the inventory.
- Kimina's saved error field contains flattened error messages. The adapter splits its position markers and excludes the recorded noncompiler types `generation_truncated_before_final_lean`, `no_theorem_header_before_cutoff`, `timeout` and `uses_sorry`. It retains a nonempty, unpositioned message for other types, matching the historical analysis; the flattened file has no per-message severity field to recheck.
- Pythagoras CLI parsing retains positioned `error:` messages and the unpositioned `Error in Linarith` form. It separates positioned warnings and leaves other unpositioned outcomes outside the diagnostic inventory.
- Historical Pythagoras JSONL output is capped at 2,000 characters. If this cuts the final error's first line, the adapter excludes that fragment and increments `truncated_final_diagnostics_excluded`. Messages whose first line survives may still have truncated bodies. The scanner cannot recover text absent from the saved artifact.
- `samples_without_compiler_error` means no retained compiler diagnostic. It does not mean a successful proof: extraction failures, timeouts and other verifier outcomes can have no compiler error message.

Experiment data, generated inventories and local audit files are stored separately from this code repository.
