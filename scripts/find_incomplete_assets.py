#!/usr/bin/env python3
"""
Find assets with incomplete annotation fields.

Scans annotation files and identifies assets where physical property fields
(material, dimensions, mass, placement) are empty, null, or have invalid format.

Output format matches find_failed_assets.py — one asset per line (category/asset_id),
compatible with --asset_list_file parameter for re-annotation.
"""
import os
import re
import json
import argparse
from tqdm import tqdm


# Valid dimensions: "X * Y * Z" with numeric values
DIMENSIONS_PATTERN = re.compile(r'^\d+\.?\d*\s*\*\s*\d+\.?\d*\s*\*\s*\d+\.?\d*$')

# Valid mass: purely numeric
MASS_PATTERN = re.compile(r'^\d+\.?\d*$')


def is_field_empty(value):
    """Check if a field value is empty/null/missing."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    if isinstance(value, list) and len(value) == 0:
        return True
    return False


def is_dimensions_invalid(value):
    """Check if dimensions field has invalid format (not X * Y * Z)."""
    if is_field_empty(value):
        return True
    if isinstance(value, str):
        return not DIMENSIONS_PATTERN.match(value.strip())
    return True


def is_mass_invalid(value):
    """Check if mass field has invalid format (not numeric)."""
    if is_field_empty(value):
        return True
    if isinstance(value, str):
        return not MASS_PATTERN.match(value.strip())
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Find assets with incomplete annotation fields"
    )
    parser.add_argument("--output_dir", required=True,
                        help="Annotation output directory to scan")
    parser.add_argument("--save_list", default="incomplete_assets.txt",
                        help="Output file for incomplete asset list (default: incomplete_assets.txt)")
    parser.add_argument("--strict", action="store_true",
                        help="Also flag assets with invalid dimensions/mass format")
    parser.add_argument("--stats", action="store_true",
                        help="Print detailed statistics by category")
    args = parser.parse_args()

    incomplete_assets = []
    total_files = 0
    field_empty_counts = {"material": 0, "dimensions": 0, "mass": 0, "placement": 0}
    field_invalid_counts = {"dimensions": 0, "mass": 0}
    category_counts = {}  # category -> {total, incomplete}

    print(f"Scanning {args.output_dir}...")

    for root, dirs, files in os.walk(args.output_dir):
        for file in files:
            if not file.endswith("_annotation.json"):
                continue

            full_path = os.path.join(root, file)
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception:
                # Corrupted file — treat as incomplete
                rel_dir = os.path.relpath(root, args.output_dir)
                asset_name = file.replace("_annotation.json", "")
                asset_id = os.path.join(rel_dir, asset_name) if rel_dir != "." else asset_name
                incomplete_assets.append(asset_id)
                continue

            if not isinstance(data, dict) or len(data) == 0:
                continue

            total_files += 1
            first_key = list(data.keys())[0]
            ann = data[first_key]

            if not isinstance(ann, dict):
                continue

            # Skip raw_output files (handled by find_failed_assets.py)
            if "raw_output" in ann:
                continue

            category = first_key.split("/")[0] if "/" in first_key else "unknown"
            if category not in category_counts:
                category_counts[category] = {"total": 0, "incomplete": 0}
            category_counts[category]["total"] += 1

            is_incomplete = False

            for field in ["material", "dimensions", "mass", "placement"]:
                val = ann.get(field)
                if is_field_empty(val):
                    field_empty_counts[field] += 1
                    is_incomplete = True

            # Strict mode: also check format validity
            if args.strict:
                dim_val = ann.get("dimensions")
                if not is_field_empty(dim_val) and is_dimensions_invalid(dim_val):
                    field_invalid_counts["dimensions"] += 1
                    is_incomplete = True

                mass_val = ann.get("mass")
                if not is_field_empty(mass_val) and is_mass_invalid(mass_val):
                    field_invalid_counts["mass"] += 1
                    is_incomplete = True

            if is_incomplete:
                incomplete_assets.append(first_key)
                category_counts[category]["incomplete"] += 1

    # Save list
    with open(args.save_list, "w") as f:
        for asset in incomplete_assets:
            f.write(f"{asset}\n")

    # Report
    print(f"\nTotal annotation files scanned: {total_files}")
    print(f"Incomplete assets found: {len(incomplete_assets)}")
    print(f"List saved to {args.save_list}")

    print(f"\nEmpty field counts:")
    for field, count in field_empty_counts.items():
        print(f"  {field}: {count}")

    if args.strict:
        print(f"\nInvalid format counts (non-empty but bad format):")
        for field, count in field_invalid_counts.items():
            print(f"  {field}: {count}")

    if args.stats and category_counts:
        print(f"\nPer-category breakdown (top 20 by incomplete count):")
        sorted_cats = sorted(category_counts.items(),
                             key=lambda x: x[1]["incomplete"], reverse=True)
        for cat, counts in sorted_cats[:20]:
            pct = counts["incomplete"] / counts["total"] * 100 if counts["total"] > 0 else 0
            print(f"  {cat}: {counts['incomplete']}/{counts['total']} ({pct:.1f}%)")

    # Preview
    print(f"\nPreview of incomplete assets:")
    for a in incomplete_assets[:10]:
        print(f"  - {a}")
    if len(incomplete_assets) > 10:
        print(f"  ... and {len(incomplete_assets) - 10} more")


if __name__ == "__main__":
    main()
