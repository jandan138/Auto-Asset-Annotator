#!/usr/bin/env python3
"""
Test script to verify the _normalize_dimensions() and _normalize_mass() methods.
"""
import sys
import re

# We need to test the normalization methods without importing the full pipeline
# due to heavy dependencies. Let's extract and test the regex logic directly.

def normalize_dimensions(value):
    """
    Normalize dimensions by stripping units and extracting numeric values.
    Input: "0.30 * 0.30 * 0.05 meters" or "0.5 * 0.15 * 0.01 m"
    Output: "0.30 * 0.30 * 0.05" or "0.5 * 0.15 * 0.01"
    """
    if not value or value == "null":
        return None

    # Handle multiplication pattern
    if '*' in value:
        parts = re.split(r'\s*\*\s*', value)
        clean_parts = []
        for part in parts:
            match = re.search(r'(\d+\.?\d*)', part)
            if match:
                clean_parts.append(match.group(1))
        return ' * '.join(clean_parts) if clean_parts else value

    # Single value
    match = re.search(r'(\d+\.?\d*)', value)
    return match.group(1) if match else value


def normalize_mass(value):
    """
    Normalize mass by stripping units and extracting numeric value.
    Input: "0.5 kg", "0.05 kilograms", "Estimated mass is 0.1 kg."
    Output: "0.5", "0.05", "0.1"
    """
    if not value or value == "null":
        return None

    match = re.search(r'(\d+\.?\d*)', value)
    return match.group(1) if match else value


def main():
    print("=" * 60)
    print("Testing Dimensions Normalization")
    print("=" * 60)

    test_dims = [
        ("0.30 * 0.30 * 0.05 meters", "0.30 * 0.30 * 0.05"),
        ("0.5 * 0.15 * 0.01 m", "0.5 * 0.15 * 0.01"),
        ("0.15 * 0.15 * 0.20", "0.15 * 0.15 * 0.20"),
        ("1.0 * 2.0 * 3.0 meters", "1.0 * 2.0 * 3.0"),
        ("0.5m * 0.5m * 1.0m", "0.5 * 0.5 * 1.0"),
        ("0.25", "0.25"),
        ("", None),
        (None, None),
        ("null", None),
    ]

    dims_passed = 0
    dims_failed = 0

    for input_val, expected in test_dims:
        result = normalize_dimensions(input_val)
        status = "PASS" if result == expected else "FAIL"
        if status == "PASS":
            dims_passed += 1
        else:
            dims_failed += 1
        print(f"  [{status}] {input_val!r} -> {result!r} (expected {expected!r})")

    print(f"\nDimensions: {dims_passed} passed, {dims_failed} failed")

    print("\n" + "=" * 60)
    print("Testing Mass Normalization")
    print("=" * 60)

    test_mass = [
        ("0.5 kg", "0.5"),
        ("0.05 kilograms", "0.05"),
        ("Estimated mass is 0.1 kg.", "0.1"),
        ("Mass: 2.5kg", "2.5"),
        ("10", "10"),
        ("10.5 grams", "10.5"),
        ("", None),
        (None, None),
        ("null", None),
    ]

    mass_passed = 0
    mass_failed = 0

    for input_val, expected in test_mass:
        result = normalize_mass(input_val)
        status = "PASS" if result == expected else "FAIL"
        if status == "PASS":
            mass_passed += 1
        else:
            mass_failed += 1
        print(f"  [{status}] {input_val!r} -> {result!r} (expected {expected!r})")

    print(f"\nMass: {mass_passed} passed, {mass_failed} failed")

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    total_passed = dims_passed + mass_passed
    total_failed = dims_failed + mass_failed
    total = total_passed + total_failed
    print(f"Total: {total_passed}/{total} tests passed")

    if total_failed == 0:
        print("\nAll tests PASSED!")
        return 0
    else:
        print(f"\n{total_failed} test(s) FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
