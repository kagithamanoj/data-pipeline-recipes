"""
CSV Processing Pipeline — Clean, transform, and analyze CSV datasets.

Usage:
    python recipes/csv_processing/csv_pipeline.py --input data.csv --output clean_data.csv
    python recipes/csv_processing/csv_pipeline.py --demo
"""

import csv
import io
import json
import argparse
import statistics
from pathlib import Path
from collections import Counter


def read_csv(filepath: str, encoding: str = "utf-8") -> tuple[list[str], list[dict]]:
    """Read CSV file and return headers + list of row dicts."""
    with open(filepath, "r", encoding=encoding, newline="") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        rows = list(reader)
    return headers, rows


def write_csv(filepath: str, headers: list[str], rows: list[dict], encoding: str = "utf-8"):
    """Write rows to CSV file."""
    with open(filepath, "w", encoding=encoding, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def profile_column(values: list[str], col_name: str) -> dict:
    """Generate statistics for a single column."""
    total = len(values)
    non_empty = [v for v in values if v and v.strip()]
    null_count = total - len(non_empty)

    profile = {
        "column": col_name,
        "total_rows": total,
        "non_null": len(non_empty),
        "null_count": null_count,
        "null_pct": round(null_count / total * 100, 1) if total else 0,
        "unique_count": len(set(non_empty)),
    }

    # Try numeric analysis
    numeric_values = []
    for v in non_empty:
        try:
            numeric_values.append(float(v.replace(",", "")))
        except (ValueError, AttributeError):
            pass

    if numeric_values and len(numeric_values) > len(non_empty) * 0.5:
        profile["type"] = "numeric"
        profile["min"] = min(numeric_values)
        profile["max"] = max(numeric_values)
        profile["mean"] = round(statistics.mean(numeric_values), 2)
        profile["median"] = round(statistics.median(numeric_values), 2)
        if len(numeric_values) > 1:
            profile["stdev"] = round(statistics.stdev(numeric_values), 2)
    else:
        profile["type"] = "categorical"
        counter = Counter(non_empty)
        profile["top_5"] = dict(counter.most_common(5))
        profile["sample"] = non_empty[:3] if non_empty else []

    return profile


def profile_dataset(headers: list[str], rows: list[dict]) -> dict:
    """Generate a full profile of the dataset."""
    print(f"📊 Dataset Profile: {len(rows)} rows × {len(headers)} columns")
    print("─" * 60)

    profiles = {}
    for col in headers:
        values = [row.get(col, "") for row in rows]
        profile = profile_column(values, col)
        profiles[col] = profile

        null_bar = "█" * int(profile["null_pct"] / 5) + "░" * (20 - int(profile["null_pct"] / 5))
        print(f"  {col:20s} | {profile['type']:12s} | null: {null_bar} {profile['null_pct']:5.1f}%")

    return profiles


def clean_dataset(headers: list[str], rows: list[dict], config: dict = None) -> list[dict]:
    """
    Clean a dataset with configurable operations.

    Config options:
        strip_whitespace: bool (default True)
        remove_duplicates: bool (default True)
        fill_nulls: dict[col_name, fill_value]
        drop_columns: list[col_name]
        rename_columns: dict[old_name, new_name]
        filter_rows: dict[col_name, allowed_values]
    """
    config = config or {}
    cleaned = [dict(row) for row in rows]  # Deep copy
    changes = []

    # Strip whitespace
    if config.get("strip_whitespace", True):
        for row in cleaned:
            for k in row:
                if isinstance(row[k], str):
                    row[k] = row[k].strip()
        changes.append("Stripped whitespace from all string values")

    # Remove duplicates
    if config.get("remove_duplicates", True):
        seen = set()
        unique = []
        for row in cleaned:
            key = tuple(sorted(row.items()))
            if key not in seen:
                seen.add(key)
                unique.append(row)
        removed = len(cleaned) - len(unique)
        if removed > 0:
            changes.append(f"Removed {removed} duplicate rows")
        cleaned = unique

    # Fill nulls
    fill_nulls = config.get("fill_nulls", {})
    for col, fill_value in fill_nulls.items():
        count = 0
        for row in cleaned:
            if not row.get(col, "").strip():
                row[col] = str(fill_value)
                count += 1
        if count:
            changes.append(f"Filled {count} nulls in '{col}' with '{fill_value}'")

    # Drop columns
    drop_cols = config.get("drop_columns", [])
    if drop_cols:
        cleaned = [{k: v for k, v in row.items() if k not in drop_cols} for row in cleaned]
        changes.append(f"Dropped columns: {drop_cols}")

    # Rename columns
    rename = config.get("rename_columns", {})
    if rename:
        cleaned = [{rename.get(k, k): v for k, v in row.items()} for row in cleaned]
        changes.append(f"Renamed columns: {rename}")

    print(f"\n🧹 Cleaning complete: {len(changes)} operations")
    for change in changes:
        print(f"  ✅ {change}")

    return cleaned


def aggregate(rows: list[dict], group_by: str, agg_col: str, agg_func: str = "sum") -> list[dict]:
    """Simple group-by aggregation."""
    groups = {}
    for row in rows:
        key = row.get(group_by, "")
        try:
            val = float(row.get(agg_col, 0))
        except (ValueError, TypeError):
            continue
        groups.setdefault(key, []).append(val)

    result = []
    for key, values in sorted(groups.items()):
        agg_value = {
            "sum": sum(values),
            "mean": statistics.mean(values),
            "count": len(values),
            "min": min(values),
            "max": max(values),
        }.get(agg_func, sum(values))

        result.append({group_by: key, f"{agg_func}_{agg_col}": round(agg_value, 2), "count": len(values)})

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CSV Processing Pipeline")
    parser.add_argument("--input", "-i", type=str, help="Input CSV file")
    parser.add_argument("--output", "-o", type=str, help="Output CSV file")
    parser.add_argument("--demo", action="store_true", help="Run demo")
    args = parser.parse_args()

    if args.demo or not args.input:
        print("📋 CSV Processing Pipeline — Demo")
        print("=" * 50)

        # Generate sample data
        sample_csv = """name,department,salary,city,start_date
John Smith,Engineering,95000,San Francisco,2022-03-15
Sarah Johnson,Marketing,82000,New York,2021-06-01
Michael Chen,Engineering,105000,San Francisco,2020-11-20
Emily Davis,Marketing,78000,New York,2023-01-10
John Smith,Engineering,95000,San Francisco,2022-03-15
Robert Wilson,Sales,,Chicago,2022-08-05
Lisa Anderson,Engineering,98000,,2021-04-12
David Brown,Sales,72000,Chicago,2023-03-01
Jennifer Lee,Marketing,85000,New York,
Tom Harris,Engineering,110000,San Francisco,2020-07-18"""

        # Parse
        reader = csv.DictReader(io.StringIO(sample_csv))
        headers = reader.fieldnames
        rows = list(reader)

        # Profile
        profiles = profile_dataset(headers, rows)

        # Clean
        cleaned = clean_dataset(headers, rows, config={
            "strip_whitespace": True,
            "remove_duplicates": True,
            "fill_nulls": {"city": "Unknown", "start_date": "N/A"},
        })

        print(f"\n📊 Before: {len(rows)} rows → After: {len(cleaned)} rows")

        # Aggregate
        print("\n📈 Salary by Department:")
        agg = aggregate(cleaned, "department", "salary", "mean")
        for row in agg:
            print(f"  {row['department']:15s} | avg: ${row['mean_salary']:>10,.2f} | {row['count']} employees")

    elif args.input:
        headers, rows = read_csv(args.input)
        profile_dataset(headers, rows)

        cleaned = clean_dataset(headers, rows)

        if args.output:
            clean_headers = list(cleaned[0].keys()) if cleaned else headers
            write_csv(args.output, clean_headers, cleaned)
            print(f"\n💾 Saved to {args.output}")
