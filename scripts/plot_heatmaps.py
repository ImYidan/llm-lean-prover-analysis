#!/usr/bin/env python3
"""Render eight-category diagnostic percentages from validated summary CSVs.

Each group must contain all eight categories, with counts summing to its
denominator. Undefined percentages (zero diagnostics) appear as gray NA cells.
"""

import argparse
import csv
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt

from error_taxonomy import CATEGORY_ORDER


MODEL_ORDER = (
    "Goedel-32B",
    "Goedel-8B",
    "DeepSeek-Prover-V2-7B",
    "Kimina-Prover-Distill-8B",
    "Pythagoras-Prover-4B",
)
BENCHMARK_ORDER = ("miniF2F", "ProofNet", "Putnam", "FATE-H", "FATE-M")


def _order_key(value: str, preferred: tuple[str, ...]) -> tuple[int, str]:
    """Return a sorting key placing known labels first, then others alphabetically.

    Inputs are a label and its preferred order; no I/O or mutation occurs.
    """
    return (preferred.index(value) if value in preferred else len(preferred), value)


def read_heatmap_table(
    path: Path, group_columns: tuple[str, ...]
) -> tuple[list[str], list[list[float]]]:
    """Read a category CSV and return ordered row labels and percentage values.

    ``group_columns`` must be ``('model',)`` or ``('model', 'benchmark')``.
    The file must contain one row per category per group, nonnegative integer
    counts, a shared denominator equal to the sum of counts, and matching
    percentages within 0.000001 percentage points. Zero denominators require
    blank or NA percentages and yield NaN values. Percentages are recomputed
    from counts after validation. The input is never modified. Invalid data
    raises ValueError; filesystem and decoding errors propagate to the caller.
    """
    if group_columns not in (("model",), ("model", "benchmark")):
        raise ValueError("group_columns must be model or model and benchmark")
    required = set(group_columns) | {"category", "count", "denominator", "percentage"}
    groups = {}
    with Path(path).open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        if len(fields) != len(set(fields)) or not required.issubset(fields):
            raise ValueError(f"{path}: missing required or duplicate CSV columns")
        for line, row in enumerate(reader, 2):
            context = f"{path}:{line}"
            if None in row or any(row.get(field) is None for field in required):
                raise ValueError(f"{context}: malformed CSV row")
            key = tuple(row[column].strip() for column in group_columns)
            if not all(key):
                raise ValueError(f"{context}: group labels cannot be blank")
            category = row["category"]
            if category not in CATEGORY_ORDER:
                raise ValueError(f"{context}: invalid category {category!r}")
            try:
                count = int(row["count"])
                denominator = int(row["denominator"])
            except ValueError as exc:
                raise ValueError(f"{context}: count and denominator must be integers") from exc
            if count < 0 or denominator < 0 or count > denominator:
                raise ValueError(f"{context}: require 0 <= count <= denominator")
            percentage_text = row["percentage"].strip()
            if denominator == 0:
                if percentage_text not in ("", "NA"):
                    raise ValueError(f"{context}: zero denominator requires blank or NA percentage")
                percentage = math.nan
            else:
                try:
                    stated_percentage = float(percentage_text)
                except ValueError as exc:
                    raise ValueError(f"{context}: percentage must be numeric") from exc
                percentage = count / denominator * 100
                if (not math.isfinite(stated_percentage)
                        or not 0 <= stated_percentage <= 100
                        or not math.isclose(stated_percentage, percentage, rel_tol=0, abs_tol=1e-6)):
                    raise ValueError(f"{context}: percentage disagrees with count / denominator")
            entries = groups.setdefault(key, {})
            if category in entries:
                raise ValueError(f"{context}: duplicate category for group {key!r}")
            entries[category] = (count, denominator, percentage)
    if not groups:
        raise ValueError(f"{path}: table contains no groups")
    for key, entries in groups.items():
        if set(entries) != set(CATEGORY_ORDER):
            raise ValueError(f"{path}: group {key!r} must contain all eight categories")
        denominators = {entry[1] for entry in entries.values()}
        if len(denominators) != 1:
            raise ValueError(f"{path}: inconsistent denominators for group {key!r}")
        if sum(entry[0] for entry in entries.values()) != next(iter(denominators)):
            raise ValueError(f"{path}: category counts do not sum to denominator for {key!r}")
    ordered = sorted(groups, key=lambda key: (
        _order_key(key[0], MODEL_ORDER),
        _order_key(key[1], BENCHMARK_ORDER) if len(key) == 2 else (0, ""),
    ))
    labels = [" / ".join(key) for key in ordered]
    values = [[groups[key][category][2] for category in CATEGORY_ORDER] for key in ordered]
    return labels, values


