#!/usr/bin/env python3
"""Create an intelligent, standard-library-only analytical profile of a CSV/TSV/DSV file."""
from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

# Common date format patterns
DATE_FORMATS = [
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%m/%d/%Y",
    "%d/%m/%Y",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%m-%d-%Y",
    "%d-%m-%Y",
]

CLEAN_NUM_REGEX = re.compile(r"^[\$€£]?\s*([+-]?\d+(?:,\d{3})*(?:\.\d+)?|\.\d+)\s*[%]?$")


def detect_dialect(path: Path) -> csv.Dialect | type[csv.Dialect]:
    """Detect delimiter and quote char from file sample, falling back safely."""
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            sample = f.read(8192)
            if not sample.strip():
                return csv.excel
            sniffer = csv.Sniffer()
            # Test common delimiters: , ; \t |
            return sniffer.sniff(sample, delimiters=",;\t|")
    except Exception:
        return csv.excel


def parse_typed_value(raw: str) -> tuple[str, Any]:
    """Infer type and parse value: integer, float, date, boolean, or string."""
    cleaned = raw.strip()
    if not cleaned:
        return ("empty", None)

    # Boolean check
    lowered = cleaned.lower()
    if lowered in {"true", "false", "yes", "no"}:
        return ("boolean", lowered in {"true", "yes"})

    # Numeric check (handling currency symbols and thousands commas)
    num_match = CLEAN_NUM_REGEX.match(cleaned)
    if num_match:
        raw_num = num_match.group(1).replace(",", "")
        try:
            if "." in raw_num:
                return ("float", float(raw_num))
            return ("integer", int(raw_num))
        except ValueError:
            pass

    # Date check
    if len(cleaned) in {8, 9, 10, 19}:
        for fmt in DATE_FORMATS:
            try:
                dt = datetime.strptime(cleaned, fmt)
                return ("date", dt)
            except ValueError:
                continue

    return ("string", cleaned)


def profile_csv(path: Path) -> dict[str, Any]:
    """Generate a comprehensive statistical profile of a delimited data file."""
    dialect = detect_dialect(path)
    delimiter = getattr(dialect, "delimiter", ",")

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, dialect=dialect)
        columns = [col for col in (reader.fieldnames or []) if col is not None]

        row_count = 0
        duplicate_rows = 0
        seen_row_hashes = set()

        missing = Counter()
        type_counts: dict[str, Counter] = {col: Counter() for col in columns}
        numeric_values: dict[str, list[float]] = {col: [] for col in columns}
        date_values: dict[str, list[datetime]] = {col: [] for col in columns}
        string_lengths: dict[str, list[int]] = {col: [] for col in columns}
        distinct: dict[str, set[str]] = {col: set() for col in columns}
        examples: dict[str, list[str]] = {col: [] for col in columns}

        for row in reader:
            row_count += 1

            # Duplicate row tracking via hash
            row_tuple = tuple(row.get(col, "") for col in columns)
            row_hash = hash(row_tuple)
            if row_hash in seen_row_hashes:
                duplicate_rows += 1
            else:
                if len(seen_row_hashes) < 50000:
                    seen_row_hashes.add(row_hash)

            for col in columns:
                raw_val = (row.get(col) or "").strip()
                if not raw_val:
                    missing[col] += 1
                    continue

                if len(distinct[col]) < 10000:
                    distinct[col].add(raw_val)
                if len(examples[col]) < 3 and raw_val not in examples[col]:
                    examples[col].append(raw_val)

                vtype, parsed = parse_typed_value(raw_val)
                type_counts[col][vtype] += 1

                if vtype in {"integer", "float"}:
                    numeric_values[col].append(float(parsed))
                elif vtype == "date":
                    date_values[col].append(parsed)
                elif vtype == "string":
                    string_lengths[col].append(len(raw_val))

    # Compile column-level summaries
    column_profiles = []
    for col in columns:
        present_count = row_count - missing[col]
        # Inferred primary type
        dominant_type = (
            type_counts[col].most_common(1)[0][0] if type_counts[col] else "empty"
        )

        col_data: dict[str, Any] = {
            "name": col,
            "inferred_type": dominant_type,
            "missing_count": missing[col],
            "missing_percent": round(
                (missing[col] / row_count * 100) if row_count else 0.0, 2
            ),
            "distinct_values_seen_up_to_10000": len(distinct[col]),
            "examples": examples[col],
        }

        # Calculate numeric statistics
        nums = numeric_values[col]
        if nums and len(nums) >= (present_count * 0.7):
            col_data["statistics"] = {
                "count": len(nums),
                "min": min(nums),
                "max": max(nums),
                "mean": round(statistics.mean(nums), 3),
                "median": round(statistics.median(nums), 3),
                "sum": round(sum(nums), 3),
                "zero_count": sum(1 for n in nums if n == 0.0),
            }
            if len(nums) > 1:
                col_data["statistics"]["std_dev"] = round(statistics.stdev(nums), 3)

        # Calculate date span
        dates = date_values[col]
        if dates and len(dates) >= (present_count * 0.7):
            dates.sort()
            col_data["temporal_span"] = {
                "earliest": dates[0].strftime("%Y-%m-%d %H:%M:%S").replace(" 00:00:00", ""),
                "latest": dates[-1].strftime("%Y-%m-%d %H:%M:%S").replace(" 00:00:00", ""),
                "timespan_days": (dates[-1] - dates[0]).days,
            }

        # Calculate text length stats
        str_lens = string_lengths[col]
        if str_lens and dominant_type == "string":
            col_data["text_metrics"] = {
                "min_length": min(str_lens),
                "max_length": max(str_lens),
                "avg_length": round(statistics.mean(str_lens), 1),
            }

        column_profiles.append(col_data)

    return {
        "file": path.name,
        "format": {
            "detected_delimiter": delimiter,
            "row_count": row_count,
            "column_count": len(columns),
            "duplicate_rows_estimated": duplicate_rows,
        },
        "columns": column_profiles,
        "notes": [
            "Distinct-value counts are capped at 10,000 unique values per column.",
            "Numeric calculations sanitize standard currency symbols ($ € £) and thousands separators.",
            "Type inference requires >=70% consistent values to assign numeric/temporal metrics.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path, help="Path to input CSV/TSV/DSV file")
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    args = parser.parse_args()

    result = profile_csv(args.csv_file)
    rendered = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
