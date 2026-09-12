#!/usr/bin/env python3
"""Inventory raw Lean errors from candidates of problems unsolved in a Pass@32 run.

Keep all parsed error messages in JSONL. Count verbatim diagnostic first lines
without assigning categories or normalizing identifiers. The default frequency
unit is one (sample, source line, source column, message head) occurrence.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

INPUT_FORMATS = ("standard-json", "kimina-jsonl", "pythagoras-minif2f-json", "pythagoras-jsonl")
POSITIONED_MESSAGE = re.compile(r"(?:^| \|\| )\[(\d+):(\d+)\]\s*")
PYTHAGORAS_DIAGNOSTIC = re.compile(r"(?m)^[^\n]*?\.lean:(\d+):(\d+): (error|warning): ")
NON_COMPILER_ERROR_TYPES = {
    "generation_truncated_before_final_lean", "no_theorem_header_before_cutoff",
    "timeout", "uses_sorry",
}


def problem_id(sample_name: str) -> str:
    """Remove the final generation suffix, e.g. ``_g17``."""
    stem, separator, generation = sample_name.rpartition("_g")
    if separator and generation.isdigit():
        return stem
    return sample_name


def is_pass(sample: dict[str, Any]) -> bool:
    result = sample.get("compilation_result") or {}
    return bool(result.get("pass")) and bool(result.get("complete")) and not bool(
        result.get("sorries")
    )


def load_excluded_problems(path: Path | None) -> set[str]:
    if path is None:
        return set()
    with path.expanduser().resolve().open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError(f"expected a JSON list of problem names or objects: {path}")

    excluded: set[str] = set()
    for row in data:
        if isinstance(row, str):
            excluded.add(row)
        elif isinstance(row, dict):
            name = row.get("name") or row.get("problem_id")
            if not isinstance(name, str) or not name:
                raise ValueError(f"excluded-problem object has no name/problem_id: {row}")
            excluded.add(name)
        else:
            raise ValueError(f"invalid excluded-problem entry: {row!r}")
    return excluded


def load_input(path: Path, input_format: str) -> list[dict[str, Any]]:
    if input_format in {"standard-json", "pythagoras-minif2f-json"}:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list) or not all(isinstance(row, dict) for row in data):
            raise ValueError(f"expected a JSON list of objects: {path}")
        if input_format == "pythagoras-minif2f-json":
            expanded: list[dict[str, Any]] = []
            for source_index, problem in enumerate(data):
                name = problem.get("name")
                sample_count = problem.get("num_samples", problem.get("n", 32))
                if not isinstance(name, str) or not name or not isinstance(sample_count, int):
                    raise ValueError(f"invalid Pythagoras miniF2F row: {problem!r}")
                for sample_index in range(1, sample_count + 1):
                    result = problem.get(f"proof_verification_result_{sample_index}")
                    if not isinstance(result, dict):
                        raise ValueError(
                            f"missing proof_verification_result_{sample_index} for {name}"
                        )
                    expanded.append(
                        {
                            "name": f"{name}_g{sample_index}",
                            "compilation_result": result,
                            "_source_record_index": source_index,
                        }
                    )
            return expanded
        return data

    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"expected object at {path}:{line_number}")
            rows.append(row)
    return rows


def row_problem(row: dict[str, Any], input_format: str) -> str:
    if input_format == "kimina-jsonl":
        return str(row.get("name", ""))
    if input_format == "pythagoras-jsonl":
        return str(row.get("problem_id", ""))
    return problem_id(str(row.get("name", "")))


def row_sample(row: dict[str, Any], input_format: str) -> str:
    if input_format == "kimina-jsonl":
        return str(row.get("problem_id", ""))
    if input_format == "pythagoras-jsonl":
        return f"{row.get('problem_id', '')}_g{row.get('sample_idx', '')}"
    return str(row.get("name", ""))


def row_success(row: dict[str, Any], input_format: str) -> bool:
    if input_format in {"kimina-jsonl", "pythagoras-jsonl"}:
        return str(row.get("success")).lower() == "true"
    return is_pass(row)


def message_head(message: str) -> str:
    """The verbatim first line of a Lean diagnostic — the project's raw error unit."""
    lines = message.splitlines()
    return lines[0] if lines else ""


