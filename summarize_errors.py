#!/usr/bin/env python3
"""Map complete diagnostic inventories, aggregate templates and build eight-category tables."""
from __future__ import annotations

import argparse
import csv
import json
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from error_taxonomy import CATEGORY_ORDER, classify_error
from error_templates import compiler_template


def parse_args() -> argparse.Namespace:
    """Read the scan root, table destination, counting unit and Top50 policy from the CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--count-unit', choices=('occurrence', 'diagnostic'), default='occurrence',
                        help='Use historical counted occurrences, or every parsed diagnostic.')
    parser.add_argument('--top50-policy', choices=('historical', 'all'), default='historical',
                        help='Historical excludes Resource exhaustion and no goals to be solved from Top50 only.')
    return parser.parse_args()


def percentage(count: int, denominator: int) -> str:
    """Format a percentage with six decimals, or return blank when its denominator is zero."""
    return f'{100.0 * count / denominator:.6f}' if denominator else ''


def write_csv(path: Path, fields: list[str], rows: Iterable[dict[str, Any]]) -> None:
    """Write a UTF-8 CSV with explicit columns, including a header when no data rows exist."""
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def discover_scans(root: Path) -> list[tuple[Path, dict[str, Any]]]:
    """Find version-2 scanner summaries; reject missing inventories, duplicate cells and mixed occurrence rules.

    Return (summary path, metadata) pairs ordered by model and benchmark.
    A directory with no scanner summaries is an error, not an empty study.
    """
    scans = []
    seen = set()
    rules = set()
    for path in sorted(root.rglob('summary.json')):
        meta = json.loads(path.read_text(encoding='utf-8'))
        if meta.get('schema_version') != 2:
            raise ValueError(f'expected schema_version 2 scanner summary: {path}')
        for field in ('model', 'benchmark'):
            if not isinstance(meta.get(field), str) or not meta[field].strip():
                raise ValueError(f'missing {field}: {path}')
        cell = (meta['model'], meta['benchmark'])
        if cell in seen:
            raise ValueError(f'duplicate model/benchmark scan: {cell}')
        seen.add(cell)
        if meta.get('count_rule') not in {'per-sample-position', 'raw'}:
            raise ValueError(f'unknown occurrence rule: {path}')
        rules.add(meta['count_rule'])
        if not (path.parent/'raw_errors.jsonl').is_file():
            raise ValueError(f'missing raw_errors.jsonl beside {path}')
        scans.append((path, meta))
    if not scans:
        raise ValueError(f'no scanner summary.json files under {root}')
    if len(rules) != 1:
        raise ValueError('mixed scanner counting rules; rescan cells with a common --count-rule')
    return sorted(scans, key=lambda item: (item[1]['model'], item[1]['benchmark']))


def read_cell(path: Path, meta: dict[str, Any]) -> tuple[Counter[str], Counter[str]]:
    """Count complete messages and counted occurrences from a cell's JSONL, checking its summary totals.

    The two returned Counters retain complete message strings as keys.
    Invalid diagnostic records and incomplete inventories raise ValueError.
    """
    diagnostics: Counter[str] = Counter()
    occurrences: Counter[str] = Counter()
    with (path.parent/'raw_errors.jsonl').open(encoding='utf-8') as handle:
        for number, line in enumerate(handle, 1):
            record = json.loads(line)
            if not isinstance(record.get('message'), str) or not isinstance(record.get('counted'), bool):
                raise ValueError(f'invalid message/counted fields at {path.parent}:{number}')
            diagnostics[record['message']] += 1
            if record['counted']:
                occurrences[record['message']] += 1
    checks = {
        'raw_diagnostics_before_rule': sum(diagnostics.values()),
        'counted_error_occurrences': sum(occurrences.values()),
        'distinct_raw_messages': len(diagnostics),
    }
    for field, actual in checks.items():
        if meta.get(field) != actual:
            raise ValueError(f'{path}: {field} mismatch: summary={meta.get(field)}, inventory={actual}')
    if meta['samples_with_compiler_error'] + meta['samples_without_compiler_error'] != meta['samples_in_scope']:
        raise ValueError(f'{path}: candidate denominator mismatch')
    return diagnostics, occurrences


def select_top50(rows: list[tuple[str, str, int]]) -> tuple[list[tuple[str, str, int]], int, int]:
    """Rank (template, category, count) rows to cumulative >=50%, retaining all cutoff-count ties.

    Return selected rows, eligible denominator and cutoff count. Input rows
    must already reflect the chosen exclusion policy; a zero total yields
    ([], 0, 0). This selects a coverage prefix, not a fixed 50 templates.
    """
    if any(count < 0 for _, _, count in rows):
        raise ValueError('negative template count')
    ranked = sorted((row for row in rows if row[2]), key=lambda row: (-row[2], row[0], row[1]))
    total = sum(count for _, _, count in ranked)
    if not total:
        return [], 0, 0
    running = 0
    cutoff = 0
    for _, _, count in ranked:
        running += count
        cutoff = count
        if 2 * running >= total:
            break
    return [row for row in ranked if row[2] >= cutoff], total, cutoff


def category_rows(counts: Counter[str], identity: dict[str, str]) -> list[dict[str, Any]]:
    """Return all eight category counts and shares for one cell or pooled model, including zero counts."""
    total = sum(counts.values())
    if any(category not in CATEGORY_ORDER for category in counts):
        raise ValueError('category outside the fixed eight-category taxonomy')
    return [dict(identity, category=category, count=counts[category], denominator=total,
                 percentage=percentage(counts[category], total)) for category in CATEGORY_ORDER]


def build_tables(scans: list[tuple[Path, dict[str, Any]]], out: Path,
                 count_unit: str, top50_policy: str) -> dict[str, Any]:
    """Build audited mappings, template counts, Top50 tables and cell/model category distributions.

    Process one cell's complete messages at a time. Category tables keep all
    eight categories; only Top50 uses the separate exclusion policy. Model
    shares divide pooled counts by pooled totals, not by mean benchmark shares.
    Write tables under out and return metadata for analysis_summary.json.
    """
    if count_unit not in {'occurrence', 'diagnostic'} or top50_policy not in {'historical', 'all'}:
        raise ValueError('unsupported count unit or Top50 policy')
    templates_out = []
    top_out = []
    top_summary = []
    cells_out = []
    models: dict[str, Counter[str]] = {}
    source_summaries = []
    total_diagnostics = total_occurrences = total_chosen = 0
    map_fields = ['model', 'benchmark', 'category', 'template', 'diagnostic_count',
                  'occurrence_count', 'count', 'raw_error_message']
    with (out/'mapped_errors.csv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=map_fields)
        writer.writeheader()
        for path, meta in scans:
            identity = {'model': meta['model'], 'benchmark': meta['benchmark']}
            diagnostics, occurrences = read_cell(path, meta)
            selected_counts = occurrences if count_unit == 'occurrence' else diagnostics
            template_counts: Counter[tuple[str, str]] = Counter()
            categories: Counter[str] = Counter()
            for message in sorted(diagnostics):
                try:
                    category = classify_error(message)
                    template = compiler_template(category, message)
                except (ValueError, TypeError) as exc:
                    raise ValueError(f"unmapped diagnostic in {identity}: {message[:180]!r}") from exc
                count = selected_counts[message]
                writer.writerow(dict(identity, category=category, template=template,
                                     diagnostic_count=diagnostics[message], occurrence_count=occurrences[message],
                                     count=count, raw_error_message=message))
                template_counts[(category, template)] += count
                categories[category] += count
            total = sum(selected_counts.values())
            if sum(categories.values()) != total or sum(template_counts.values()) != total:
                raise AssertionError(f'category/template conservation failure: {identity}')
            cells_out.extend(category_rows(categories, identity))
            models.setdefault(meta['model'], Counter()).update(categories)
            total_diagnostics += sum(diagnostics.values())
            total_occurrences += sum(occurrences.values())
            total_chosen += total
            eligible = []
            excluded_resource = excluded_no_goals = 0
            for (category, template), count in sorted(template_counts.items(), key=lambda item: (-item[1], item[0])):
                if not count:
                    continue
                templates_out.append(dict(identity, category=category, template=template, count=count,
                                          denominator=total, percentage=percentage(count, total)))
                if top50_policy == 'historical' and category == 'Resource exhaustion':
                    excluded_resource += count
                elif top50_policy == 'historical' and template == 'no goals to be solved':
                    excluded_no_goals += count
                else:
                    eligible.append((template, category, count))
            chosen, denominator, cutoff = select_top50(eligible)
            cumulative = 0
            for rank, (template, category, count) in enumerate(chosen, 1):
                cumulative += count
                top_out.append(dict(identity, rank=rank, category=category, template=template, count=count,
                                    denominator=denominator, percentage=percentage(count, denominator),
                                    cumulative_count=cumulative, cumulative_percentage=percentage(cumulative, denominator),
                                    cutoff_count=cutoff))
            if denominator + excluded_resource + excluded_no_goals != total:
                raise AssertionError(f'Top50 denominator mismatch: {identity}')
            top_summary.append(dict(identity, original_count=total, excluded_resource_count=excluded_resource,
                                    excluded_no_goals_count=excluded_no_goals, eligible_denominator=denominator,
                                    selected_template_count=len(chosen), selected_count=cumulative,
                                    coverage_percentage=percentage(cumulative, denominator), cutoff_count=cutoff))
            source_summaries.append(meta)
    write_csv(out/'template_counts.csv', ['model','benchmark','category','template','count','denominator','percentage'], templates_out)
    write_csv(out/'top50_errors.csv', ['model','benchmark','rank','category','template','count','denominator','percentage',
                                      'cumulative_count','cumulative_percentage','cutoff_count'], top_out)
    write_csv(out/'top50_summary.csv', ['model','benchmark','original_count','excluded_resource_count','excluded_no_goals_count',
                                      'eligible_denominator','selected_template_count','selected_count','coverage_percentage','cutoff_count'], top_summary)
    write_csv(out/'categories_by_cell.csv', ['model','benchmark','category','count','denominator','percentage'], cells_out)
    pooled = [row for model, counts in sorted(models.items()) for row in category_rows(counts, {'model':model})]
    write_csv(out/'categories_by_model.csv', ['model','category','count','denominator','percentage'], pooled)
    return {'schema_version': 1, 'count_unit': count_unit, 'scan_count_rule': scans[0][1]['count_rule'],
            'top50_policy': top50_policy, 'top50_target_share': 0.5, 'top50_cutoff_ties': 'included',
            'cell_count':len(scans), 'model_count':len(models), 'raw_diagnostic_count':total_diagnostics,
            'occurrence_count':total_occurrences, 'analysis_count':total_chosen, 'categories':list(CATEGORY_ORDER),
            'scans': source_summaries}


def main() -> None:
    """Validate scans and build tables in a temporary directory, publishing outputs only after all cells succeed."""
    args = parse_args()
    root = args.input_dir.expanduser().resolve()
    out = args.output_dir.expanduser().resolve()
    scans = discover_scans(root)
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.error-tables-', dir=out.parent) as temp:
        stage = Path(temp)
        summary = build_tables(scans, stage, args.count_unit, args.top50_policy)
        (stage/'analysis_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        out.mkdir(parents=True, exist_ok=True)
        for path in sorted(stage.iterdir(), key=lambda p: p.name == 'analysis_summary.json'):
            path.replace(out/path.name)
    print(f"Wrote {summary['cell_count']} cells / {summary['model_count']} models using {summary['analysis_count']} {args.count_unit}s to {out}")


if __name__ == '__main__':
    main()
