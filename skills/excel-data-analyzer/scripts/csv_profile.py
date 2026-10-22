#!/usr/bin/env python3
"""Create a lightweight, standard-library-only profile of a CSV file."""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path


def profile_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        row_count = 0
        missing = Counter()
        distinct = {column: set() for column in columns}
        examples = {column: [] for column in columns}

        for row in reader:
            row_count += 1
            for column in columns:
                value = (row.get(column) or "").strip()
                if not value:
                    missing[column] += 1
                    continue
                if len(distinct[column]) < 10000:
                    distinct[column].add(value)
                if len(examples[column]) < 3 and value not in examples[column]:
                    examples[column].append(value)

    return {
        "file": path.name,
        "row_count": row_count,
        "column_count": len(columns),
        "columns": [
            {
                "name": column,
                "missing_count": missing[column],
                "missing_percent": round(
                    (missing[column] / row_count * 100) if row_count else 0, 2
                ),
                "distinct_values_seen_up_to_10000": len(distinct[column]),
                "examples": examples[column],
            }
            for column in columns
        ],
        "notes": [
            "Distinct-value counts are capped at 10,000 unique values per column.",
            "This profile does not infer data types or prove data quality.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path, help="Path to the input CSV file")
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