def standard_diagnostics(row: dict[str, Any]) -> Iterable[tuple[int | None, int | None, str]]:
    result = row.get("compilation_result") or {}
    for diagnostic in result.get("errors", []):
        if not (
            isinstance(diagnostic, dict)
            and diagnostic.get("severity") == "error"
            and isinstance(diagnostic.get("data"), str)
        ):
            continue
        position = diagnostic.get("pos") or {}
        line = position.get("line") if isinstance(position.get("line"), int) else None
        column = position.get("column") if isinstance(position.get("column"), int) else None
        yield line, column, diagnostic["data"]


def kimina_diagnostics(row: dict[str, Any]) -> Iterable[tuple[int | None, int | None, str]]:
    if row.get("error_type") in NON_COMPILER_ERROR_TYPES:
        return
    error = row.get("error")
    if not isinstance(error, str) or not error:
        return
    matches = list(POSITIONED_MESSAGE.finditer(error))
    if not matches:
        yield None, None, error
        return
    for index, found in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(error)
        yield int(found.group(1)), int(found.group(2)), error[found.end():end]


def pythagoras_diagnostics(
    row: dict[str, Any],
) -> Iterable[tuple[int | None, int | None, str]]:
    """Extract only Lean errors from Pythagoras CLI output.

    The JSONL mixes compiler diagnostics with non-compiler sentinels such as
    ``no_proof_extracted``, ``contains_sorry``, ``statement_not_verbatim``,
    timeout/OOM outcomes, warning-only output, and verifier panics.  Positioned
    ``error:`` records are authoritative.  A handful of Linarith failures omit
    the filename/position prefix and are retained as genuine Lean errors.
    """
    error = row.get("error")
    if not isinstance(error, str) or not error:
        return
    matches = list(PYTHAGORAS_DIAGNOSTIC.finditer(error))
    if matches:
        for index, found in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(error)
            if found.group(3) == "error":
                message = error[found.end():end]
                # These JSONL artifacts cap CLI output at exactly 2,000
                # characters.  If the cap lands inside the final diagnostic's
                # first line, fragments such as ``unknow`` or ``unsolv`` are
                # extraction artifacts, not native Lean message heads.
                if index == len(matches) - 1 and len(error) == 2000 and "\n" not in message:
                    continue
                yield int(found.group(1)), int(found.group(2)), message
        return
    if error.startswith("Error in Linarith.") or error.startswith("Error in Linarith"):
        yield None, None, error


def pythagoras_truncated_final_diagnostic(row: dict[str, Any]) -> int:
    """Return 1 when the 2,000-character CLI cap cuts a final error head."""
    error = row.get("error")
    if not isinstance(error, str) or len(error) != 2000:
        return 0
    matches = list(PYTHAGORAS_DIAGNOSTIC.finditer(error))
    if not matches or matches[-1].group(3) != "error":
        return 0
    return int("\n" not in error[matches[-1].end():])


