#!/usr/bin/env python3
"""
Fill annotations from Auto-Asset-Annotator output to GRScenes target files.

This script reads annotation data from:
    /cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator/output/{category}/{asset_id}_annotation.json

And fills them into target files at:
    /cpfs/shared/simulation/zhuzihou/dev/usd-scene-physics-prep/GRScenes-test1/GRScenes_assets/{category}/{asset_id}/{asset_id}_annotation.json

Fields filled: description, material, dimensions, mass, placement
"""

import json
import os
from pathlib import Path
from typing import Optional

# Paths
SOURCE_DIR = Path("/cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator/output")
TARGET_DIR = Path("/cpfs/shared/simulation/zhuzihou/dev/usd-scene-physics-prep/GRScenes-test1/GRScenes_assets")


def parse_placement(placement_value: Optional[str]) -> list:
    """
    Parse placement string from source format to target array format.
    Source: "OnTable, OnObject" or "OnTable"
    Target: ["OnTable", "OnObject"]
    """
    if placement_value is None or placement_value == "":
        return []

    # Split by comma and strip whitespace
    placements = [p.strip() for p in str(placement_value).split(",")]
    # Filter out empty strings
    return [p for p in placements if p]


def process_annotation(source_file: Path, target_file: Path, dry_run: bool = False) -> dict:
    """
    Process a single annotation file pair.
    Returns status dict with success/failure info.
    """
    result = {
        "source": str(source_file),
        "target": str(target_file),
        "success": False,
        "skipped": False,
        "error": None,
        "fields_updated": []
    }

    try:
        # Read source file
        with open(source_file, 'r', encoding='utf-8') as f:
            source_data = json.load(f)

        # Source has nested structure: {"category/asset_id": {fields...}}
        if not source_data:
            result["error"] = "Empty source file"
            return result

        # Get the nested data (first and only value)
        source_annotation = list(source_data.values())[0]

        # Check for raw_output field (indicates parse failure, skip these)
        if "raw_output" in source_annotation:
            result["skipped"] = True
            result["error"] = "Source has raw_output (parse failure)"
            return result

        # Read target file
        with open(target_file, 'r', encoding='utf-8') as f:
            target_data = json.load(f)

        # Fields to copy
        fields = ["description", "material", "dimensions", "mass"]

        # Track if any changes were made
        changes_made = False

        for field in fields:
            source_value = source_annotation.get(field)
            # Skip None or empty values
            if source_value is not None and source_value != "":
                if target_data.get(field) != source_value:
                    target_data[field] = source_value
                    result["fields_updated"].append(field)
                    changes_made = True

        # Handle placement separately (needs format conversion)
        source_placement = source_annotation.get("placement")
        if source_placement is not None and source_placement != "":
            target_placement = parse_placement(source_placement)
            if target_data.get("placement") != target_placement:
                target_data["placement"] = target_placement
                result["fields_updated"].append("placement")
                changes_made = True

        if not changes_made:
            result["skipped"] = True
            result["error"] = "No changes needed (target already has data)"
            return result

        # Write updated target file
        if not dry_run:
            with open(target_file, 'w', encoding='utf-8') as f:
                json.dump(target_data, f, indent=2, ensure_ascii=False)

        result["success"] = True
        return result

    except FileNotFoundError as e:
        result["error"] = f"File not found: {e}"
        return result
    except json.JSONDecodeError as e:
        result["error"] = f"JSON decode error: {e}"
        return result
    except Exception as e:
        result["error"] = f"Unexpected error: {e}"
        return result


def find_matching_target(source_file: Path) -> Optional[Path]:
    """
    Find the matching target file for a given source file.
    Source: .../output/{category}/{asset_id}_annotation.json
    Target: .../{category}/{asset_id}/{asset_id}_annotation.json
    """
    # Parse source path
    parts = source_file.relative_to(SOURCE_DIR).parts
    if len(parts) != 2:
        return None

    category = parts[0]
    filename = parts[1]  # {asset_id}_annotation.json

    # Extract asset_id from filename
    if not filename.endswith("_annotation.json"):
        return None

    asset_id = filename[:-len("_annotation.json")]

    # Build target path
    target_file = TARGET_DIR / category / asset_id / f"{asset_id}_annotation.json"

    if target_file.exists():
        return target_file
    return None


def main(dry_run: bool = True, limit: Optional[int] = None, category_filter: Optional[str] = None):
    """
    Main processing function.

    Args:
        dry_run: If True, don't actually write changes
        limit: Maximum number of files to process (for testing)
        category_filter: Only process this category (for testing)
    """
    # Find all source files
    if category_filter:
        source_pattern = SOURCE_DIR / category_filter / "*_annotation.json"
        source_files = list(SOURCE_DIR.glob(f"{category_filter}/*_annotation.json"))
    else:
        source_files = list(SOURCE_DIR.glob("*/*_annotation.json"))

    # Sort for deterministic ordering
    source_files.sort()

    print(f"Found {len(source_files)} source annotation files")

    if limit:
        source_files = source_files[:limit]
        print(f"Limited to first {limit} files")

    # Statistics
    stats = {
        "total": 0,
        "success": 0,
        "skipped": 0,
        "failed": 0,
        "no_target": 0,
        "fields_updated": {}
    }

    for source_file in source_files:
        stats["total"] += 1

        # Find matching target
        target_file = find_matching_target(source_file)
        if not target_file:
            stats["no_target"] += 1
            continue

        # Process the file
        result = process_annotation(source_file, target_file, dry_run=dry_run)

        if result["success"]:
            stats["success"] += 1
            for field in result["fields_updated"]:
                stats["fields_updated"][field] = stats["fields_updated"].get(field, 0) + 1
        elif result["skipped"]:
            stats["skipped"] += 1
        else:
            stats["failed"] += 1
            print(f"Failed: {source_file} - {result['error']}")

        # Progress report every 1000 files
        if stats["total"] % 1000 == 0:
            print(f"Processed {stats['total']} files... (success: {stats['success']}, skipped: {stats['skipped']}, failed: {stats['failed']})")

    # Final report
    print("\n" + "="*60)
    print("FINAL REPORT")
    print("="*60)
    print(f"Total source files processed: {stats['total']}")
    print(f"Successfully updated: {stats['success']}")
    print(f"Skipped (no changes needed or raw_output): {stats['skipped']}")
    print(f"Failed: {stats['failed']}")
    print(f"No matching target: {stats['no_target']}")
    print("\nFields updated:")
    for field, count in stats["fields_updated"].items():
        print(f"  {field}: {count}")

    if dry_run:
        print("\n*** DRY RUN MODE - No files were actually modified ***")
        print("Run with --apply to apply changes")

    return stats


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fill annotations from source to target files")
    parser.add_argument("--apply", action="store_true", help="Actually apply changes (default is dry-run)")
    parser.add_argument("--limit", type=int, help="Limit to first N files (for testing)")
    parser.add_argument("--category", type=str, help="Only process specific category (for testing)")

    args = parser.parse_args()

    dry_run = not args.apply
    if dry_run:
        print("*** DRY RUN MODE ***")
        print("No files will be modified. Use --apply to apply changes.\n")

    main(dry_run=dry_run, limit=args.limit, category_filter=args.category)
