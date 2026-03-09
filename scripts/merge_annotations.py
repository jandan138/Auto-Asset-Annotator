#!/usr/bin/env python3
"""
Merge re-annotated results back into existing annotation files.

Selectively fills only empty/null/invalid fields from new annotations,
preserving existing valid data (especially descriptions).

Usage:
    # Dry-run (default): show what would change
    python scripts/merge_annotations.py --old_dir ./output --new_dir ./output_reannotate

    # Apply changes
    python scripts/merge_annotations.py --old_dir ./output --new_dir ./output_reannotate --apply
"""
import os
import re
import json
import argparse
from tqdm import tqdm


DIMENSIONS_PATTERN = re.compile(r'^\d+\.?\d*\s*\*\s*\d+\.?\d*\s*\*\s*\d+\.?\d*$')
MASS_PATTERN = re.compile(r'^\d+\.?\d*$')


def is_field_empty(value):
    """Check if a field value is effectively empty."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    if isinstance(value, list) and len(value) == 0:
        return True
    return False


def is_field_invalid(field_name, value):
    """Check if a non-empty field has invalid format."""
    if is_field_empty(value):
        return True
    if field_name == "dimensions" and isinstance(value, str):
        return not DIMENSIONS_PATTERN.match(value.strip())
    if field_name == "mass" and isinstance(value, str):
        return not MASS_PATTERN.match(value.strip())
    return False


def main():
    parser = argparse.ArgumentParser(
        description="Merge re-annotated results into existing annotations"
    )
    parser.add_argument("--old_dir", required=True,
                        help="Existing annotation directory (will be updated)")
    parser.add_argument("--new_dir", required=True,
                        help="Re-annotated results directory")
    parser.add_argument("--apply", action="store_true",
                        help="Actually write changes (default: dry-run)")
    parser.add_argument("--fields", nargs="+",
                        default=["material", "dimensions", "mass", "placement"],
                        help="Fields to merge (default: material dimensions mass placement)")
    parser.add_argument("--include_description", action="store_true",
                        help="Also merge description field if empty in old")
    args = parser.parse_args()

    if args.include_description and "description" not in args.fields:
        args.fields = ["description"] + args.fields

    merge_fields = args.fields

    updated_count = 0
    skipped_count = 0
    no_new_count = 0
    field_update_counts = {f: 0 for f in merge_fields}
    new_also_empty = 0

    print(f"Scanning new annotations in {args.new_dir}...")
    print(f"Fields to merge: {merge_fields}")
    print(f"Mode: {'APPLY' if args.apply else 'DRY-RUN'}")
    print()

    for root, dirs, files in os.walk(args.new_dir):
        for file in files:
            if not file.endswith("_annotation.json"):
                continue

            new_path = os.path.join(root, file)

            # Compute corresponding old path
            rel_path = os.path.relpath(new_path, args.new_dir)
            old_path = os.path.join(args.old_dir, rel_path)

            if not os.path.exists(old_path):
                no_new_count += 1
                continue

            try:
                with open(new_path, 'r', encoding='utf-8') as f:
                    new_data = json.load(f)
                with open(old_path, 'r', encoding='utf-8') as f:
                    old_data = json.load(f)
            except Exception as e:
                print(f"  WARN: Failed to read {rel_path}: {e}")
                continue

            if not isinstance(old_data, dict) or not isinstance(new_data, dict):
                continue

            old_key = list(old_data.keys())[0]
            new_key = list(new_data.keys())[0]

            old_ann = old_data[old_key]
            new_ann = new_data[new_key]

            if not isinstance(old_ann, dict) or not isinstance(new_ann, dict):
                continue

            # Skip if new annotation is also a failure
            if "raw_output" in new_ann:
                skipped_count += 1
                continue

            changed = False
            for field in merge_fields:
                old_val = old_ann.get(field)
                new_val = new_ann.get(field)

                # Only update if old value is empty or invalid
                if is_field_invalid(field, old_val):
                    if not is_field_empty(new_val):
                        # For dimensions and mass, also validate new value format
                        if field == "dimensions" and isinstance(new_val, str):
                            if not DIMENSIONS_PATTERN.match(new_val.strip()):
                                continue  # New value also bad format, skip
                        if field == "mass" and isinstance(new_val, str):
                            if not MASS_PATTERN.match(new_val.strip()):
                                continue  # New value also bad format, skip

                        old_ann[field] = new_val
                        field_update_counts[field] += 1
                        changed = True
                    else:
                        new_also_empty += 1

            if changed:
                updated_count += 1
                if args.apply:
                    old_data[old_key] = old_ann
                    with open(old_path, 'w', encoding='utf-8') as f:
                        json.dump(old_data, f, indent=4, ensure_ascii=False)
            else:
                skipped_count += 1

    # Report
    print(f"\n{'=' * 60}")
    print(f"MERGE REPORT")
    print(f"{'=' * 60}")
    print(f"Files updated: {updated_count}")
    print(f"Files skipped (no changes needed): {skipped_count}")
    print(f"Files with no matching old file: {no_new_count}")
    print(f"Fields where new annotation was also empty: {new_also_empty}")
    print()
    print(f"Field update counts:")
    for field, count in field_update_counts.items():
        print(f"  {field}: {count}")

    if not args.apply:
        print(f"\nThis was a DRY-RUN. Use --apply to write changes.")


if __name__ == "__main__":
    main()
