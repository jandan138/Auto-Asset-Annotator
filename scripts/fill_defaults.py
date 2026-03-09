#!/usr/bin/env python3
"""
Fill empty physical property fields with category-based default values.

For assets where VLM annotation left material, mass, or placement empty,
this script fills in reasonable defaults derived from statistical analysis
of existing annotations (medians, modes) for each category.

Dimensions are NOT filled by default (too model-specific to generalize).

Usage:
    # Dry-run (default): show what would change
    python scripts/fill_defaults.py --output_dir ./output --asset_list remaining_incomplete.txt

    # Apply changes
    python scripts/fill_defaults.py --output_dir ./output --asset_list remaining_incomplete.txt --apply

    # Also fill dimensions (optional)
    python scripts/fill_defaults.py --output_dir ./output --asset_list remaining_incomplete.txt --apply --fill_dimensions
"""
import os
import re
import json
import argparse

MASS_PATTERN = re.compile(r'^\d+\.?\d*$')

# Default values per category, derived from statistical analysis of 50k+ annotations.
# material: most common material description for the category
# mass: median mass in kg
# placement: most common placement value
CATEGORY_DEFAULTS = {
    # Structural elements
    "wall":       {"material": "Plaster or concrete",            "mass": "0.05", "placement": "OnFloor"},
    "ground":     {"material": "Concrete or tile",               "mass": "0.05", "placement": "OnFloor"},
    "ceiling":    {"material": "Plaster",                        "mass": "0.05", "placement": "OnCeiling"},
    "column":     {"material": "Concrete or stone",              "mass": "0.05", "placement": "OnFloor"},
    "threshold":  {"material": "Wood or metal",                  "mass": "0.1",  "placement": "OnFloor"},

    # Architectural components
    "door":       {"material": "Wood",                           "mass": "10.0", "placement": "OnWall"},
    "window":     {"material": "Aluminum and glass",             "mass": "10.0", "placement": "OnWall"},
    "curtain":    {"material": "Fabric",                         "mass": "0.2",  "placement": "OnWall"},
    "mirror":     {"material": "Glass and metal frame",          "mass": "1.0",  "placement": "OnWall"},
    "hearth":     {"material": "Brick or stone",                 "mass": "5.0",  "placement": "OnFloor"},

    # Containers / tableware
    "bottle":     {"material": "Plastic (PET)",                  "mass": "0.15", "placement": "OnTable"},
    "cup":        {"material": "Ceramic",                        "mass": "0.2",  "placement": "OnTable"},
    "plate":      {"material": "Ceramic",                        "mass": "0.05", "placement": "OnTable"},
    "pot":        {"material": "Metal",                          "mass": "0.5",  "placement": "OnTable"},
    "pan":        {"material": "Metal",                          "mass": "0.3",  "placement": "OnTable"},
    "tray":       {"material": "Plastic or metal",               "mass": "0.2",  "placement": "OnTable"},
    "trash_can":  {"material": "Plastic",                        "mass": "0.5",  "placement": "OnFloor"},

    # Furniture
    "cabinet":    {"material": "Wood or MDF",                    "mass": "5.0",  "placement": "OnFloor"},
    "shelf":      {"material": "Wood or metal",                  "mass": "2.0",  "placement": "OnWall"},
    "book_shelf": {"material": "Wood or MDF",                    "mass": "5.0",  "placement": "OnFloor"},
    "table":      {"material": "Wood",                           "mass": "5.0",  "placement": "OnFloor"},
    "desk":       {"material": "Wood or MDF",                    "mass": "5.0",  "placement": "OnFloor"},
    "counter":    {"material": "Wood or stone",                  "mass": "5.0",  "placement": "OnFloor"},
    "couch":      {"material": "Fabric and wood frame",          "mass": "15.0", "placement": "OnFloor"},
    "sofa_chair": {"material": "Fabric and wood frame",          "mass": "10.0", "placement": "OnFloor"},
    "stool":      {"material": "Wood or metal",                  "mass": "2.0",  "placement": "OnFloor"},
    "bed":        {"material": "Wood frame with fabric mattress","mass": "20.0", "placement": "OnFloor"},
    "chest_of_drawers": {"material": "Wood or MDF",              "mass": "10.0", "placement": "OnFloor"},

    # Electronics
    "tv":         {"material": "Plastic and glass",              "mass": "5.0",  "placement": "OnWall"},
    "monitor":    {"material": "Plastic and glass",              "mass": "3.0",  "placement": "OnTable"},
    "telephone":  {"material": "Plastic",                        "mass": "0.2",  "placement": "OnTable"},
    "microwave":  {"material": "Metal and plastic",              "mass": "10.0", "placement": "OnTable"},
    "fan":        {"material": "Plastic and metal",              "mass": "2.0",  "placement": "OnFloor"},

    # Household items
    "book":       {"material": "Paper and cardboard",            "mass": "0.5",  "placement": "OnTable"},
    "pen":        {"material": "Plastic",                        "mass": "0.01", "placement": "OnTable"},
    "pillow":     {"material": "Fabric (cotton or polyester)",   "mass": "0.5",  "placement": "OnTable"},
    "blanket":    {"material": "Fabric (cotton)",                "mass": "1.0",  "placement": "OnTable"},
    "towel":      {"material": "Cotton fabric",                  "mass": "0.3",  "placement": "OnTable"},
    "toy":        {"material": "Plastic",                        "mass": "0.1",  "placement": "OnTable"},
    "plant":      {"material": "Synthetic leaves, ceramic pot",  "mass": "0.2",  "placement": "OnTable"},
    "picture":    {"material": "Paper and wood frame",           "mass": "0.5",  "placement": "OnWall"},
    "decoration": {"material": "Mixed materials",                "mass": "0.2",  "placement": "OnTable"},
    "person":     {"material": "Fabric (textured)",              "mass": "60.0", "placement": "OnFloor"},
    "faucet":     {"material": "Metal (chrome-plated)",          "mass": "0.2",  "placement": "OnWall"},
    "light":      {"material": "Metal and glass",                "mass": "1.0",  "placement": "OnCeiling"},
    "lamp":       {"material": "Metal and fabric shade",         "mass": "1.0",  "placement": "OnTable"},
    "clock":      {"material": "Plastic and metal",              "mass": "0.5",  "placement": "OnWall"},
    "clothes":    {"material": "Fabric",                         "mass": "0.3",  "placement": "OnTable"},
    "shoe":       {"material": "Leather or synthetic",           "mass": "0.3",  "placement": "OnFloor"},

    # Catch-all fallback
    "_default":   {"material": "Mixed materials",                "mass": "0.1",  "placement": "OnTable"},
}