def plot_heatmap(
    labels: list[str], values: list[list[float]], title: str, output_stem: Path,
    count_unit: str = "occurrence",
) -> tuple[Path, Path]:
    """Save a percentage matrix as PNG and PDF, returning both output paths.

    ``labels`` identifies rows; ``values`` has eight columns in CATEGORY_ORDER
    with finite values from 0 to 100 or NaN for undefined percentages.
    ``count_unit`` is ``occurrence`` (default) or ``diagnostic`` and identifies
    the denominator in the colorbar and NA note. The
    function validates dimensions and range before creating the output parent
    directory. It overwrites files sharing the requested stem, fixes the color
    scale to 0..100, annotates to one decimal place, and shades NaNs gray with
    NA text. Invalid matrix data raises ValueError; save errors propagate.
    Matplotlib figures are closed even if saving fails.
    """
    if count_unit not in ("occurrence", "diagnostic"):
        raise ValueError("count_unit must be occurrence or diagnostic")
    unit_label = "error occurrences" if count_unit == "occurrence" else "error diagnostics"
    if not labels or len(labels) != len(values):
        raise ValueError("heatmap requires nonempty labels and one matrix row per label")
    if any(len(row) != len(CATEGORY_ORDER) for row in values):
        raise ValueError("heatmap requires eight category columns")
    if any(not math.isnan(value) and (not math.isfinite(value) or not 0 <= value <= 100)
           for row in values for value in row):
        raise ValueError("heatmap values must be percentages or NaN")
    output_stem = Path(output_stem)
    output_stem.parent.mkdir(parents=True, exist_ok=True)
    paths = (output_stem.with_suffix(".png"), output_stem.with_suffix(".pdf"))
    cmap = plt.get_cmap("Blues").with_extremes(bad="#d9d9d9")
    figure, axes = plt.subplots(figsize=(13, max(4.5, 0.39 * len(labels) + 2.4)))
    try:
        heatmap = axes.imshow(values, cmap=cmap, vmin=0, vmax=100, aspect="auto")
        axes.set_xticks(range(len(CATEGORY_ORDER)),
                        [category.replace(" ", "\n", 1) for category in CATEGORY_ORDER],
                        fontsize=10)
        axes.set_yticks(range(len(labels)), labels, fontsize=10)
        axes.tick_params(axis="both", length=0, pad=7)
        axes.set_title(title, fontsize=14, pad=16)
        axes.set_xticks([index - 0.5 for index in range(len(CATEGORY_ORDER) + 1)], minor=True)
        axes.set_yticks([index - 0.5 for index in range(len(labels) + 1)], minor=True)
        axes.grid(which="minor", color="white", linewidth=0.7)
        axes.tick_params(which="minor", bottom=False, left=False)
        for row_index, row in enumerate(values):
            for column_index, value in enumerate(row):
                axes.text(column_index, row_index, "NA" if math.isnan(value) else f"{value:.1f}",
                          ha="center", va="center", fontsize=9,
                          color="white" if not math.isnan(value) and value >= 55 else "#202020")
        colorbar = figure.colorbar(heatmap, ax=axes, fraction=0.035, pad=0.025)
        colorbar.set_label(f"Share of {unit_label} (%)", fontsize=10)
        colorbar.set_ticks([0, 20, 40, 60, 80, 100])
        figure.text(0.99, 0.01, f"NA: no {unit_label} (denominator = 0)",
                    ha="right", fontsize=9, color="#555555")
        figure.tight_layout(rect=(0, 0.03, 1, 1))
        for path in paths:
            figure.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")
    finally:
        plt.close(figure)
    return paths


def main(argv: list[str] | None = None) -> int:
    """Parse CLI arguments, validate both input tables, and save four figures.

    ``argv`` is an optional argument list, defaulting to the process arguments.
    Required flags are --input-dir and --output-dir. The input directory must
    contain both category CSVs and analysis_summary.json with count_unit set
    to occurrence or diagnostic. Metadata and both CSVs are validated before
    any figure is written. Returns zero on success; argparse exits with
    status two for invalid arguments, table data, or filesystem errors. Existing
    figure filenames are overwritten, and input tables are read without edits.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True,
                        help="Directory containing categories_by_cell.csv, categories_by_model.csv, "
                             "and analysis_summary.json with count_unit metadata")
    parser.add_argument("--output-dir", type=Path, required=True,
                        help="Directory for PNG and PDF figures")
    args = parser.parse_args(argv)
    try:
        metadata_path = args.input_dir / "analysis_summary.json"
        with metadata_path.open(encoding="utf-8") as handle:
            metadata = json.load(handle)
        if not isinstance(metadata, dict) or metadata.get("count_unit") not in ("occurrence", "diagnostic"):
            raise ValueError(f"{metadata_path}: count_unit must be occurrence or diagnostic")
        count_unit = metadata["count_unit"]
        cell = read_heatmap_table(args.input_dir / "categories_by_cell.csv", ("model", "benchmark"))
        model = read_heatmap_table(args.input_dir / "categories_by_model.csv", ("model",))
        plot_heatmap(*cell, "Diagnostic categories by model and benchmark",
                     args.output_dir / "category_heatmap_by_cell", count_unit=count_unit)
        plot_heatmap(*model, "Diagnostic categories by model (pooled counts)",
                     args.output_dir / "category_heatmap_by_model", count_unit=count_unit)
    except (OSError, UnicodeError, ValueError, csv.Error) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
