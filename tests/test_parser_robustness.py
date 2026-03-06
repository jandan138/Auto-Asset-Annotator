
import unittest
from src.auto_asset_annotator.core.pipeline import AnnotationPipeline
from src.auto_asset_annotator.config.settings import Config
from src.auto_asset_annotator.core.model import ModelEngine

# Mock classes to avoid full initialization
class MockConfig:
    pass

class MockEngine:
    pass

class TestPipeline(unittest.TestCase):
    def setUp(self):
        self.pipeline = AnnotationPipeline(MockConfig(), MockEngine())

    def test_multi_object_parsing(self):
        # Text from the stubborn failed case
        text = """### Object 1

**Category:** Ceiling Panel

**Description:** The ceiling panel has a rectangular shape...

**Material:** The main material of the ceiling panel appears to be...

**Dimensions:** 2.0 m * 1.0 m * 0.05 m

**Mass:** 10 kg

**Placement:** OnCeiling

---

### Object 2

**Category:** Pole

**Description:** The pole is a slender...
"""
        result = self.pipeline.parse_structured_text(text)
        
        # Should extract Object 1's details
        self.assertEqual(result.get('category'), "Ceiling Panel")
        self.assertTrue(result.get('description').startswith("The ceiling panel"))
        self.assertEqual(result.get('mass'), "10 kg")
        
        # Should NOT contain Object 2's details mixed in
        self.assertNotIn("Pole", result.get('category'))

    def test_missing_fields(self):
        text = """
Category: Cup
Description: A nice cup.
"""
        result = self.pipeline.parse_structured_text(text)
        self.assertEqual(result.get('category'), "Cup")
        self.assertEqual(result.get('description'), "A nice cup.")
        self.assertIsNone(result.get('mass')) # Should be None, not fail

    def test_messy_format(self):
        text = """
Here is the info:
* Category: Bowl
* Description: 
A white bowl.
Very round.
* Material: Ceramic
"""
        result = self.pipeline.parse_structured_text(text)
        self.assertEqual(result.get('category'), "Bowl")
        self.assertIn("A white bowl", result.get('description'))
        self.assertIn("Very round", result.get('description'))
        self.assertEqual(result.get('material'), "Ceramic")

if __name__ == '__main__':
    unittest.main()