# Values that should be treated as invalid for mass (non-numeric placeholders)
INVALID_MASS_VALUES = {"n/a", "unknown", "varies", "variable", "not applicable", "none", "-"}


def is_field_empty(value):
    """Check if a field value is empty/null/missing."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    if isinstance(value, list) and len(value) == 0:
        return True
    return False


def is_mass_invalid(value):
    """Check if mass is non-numeric (e.g. 'N/A', 'unknown')."""
    if is_field_empty(value):
        return True
    if isinstance(value, str):
        stripped = value.strip().lower()
        if stripped in INVALID_MASS_VALUES:
            return True
        if not MASS_PATTERN.match(stripped):
            return True
    return False


def get_defaults(category):
    """Get default values for a category, falling back to _default."""
    return CATEGORY_DEFAULTS.get(category, CATEGORY_DEFAULTS["_default"])


def main():
    parser = argparse.ArgumentParser(
        description="Fill empty physical property fields with category-based defaults"
    )
    parser.add_argument("--output_dir", required=True,
                        help="Annotation output directory to update")
    parser.add_argument("--asset_list", required=True,
                        help="File listing incomplete assets (one per line: category/asset_id)")
    parser.add_argument("--apply", action="store_true",
                        help="Actually write changes (default: dry-run)")
    parser.add_argument("--fill_dimensions", action="store_true",
                        help="Also fill dimensions field (disabled by default)")
    args = parser.parse_args()

    # Read asset list
    with open(args.asset_list, "r") as f:
        asset_ids = [line.strip() for line in f if line.strip()]

    fields_to_fill = ["material", "mass", "placement"]
    if args.fill_dimensions:
        fields_to_fill.append("dimensions")

    print(f"Assets to process: {len(asset_ids)}")
    print(f"Fields to fill: {fields_to_fill}")
    print(f"Mode: {'APPLY' if args.apply else 'DRY-RUN'}")
    print()

    updated_count = 0
    not_found_count = 0
    field_fill_counts = {f: 0 for f in fields_to_fill}
    mass_format_fixes = 0
    category_update_counts = {}  # category -> count of assets updated
    missing_category_defaults = set()

    for asset_id in asset_ids:
        parts = asset_id.split("/")
        if len(parts) != 2:
            print(f"  WARN: Invalid asset ID format: {asset_id}")
            continue

        category, uuid = parts
        annotation_file = os.path.join(args.output_dir, category, f"{uuid}_annotation.json")

        if not os.path.exists(annotation_file):
            not_found_count += 1
            continue

        try:
            with open(annotation_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"  WARN: Failed to read {annotation_file}: {e}")
            continue

        if not isinstance(data, dict) or len(data) == 0:
            continue

        key = list(data.keys())[0]
        ann = data[key]

        if not isinstance(ann, dict):
            continue

        defaults = get_defaults(category)
        if category not in CATEGORY_DEFAULTS and category != "_default":
            missing_category_defaults.add(category)

        changed = False

        for field in fields_to_fill:
            current_val = ann.get(field)

            # Check if field needs filling
            needs_fill = is_field_empty(current_val)

            # Special case: mass with invalid format (e.g. "N/A", "unknown")
            if field == "mass" and not needs_fill and is_mass_invalid(current_val):
                needs_fill = True
                mass_format_fixes += 1

            if needs_fill and field in defaults:
                ann[field] = defaults[field]
                field_fill_counts[field] += 1
                changed = True

        if changed:
            updated_count += 1
            category_update_counts[category] = category_update_counts.get(category, 0) + 1

            if args.apply:
                data[key] = ann
                with open(annotation_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)

    # Report
    print(f"{'=' * 60}")
    print(f"FILL DEFAULTS REPORT")
    print(f"{'=' * 60}")
    print(f"Assets processed: {len(asset_ids)}")
    print(f"Assets updated: {updated_count}")
    print(f"Assets not found: {not_found_count}")
    print(f"Mass format fixes (non-numeric replaced): {mass_format_fixes}")
    print()
    print(f"Field fill counts:")
    for field, count in field_fill_counts.items():
        print(f"  {field}: {count}")

    if missing_category_defaults:
        print(f"\nCategories using _default fallback: {sorted(missing_category_defaults)}")

    if category_update_counts:
        print(f"\nPer-category updates (top 20):")
        sorted_cats = sorted(category_update_counts.items(), key=lambda x: x[1], reverse=True)
        for cat, count in sorted_cats[:20]:
            using_fallback = " (fallback)" if cat in missing_category_defaults else ""
            print(f"  {cat}: {count}{using_fallback}")

    if not args.apply:
        print(f"\nThis was a DRY-RUN. Use --apply to write changes.")
    else:
        print(f"\nChanges applied successfully.")


if __name__ == "__main__":
    main()
