# test_enhanced_parser.py
import sys
sys.path.insert(0, 'src')

from auto_asset_annotator.core.pipeline import AnnotationPipeline

# Mock config and engine
class MockConfig:
    data = type('obj', (object,), {'input_dir': './data'})()

class MockEngine:
    pass

pipeline = AnnotationPipeline(MockConfig(), MockEngine())

# Test cases
test_cases = [
    # Multi-object format with markdown headers
    ("""**Object 1: Ruler**

* **Category:** Measuring Tool
* **Description:** The ruler has a straight shape
* **Material:** The ruler is made of plastic
* **Dimensions:** 0.25 * 0.01 * 0.005 meters
* **Mass:** 0.05 kg

**Object 2: Toothpick**
* **Category:** Tool
...""", "Should extract ruler data (markdown format)"),

    # Multi-object format with plain text
    ("""Object 1:
Category: Bowl
Description: A blue bowl
Material: Ceramic

Object 2:
Category: Cup
Description: A red cup
...""", "Should extract bowl data (plain format)"),

    # addCriterion artifact
    ("Category: Bowl\nDescription: A blue bowl\naddCriterion: mass is 0.5",
     "Should remove addCriterion"),

    # Repetition pattern
    ("Category: Cup\nDescription: cup cup cup cup is blue",
     "Should remove repetition"),

    # **Image artifact
    ("**Image\n\nCategory: Plate\nDescription: A plate",
     "Should remove **Image prefix"),

    # Normal single object (should work as before)
    ("Category: Bowl\nDescription: A blue bowl\nMaterial: Ceramic",
     "Should parse normally"),
]

print("Testing enhanced parser methods:")
print("=" * 60)

for text, desc in test_cases:
    result = pipeline.parse_structured_text_enhanced(text)
    print(f"\n{desc}:")
    print(f"  Input preview: {text[:50]}...")
    print(f"  Result: {result}")

print("\n" + "=" * 60)
print("Testing individual helper methods:")
print("=" * 60)

# Test _clean_artifacts
print("\n1. Testing _clean_artifacts:")
text_with_artifact = "Category: Bowl\naddCriterion: mass is 0.5"
cleaned = pipeline._clean_artifacts(text_with_artifact)
print(f"   Input: {repr(text_with_artifact)}")
print(f"   Output: {repr(cleaned)}")

# Test _is_multi_object_output
print("\n2. Testing _is_multi_object_output:")
multi_obj_text = "Object 1:\nCategory: Bowl\n\nObject 2:\nCategory: Cup"
is_multi = pipeline._is_multi_object_output(multi_obj_text)
print(f"   Input: {repr(multi_obj_text[:40])}...")
print(f"   Is multi-object: {is_multi}")

single_obj_text = "Category: Bowl\nDescription: A bowl"
is_multi = pipeline._is_multi_object_output(single_obj_text)
print(f"   Input: {repr(single_obj_text)}")
print(f"   Is multi-object: {is_multi}")

# Test _extract_first_object
print("\n3. Testing _extract_first_object:")
first_obj = pipeline._extract_first_object(multi_obj_text)
print(f"   Input: {repr(multi_obj_text)}")
print(f"   First object: {repr(first_obj)}")

print("\n" + "=" * 60)
print("All tests completed!")
