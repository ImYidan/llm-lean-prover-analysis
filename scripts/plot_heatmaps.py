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
from matplotlib.colors import LinearSegmentedColormap

from error_taxonomy import CATEGORY_ORDER


MODEL_ORDER = (
    "Goedel-32B",
    "Goedel-8B",
    "DeepSeek-Prover-V2-7B",
    "Kimina-Prover-Distill-8B",
    "Pythagoras-Prover-4B",
)
BENCHMARK_ORDER = ("miniF2F", "ProofNet", "Putnam", "FATE-H", "FATE-M")
MODEL_SHORT = dict(zip(MODEL_ORDER, ("G32", "G8", "DS7", "K8", "P4")))


def _order_key(value: str, preferred: tuple[str, ...]) -> tuple[int, str]:
    """Return a sorting key placing known labels first, then others alphabetically.

    Inputs are a label and its preferred order; no I/O or mutation occurs.
    """
    return (preferred.index(value) if value in preferred else len(preferred), value)


def read_heatmap_table(
    path: Path, group_columns: tuple[str, ...]
) -> tuple[list[str], list[list[float]]]:
    """Read a category CSV and return group labels and eight-category percentages.

    ``group_columns`` must be ``('model',)`` or ``('model', 'benchmark')``.
    The file must contain one row per category per group, nonnegative integer
    counts, a shared denominator equal to the sum of counts, and matching
    percentages within 0.000001 percentage points. Zero denominators require
    blank or NA percentages and yield NaN values. Percentages are recomputed
    from counts after validation. The input is never modified. Invalid data
    raises ValueError; filesystem and decoding errors propagate to the caller.
    Cells sort by benchmark then model; pooled groups sort by model.
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
        _order_key(key[1], BENCHMARK_ORDER) if len(key) == 2 else (0, ""),
        _order_key(key[0], MODEL_ORDER),
    ))
    labels = [" / ".join(key) for key in ordered]
    values = [[groups[key][category][2] for category in CATEGORY_ORDER] for key in ordered]
    return labels, values


def plot_heatmap(
    labels: list[str], values: list[list[float]], title: str, output_stem: Path,
    count_unit: str = "occurrence", group_by_benchmark: bool = False,
    color_max: float = 100,
) -> tuple[Path, Path]:
    """Save a thesis-style category-by-group heatmap as PNG and PDF.

    Input rows in ``values`` correspond to ``labels``; each has eight values
    in CATEGORY_ORDER, from 0 to 100 or NaN. Rendering transposes this matrix
    so categories run vertically and model groups horizontally. For cell
    plots, set ``group_by_benchmark`` and supply contiguous benchmark groups
    labelled ``model / benchmark`` (as returned by read_heatmap_table).
    Benchmark headings and separators mark the groups; pooled plots use
    model abbreviations alone. Unknown model labels are shown in full.

    The muted blue palette, serif labels and compact layout follow the thesis
    presentation. The color scale runs from zero to ``color_max`` (default 100), which must
    cover every finite value. The CLI chooses one shared upper limit for both
    figures, rounding their maximum up to the next ten percentage points.
    The colorbar identifies
    ``count_unit`` as occurrence or diagnostic. Numeric cell annotations are
    omitted; undefined percentages are gray and labelled NA. Dimensions and
    values are checked before output creation. Files sharing the stem are
    overwritten; figures are closed even if saving fails.
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
    if (not math.isfinite(color_max) or not 0 < color_max <= 100
            or any(value > color_max for row in values for value in row if not math.isnan(value))):
        raise ValueError("color_max must cover all finite percentages and be in (0, 100]")
    columns = [label.rsplit(" / ", 1) for label in labels] if group_by_benchmark else [[label] for label in labels]
    if group_by_benchmark and any(len(column) != 2 for column in columns):
        raise ValueError("benchmark plots require model / benchmark labels")
    output_stem = Path(output_stem)
    output_stem.parent.mkdir(parents=True, exist_ok=True)
    paths = (output_stem.with_suffix(".png"), output_stem.with_suffix(".pdf"))
    cmap = LinearSegmentedColormap.from_list(
        "thesis_blues", ["#f7f9fc", "#dbe5f2", "#a3badc", "#4b6fa7"]
    ).with_extremes(bad="#d9d9d9")
    matrix = list(map(list, zip(*values)))
    style = {"font.family": "serif", "font.serif": ["STIXGeneral"],
             "pdf.fonttype": 42, "axes.linewidth": 0.5}
    with plt.rc_context(style):
        width = max(6.2, 2.6 + 0.34 * len(labels))
        figure, axes = plt.subplots(figsize=(width, 4.5))
        try:
            heatmap = axes.imshow(matrix, cmap=cmap, vmin=0, vmax=color_max, aspect="auto")
            axes.set_xticks(range(len(labels)),
                            [MODEL_SHORT.get(column[0], column[0]) for column in columns],
                            rotation=55, ha="right", rotation_mode="anchor", fontsize=9)
            axes.set_yticks(range(len(CATEGORY_ORDER)),
                            ["Termination" if category == "Termination failure" else
                             "Resource" if category == "Resource exhaustion" else category
                             for category in CATEGORY_ORDER], fontsize=11)
            axes.tick_params(axis="both", length=2.5, width=0.4, direction="in", pad=5,
                             top=True, right=True, color="#777777")
            axes.set_title(title, fontsize=12, pad=32 if group_by_benchmark else 14)
            for spine in axes.spines.values():
                spine.set_color("#777777")
            if group_by_benchmark:
                start = 0
                for stop in range(1, len(columns) + 1):
                    if stop == len(columns) or columns[stop][1] != columns[start][1]:
                        benchmark = columns[start][1]
                        axes.text((start + stop - 1) / 2, 1.035,
                                  "PutnamBench" if benchmark == "Putnam" else benchmark,
                                  transform=axes.get_xaxis_transform(), ha="center",
                                  va="bottom", fontsize=10)
                        if stop < len(columns):
                            axes.axvline(stop - 0.5, color="white", linewidth=1.2)
                        start = stop
            for row_index, row in enumerate(matrix):
                for column_index, value in enumerate(row):
                    if math.isnan(value):
                        axes.text(column_index, row_index, "NA", ha="center", va="center",
                                  fontsize=8, color="#555555")
            colorbar = figure.colorbar(heatmap, ax=axes, fraction=0.035, pad=0.025)
            colorbar.set_label(f"Share of {unit_label} (%)", fontsize=10)
            colorbar.set_ticks([*range(0, math.ceil(color_max), 20), color_max])
            colorbar.ax.tick_params(labelsize=9, width=0.4, length=2)
            colorbar.outline.set_edgecolor("#777777")
            figure.text(0.99, 0.015, f"NA: no {unit_label} (denominator = 0)",
                        ha="right", fontsize=8, color="#555555")
            figure.tight_layout(rect=(0, 0.045, 1, 1))
            for path in paths:
                figure.savefig(path, dpi=250, bbox_inches="tight", facecolor="white")
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
        largest = max((value for values in (cell[1], model[1]) for row in values
                       for value in row if math.isfinite(value)), default=0)
        color_max = max(10, math.ceil(largest / 10) * 10)
        plot_heatmap(*cell, "Diagnostic categories by model and benchmark",
                     args.output_dir / "category_heatmap_by_cell", count_unit=count_unit,
                     group_by_benchmark=True, color_max=color_max)
        plot_heatmap(*model, "Diagnostic categories by model (pooled counts)",
                     args.output_dir / "category_heatmap_by_model", count_unit=count_unit,
                     color_max=color_max)
    except (OSError, UnicodeError, ValueError, csv.Error) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
