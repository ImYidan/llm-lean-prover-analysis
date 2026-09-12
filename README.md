# LLM Lean Prover Analysis

Code for the diagnostic analysis of the [LLM Lean prover experiments](https://github.com/ImYidan/llm-lean-prover-evaluation): complete error inventories, eight-category mappings, compiler-message templates, cumulative-50% error tables, and category heatmaps.

## Repository layout

| File | Responsibility |
|---|---|
| `scripts/scan_raw_errors.py` | Read verification artifacts and preserve all parsed diagnostics for problems unsolved in the input run. |
| `scripts/error_taxonomy.py` | Assign each diagnostic to one of the eight manually defined categories using fixed rules. |
| `scripts/error_templates.py` | Group diagnostic wordings into deterministic compiler-message templates. |
| `scripts/summarize_errors.py` | Produce mappings, template frequencies, Top50 coverage tables, category distributions by cell, and pooled distributions by model. |
| `scripts/plot_heatmaps.py` | Render and validate the category heatmaps. |
| `requirements.txt` | Pin the plotting dependency used for validation. |

All analysis code lives in `scripts/`. Published tables, compressed complete-message mappings, heatmaps and their Markdown guide live in [`results/`](results/README.md). Experiment inputs and intermediate candidate inventories are generated locally. The analysis does not run Lean or query a language model.

```text
scripts/                 Analysis scripts and mapping rules
results/
  README.md              Result index, scope and statistical overview
  tables/                CSV tables, metadata and compressed full-message mapping
  figures/               Cell and pooled-model heatmaps in PNG/PDF
README.md                Methods, commands and function reference
requirements.txt         Plotting dependency
```

## Install and run

Scanning, mapping and statistics require Python 3.10 or later and use only the standard library. The pinned plotting dependency requires Python 3.11 or later. To run the entire pipeline, use Python 3.11+:

```bash
python3 -m pip install -r requirements.txt
```

Run the following commands from the repository root. To redraw the published figures, run only the plotting command against `results/tables/`; no experiment inputs are needed. To regenerate all tables, the original verification artifacts and applicable exclusion lists are required.

First, scan one complete verification artifact for each model and benchmark. Include successful candidates in the input so that the script can identify solved problems:

```bash
python3 scripts/scan_raw_errors.py \
  --input /path/to/code_compilation_repl.json \
  --input-format standard-json \
  --model Goedel-32B \
  --benchmark miniF2F \
  --output-dir results/scans/goedel32b/minif2f
```

Repeat for the other cells, choosing the adapter from the table below. Keep one scan directory per model–benchmark pair under `results/scans/`. Use consistent model and benchmark labels across commands.

For problem exclusions, append `--exclude-problems /path/to/excluded_problems.json` to the scan command. The file accepts a JSON list of names, or objects with `name` or `problem_id`. Exclusions apply before solved/unsolved selection. Missing exclusions cause an error unless `--allow-missing-exclusions` is supplied; the summary records requested, applied and missing counts.

Next, build all statistical tables and figures:

```bash
python3 scripts/summarize_errors.py \
  --input-dir results/scans \
  --output-dir results/tables

python3 scripts/plot_heatmaps.py \
  --input-dir results/tables \
  --output-dir results/figures
```

The summarizer finds scanner `summary.json` files recursively. It checks their schema, rejects duplicate model–benchmark cells and mixed scan counting rules, and verifies diagnostic totals against each inventory. Output metadata lists the supplied cells; supplying a subset produces a subset analysis.

## Input adapters and study scope

The historical study analyzes **all candidates of problems that remain unsolved at Pass@32**. A problem enters the scope only if none of its supplied candidates succeeds. Failed candidates of already solved problems are outside this scope.

The scanner determines solved status from the supplied records. It does not verify that the input is a complete 32-candidate run. With partial inputs, its `unsolved-problems-in-input` scope need not equal the study's Pass@32 scope.

| `--input-format` | Input structure and problem/candidate identity | Successful candidate |
|---|---|---|
| `standard-json` | JSON list; `name` identifies a candidate with a final `_gN` suffix; `compilation_result.errors` holds diagnostic objects. Used for Goedel-32B, Goedel-8B and DeepSeek. | Both `compilation_result.pass` and `complete` are true, with no `sorries`. |
| `kimina-jsonl` | One candidate per line; `name` identifies the problem, `problem_id` identifies the candidate, and `error` contains flattened diagnostics. | `success` is true. |
| `pythagoras-minif2f-json` | JSON list with one object per problem; `name`, `num_samples` (or `n`, default 32), and `proof_verification_result_1` through `_N`. | Same structured verdict as `standard-json`. |
| `pythagoras-jsonl` | One candidate per line; `problem_id`, `sample_idx`, and `error` containing Lean CLI output. | `success` is true. |

The JSONL success field can be a boolean or its string representation. The adapters retain historical problem grouping: Kimina ProofNet groups 186 statement rows by 181 origin names; Pythagoras ProofNet uses 186 statement IDs. They trust the stored verifier verdicts.

## Complete diagnostics and counting units

The scanner writes every retained diagnostic's **complete available message**, including multiline goal context, to `raw_errors.jsonl`. A candidate can contribute multiple diagnostics and multiple categories. The analysis never selects one first error or one primary category per candidate.

Two counts are available:

- **Diagnostic count:** every parsed error message counts, including repeated reports.
- **Occurrence count:** the historical default counts once per `(candidate record, source line, source column, diagnostic header)`. A header is the message's first line. Repetitions at the same position count once; different positions or candidate records count separately. Missing positions share `(null, null)` within that candidate.

The header serves only as a technical key for the existing deduplication, mapping and template rules. Complete messages remain available for examination. When repeated messages share a deduplication key but have different bodies, the first parsed report receives the occurrence count; all reports still contribute to diagnostic counts.

By default, `scripts/summarize_errors.py` uses occurrence counts to reproduce the historical tables. To base the entire analysis on every diagnostic, including repeats, use a separate output directory:

```bash
python3 scripts/summarize_errors.py \
  --input-dir results/scans \
  --count-unit diagnostic \
  --output-dir results/local/tables_diagnostic
```

No rescan is needed for this alternative. The scanner also accepts `--count-rule raw`, which marks every parsed diagnostic as a counted occurrence; use the same scanner rule across all cells. `analysis_summary.json` records both the scanner rule and the chosen analysis unit.

## Eight categories and template grouping

The eight categories are a **manually defined taxonomy**. `classify_error(message)` applies ordered string/regular-expression rules to each diagnostic independently. This is an operational classification of compiler symptoms, not an inferred mathematical root cause.

| Category | Operational meaning |
|---|---|
| Syntax error | Lean rejects the generated syntax. |
| Unresolved name | A name, declaration, tactic, namespace or field cannot be resolved, is ambiguous, or conflicts with another declaration. |
| Type mismatch | Elaboration or type checking fails. The fixed scheme also includes rare kernel-evaluation and code-generation diagnostics here. |
| Missing instance | Typeclass synthesis fails or an instance is required. |
| Tactic failure | A recognized tactic rejects its arguments or goal, fails to transform/prove it, or makes no progress. |
| Unsolved goals | A proof or tactic block ends with remaining goals. |
| Termination failure | Lean cannot establish termination of a recursive definition. |
| Resource exhaustion | Lean reports a heartbeat, deterministic-time, recursion-depth or memory limit. |

Specific wording overrides run before broad fallback patterns. Rule order can resolve overlapping wording *within one diagnostic*; it does not prioritize one diagnostic over the others in a candidate. An unknown diagnostic raises an error with its cell and message context. There is no silent `Other` assignment.

`compiler_template(category, message)` performs **rule-based template aggregation**. It masks concrete identifiers, terms, token spellings and numeric values while retaining failure wording and meaningful suffixes. It uses category-specific rules; it is not a learned or unsupervised clustering algorithm.

```python
from scripts.error_taxonomy import classify_error
from scripts.error_templates import compiler_template

message = "unknown identifier 'Example.lemma'\n⊢ P"
category = classify_error(message)                 # Unresolved name
template = compiler_template(category, message)    # unknown identifier 'ID'
# The complete message is retained separately in the diagnostic inventory.
```

The historical mappings and templates inspect each diagnostic's header. Goal-state words in the body do not override the diagnostic emitter's category. Distinct complete messages can therefore share a template. `mapped_errors.csv` records each full message's category, template and counts so that this grouping remains auditable.

## Top50 means cumulative coverage

For each model–benchmark cell independently, rank **aggregated error templates** by count and select the descending prefix that reaches at least 50% of eligible errors. Include every template tied at the cutoff count. Thus the number of selected templates varies by cell, and coverage can exceed 50% substantially when counts tie. It is not a list of exactly 50 errors.

The default `--top50-policy historical` reproduces the study's ranking exclusions:

- Exclude `Resource exhaustion` from the ranking and its denominator.
- Exclude the `no goals to be solved` template because it reports continued tactic execution after a goal has closed.

These exclusions apply **only to Top50**, not to the eight-category tables or heatmaps. `top50_summary.csv` records the original count, each excluded count, eligible denominator, cutoff and achieved coverage. To rank all categories and templates, use `--top50-policy all` with a separate output directory.

## Category tables and heatmaps

`categories_by_cell.csv` keeps a separate denominator for each model–benchmark pair. `categories_by_model.csv` first sums category counts across the supplied benchmarks for each model, then divides by that model's pooled total. It does not average benchmark percentages: benchmarks contributing more counted errors receive more weight.

Both tables contain all eight categories, including zero-count rows. Percentages range from 0 to 100 and use six decimal places; a zero denominator has a blank percentage. For five models and five benchmarks, the cell table has 200 rows and the pooled table has 40 rows.

The plotting script reads the two category CSVs and the required `analysis_summary.json`. It validates the recorded counting unit, category completeness, duplicate rows, nonnegative counts, denominator conservation and percentage consistency before drawing. Each exported figure identifies error occurrences or error diagnostics on its colorbar and footnote. Both heatmaps follow the thesis presentation with muted blue shading, serif labels and categories on the vertical axis. The cell heatmap groups model columns under benchmark headings; the pooled heatmap has one column per model. Both share one color scale starting at zero, with its upper limit rounded up from the largest percentage across the two matrices to the next multiple of ten (0–60% for the published data). Gray `NA` cells indicate zero denominators. Numeric cell annotations are omitted for readability; exact percentages remain in the CSV tables. G32/G8 denote Goedel-32B/8B, DS7 denotes DeepSeek, K8 denotes Kimina and P4 denotes Pythagoras. Only the visual style follows the thesis: these figures retain the full eight-category error-occurrence analysis, including resource exhaustion and `no goals to be solved`.

## Output files and columns

Scanner outputs in each cell directory:

| File | Fields and interpretation |
|---|---|
| `raw_errors.jsonl` | `source_record_index`, `problem_id`, `sample_id`, `diagnostic_index`, `line`, `column`, complete `message`, and boolean `counted` for the occurrence rule. Repeated reports are retained. |
| `raw_error_counts.csv` | `rank`, `diagnostic_count`, `occurrence_count`, `raw_error_message`. One row per distinct complete message; rank sorts by occurrence count, diagnostic count, then message. Zero-occurrence rows retain reports suppressed by deduplication. |
| `summary.json` | Schema version 2; model/benchmark, input and exclusion filenames/SHA-256 fingerprints, scope and denominator counts, parsing exclusions, both error totals and number of distinct complete messages. |

`source_record_index` is zero-based: an input array index or nonblank JSONL record index. For nested Pythagoras miniF2F it identifies the problem object; the sample ID identifies its numbered verification result. `diagnostic_index` is zero-based among retained diagnostics in that candidate.

Statistical outputs in the table directory:

| File | Fields and interpretation |
|---|---|
| `mapped_errors.csv` | `model`, `benchmark`, `category`, `template`, `diagnostic_count`, `occurrence_count`, selected-unit `count`, and complete `raw_error_message`. Includes distinct messages with zero selected-unit count. |
| `template_counts.csv` | `model`, `benchmark`, `category`, `template`, `count`, full-cell `denominator`, `percentage`. Only positive template counts appear. |
| `top50_errors.csv` | `model`, `benchmark`, `rank`, `category`, `template`, `count`, eligible `denominator`, `percentage`, `cumulative_count`, `cumulative_percentage`, `cutoff_count`. |
| `top50_summary.csv` | `model`, `benchmark`, `original_count`, `excluded_resource_count`, `excluded_no_goals_count`, `eligible_denominator`, `selected_template_count`, `selected_count`, `coverage_percentage`, `cutoff_count`. |
| `categories_by_cell.csv` | `model`, `benchmark`, `category`, `count`, `denominator`, `percentage`. All eight categories per supplied cell. |
| `categories_by_model.csv` | `model`, `category`, `count`, `denominator`, `percentage`. All eight categories per model, pooling counts across supplied benchmarks. |
| `analysis_summary.json` | Counting rule/unit, Top50 policy, coverage threshold/tie policy, supplied cell/model counts, total counts, taxonomy order and each input scan's metadata. |

Figures: `category_heatmap_by_cell.png`, `category_heatmap_by_cell.pdf`, `category_heatmap_by_model.png` and `category_heatmap_by_model.pdf`.

The published full-message mapping is losslessly compressed as `results/tables/mapped_errors.csv.gz`; the summarizer produces its uncompressed CSV. See [the result guide](results/README.md) for reading and compression commands. Intermediate `results/scans/`, alternative local analyses under `results/local/`, and the uncompressed mapping are ignored by Git.

Commands replace their own output filenames. The summarizer builds in a temporary directory and publishes only after all cells pass mapping and conservation checks. Complete diagnostic fields can exceed Python CSV's default field-size limit; readers of the full-message CSVs may need `csv.field_size_limit(sys.maxsize)`. JSONL preserves these messages without that CSV limit.

## Limits of the saved diagnostics

- Structured adapters retain string-valued `severity: error` messages; they exclude warnings.
- Kimina stores flattened errors as `[line:column] message || [line:column] message`. Its adapter removes markers and their following whitespace. It excludes `generation_truncated_before_final_lean`, `no_theorem_header_before_cutoff`, `timeout` and `uses_sorry`. Other nonempty, unpositioned messages follow the historical parser; the flattened data has no per-message severity to recheck.
- Pythagoras CLI parsing retains positioned `error:` messages and the unpositioned `Error in Linarith` form. Other unpositioned outcomes and positioned warnings remain outside this compiler-diagnostic inventory.
- Historical Pythagoras JSONL caps CLI output at 2,000 characters. The adapter excludes a final diagnostic when this cap cuts its header and records `truncated_final_diagnostics_excluded`. A retained message can still have a truncated body. No step recovers text absent from the saved artifact.
- `samples_without_compiler_error` means no retained diagnostic; it does not establish proof success. Extraction failures, timeouts and other verifier outcomes may have no Lean error message.

## Function reference

Each function also has a source docstring. Pure mapping helpers do not modify raw input; the command entry points handle filesystem outputs.

### scripts/scan_raw_errors.py

| Function | Purpose |
|---|---|
| `problem_id()` | Remove the final generation suffix, e.g. ``_g17``. |
| `is_pass()` | Return the structured verifier verdict: pass and complete must be true and sorries empty; no Lean rerun occurs. |
| `load_excluded_problems()` | Read an optional JSON exclusion list into problem IDs; reject malformed names or list entries. |
| `load_input()` | Read historical JSON/JSONL verification objects; expand nested Pythagoras miniF2F samples and retain their source indices. |
| `row_problem()` | Return the problem identifier under the selected historical adapter, preserving its original grouping semantics. |
| `row_sample()` | Return the candidate identifier under the selected adapter; preserve the original generation numbering. |
| `row_success()` | Return the stored candidate-success verdict using the adapter-specific fields. |
| `message_head()` | Return the diagnostic header used internally for historical deduplication; keep the complete message in outputs. |
| `standard_diagnostics()` | Yield line, column and full message for structured severity=error entries; ignore warnings and non-string payloads. |
| `kimina_diagnostics()` | Yield errors split from flattened Kimina messages, excluding known noncompiler outcomes and stripping position markers. |
| `pythagoras_diagnostics()` | Extract only Lean errors from Pythagoras CLI output. |
| `pythagoras_truncated_final_diagnostic()` | Return 1 when the 2,000-character CLI cap cuts a final error head. |
| `diagnostics_for_format()` | Return the diagnostic parser for one supported input format; raise ValueError for an unsupported format. |
| `parse_args()` | Parse required input/format/model/benchmark/output paths and explicit exclusion/counting options from the CLI. |
| `file_sha256()` | Stream a local file to compute its SHA-256 fingerprint without loading a second full copy into memory. |
| `main()` | Read one verification artifact, select unsolved problems after exclusions, and overwrite the three inventory outputs. Preserve every parsed diagnostic and report both pre-deduplication and occurrence counts; reject invalid IDs or an output path that aliases an input. |

### scripts/error_taxonomy.py

| Function | Purpose |
|---|---|
| `matches()` | Return whether a case-insensitive regex matches the diagnostic header. |
| `_fallback_category()` | Classify a raw line without changing it; fail closed if no rule applies. |
| `_classify_head()` | Apply historical header-specific overrides, then the broad regex rules; raise on an unknown diagnostic. |
| `classify_error()` | Map one complete parsed diagnostic to exactly one of CATEGORY_ORDER. |

### scripts/error_templates.py

| Function | Purpose |
|---|---|
| `lower_initial()` | Normalize surrounding whitespace, quote style and initial case for a template; leave the raw message untouched. |
| `replace_quoted()` | Replace quoted identifier payloads with a placeholder, handling identifier-final primes and word apostrophes. |
| `replace_dynamic()` | Parameterize quoted values, metavariables and numeric indices; collapse whitespace in a template only. |
| `syntax_template()` | Return a syntax-error template retaining expected-token structure while masking concrete tokens. |
| `name_template()` | Return a name-resolution template with referenced identifiers and fields replaced by ID. |
| `type_template()` | Return a type-checking template preserving the failure wording while masking concrete term payloads. |
| `instance_template()` | Return a typeclass-failure template with concrete instance payloads replaced by TYPE. |
| `tactic_suffix_template()` | Normalize a tactic diagnostic suffix while retaining the specific kind of tactic failure. |
| `tactic_template()` | Return a tactic-error template preserving meaningful failure suffixes and masking variable payloads. |
| `resource_template()` | Return a resource-limit template with concrete locations and numeric limits parameterized. |
| `aggregate_template()` | Dispatch a diagnostic header to its category-specific deterministic template function. |
| `compiler_template()` | Return the historical compiler-shaped template for a full diagnostic. |

### scripts/summarize_errors.py

| Function | Purpose |
|---|---|
| `parse_args()` | Read the scan root, table destination, counting unit and Top50 policy from the CLI. |
| `percentage()` | Format a percentage with six decimals, or return blank when its denominator is zero. |
| `write_csv()` | Write a UTF-8 CSV with explicit columns, including a header when no data rows exist. |
| `discover_scans()` | Find version-2 scanner summaries; reject missing inventories, duplicate cells and mixed occurrence rules. |
| `read_cell()` | Count complete messages and counted occurrences from a cell's JSONL, checking its summary totals. |
| `select_top50()` | Rank (template, category, count) rows to cumulative >=50%, retaining all cutoff-count ties. |
| `category_rows()` | Return all eight category counts and shares for one cell or pooled model, including zero counts. |
| `build_tables()` | Build audited mappings, template counts, Top50 tables and cell/model category distributions. |
| `main()` | Validate scans and build tables in a temporary directory, publishing outputs only after all cells succeed. |

### scripts/plot_heatmaps.py

| Function | Purpose |
|---|---|
| `_order_key()` | Return a sorting key placing known labels first, then others alphabetically. |
| `read_heatmap_table()` | Validate a category CSV and return labels/percentages ordered by benchmark then model, or by model for pooled counts. |
| `plot_heatmap()` | Render categories vertically with thesis-style blue shading and serif labels, grouping model columns by benchmark when requested; save PNG and PDF. |
| `main()` | Parse CLI arguments, validate both input tables, and save four figures. |