def diagnostics_for_format(input_format: str):
    if input_format in {"standard-json", "pythagoras-minif2f-json"}:
        return standard_diagnostics
    if input_format == "kimina-jsonl":
        return kimina_diagnostics
    if input_format == "pythagoras-jsonl":
        return pythagoras_diagnostics
    raise ValueError(f"unsupported input format: {input_format}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--input-format', choices=INPUT_FORMATS, required=True)
    parser.add_argument('--model', required=True)
    parser.add_argument('--benchmark', required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--exclude-problems', type=Path)
    parser.add_argument('--allow-missing-exclusions', action='store_true')
    parser.add_argument('--count-rule', choices=('per-sample-position', 'raw'),
                        default='per-sample-position',
                        help='Frequency counts: deduplicate heads at each sample position, or count every diagnostic.')
    return parser.parse_args()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    args = parse_args()
    source = args.input.expanduser().resolve()
    out = args.output_dir.expanduser().resolve()
    exclusions_path = args.exclude_problems.expanduser().resolve() if args.exclude_problems else None
    for name in ('raw_errors.jsonl', 'raw_error_counts.csv', 'summary.json'):
        if (out / name).resolve() in {source, exclusions_path}:
            raise ValueError('output would overwrite an input file')
    rows = load_input(source, args.input_format)
    indexed = list(enumerate(rows))
    for _, row in indexed:
        if not row_problem(row, args.input_format) or not row_sample(row, args.input_format):
            raise ValueError('each candidate must have a problem ID and sample ID')
    input_problems = {row_problem(row, args.input_format) for row in rows}
    requested = load_excluded_problems(exclusions_path)
    missing = requested - input_problems
    if missing and not args.allow_missing_exclusions:
        raise ValueError(f'{len(missing)} excluded problems are absent from the input')
    excluded = requested & input_problems
    eligible = [(i, r) for i, r in indexed if row_problem(r, args.input_format) not in excluded]
    all_problems = {row_problem(r, args.input_format) for _, r in eligible}
    solved = {row_problem(r, args.input_format) for _, r in eligible if row_success(r, args.input_format)}
    scope = all_problems - solved
    selected = [(i, r) for i, r in eligible if row_problem(r, args.input_format) in scope]
    parser = diagnostics_for_format(args.input_format)
    counts: Counter[str] = Counter()
    samples_with_error = raw_total = missing_position = truncated = 0
    out.mkdir(parents=True, exist_ok=True)
    with (out / 'raw_errors.jsonl').open('w', encoding='utf-8') as handle:
        for source_index, row in selected:
            diagnostics = list(parser(row))
            samples_with_error += bool(diagnostics)
            if args.input_format == 'pythagoras-jsonl':
                truncated += pythagoras_truncated_final_diagnostic(row)
            seen: set[tuple[int | None, int | None, str]] = set()
            for diagnostic_index, (line, column, message) in enumerate(diagnostics):
                raw_total += 1
                head = message_head(message)
                key = (line, column, head)
                counted = args.count_rule == 'raw' or key not in seen
                seen.add(key)
                if counted:
                    counts[head] += 1
                    missing_position += line is None or column is None
                record = {
                    'source_record_index': row.get('_source_record_index', source_index)
                        if args.input_format == 'pythagoras-minif2f-json' else source_index,
                    'problem_id': row_problem(row, args.input_format),
                    'sample_id': row_sample(row, args.input_format),
                    'diagnostic_index': diagnostic_index,
                    'line': line, 'column': column,
                    'message': message, 'raw_error_head': head, 'counted': counted,
                }
                handle.write(json.dumps(record, ensure_ascii=False) + '\n')
    total = sum(counts.values())
    with (out / 'raw_error_counts.csv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(('rank', 'count', 'ratio', 'raw_error_head'))
        for rank, (head, count) in enumerate(sorted(counts.items(), key=lambda item: (-item[1], item[0])), 1):
            writer.writerow((rank, count, f'{100 * count / total:.6f}', head))
    summary = {
        'model': args.model, 'benchmark': args.benchmark,
        'input_file': source.name, 'input_sha256': file_sha256(source),
        'input_format': args.input_format, 'scope': 'unsolved-problems-in-input',
        'exclusion_file': exclusions_path.name if exclusions_path else None,
        'exclusion_sha256': file_sha256(exclusions_path) if exclusions_path else None,
        'requested_exclusions': len(requested), 'applied_exclusions': len(excluded),
        'missing_exclusions_allowed': len(missing),
        'total_samples_in_input': len(rows), 'total_problems_in_input': len(input_problems),
        'problems_after_exclusions': len(all_problems), 'problems_solved_in_input': len(solved),
        'problems_in_scope': len(scope), 'samples_in_scope': len(selected),
        'samples_with_compiler_error': samples_with_error,
        'samples_without_compiler_error': len(selected) - samples_with_error,
        'count_rule': args.count_rule, 'raw_diagnostics_before_rule': raw_total,
        'counted_error_occurrences': total, 'distinct_raw_error_heads': len(counts),
        'diagnostics_without_position': missing_position,
        'truncated_final_diagnostics_excluded': truncated,
    }
    (out / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
