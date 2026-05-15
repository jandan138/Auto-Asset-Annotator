import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "sync_grscenes_annotations.py"


def load_sync_module():
    spec = importlib.util.spec_from_file_location(
        "sync_grscenes_annotations", SCRIPT_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


class TestSyncGRScenesAnnotations(unittest.TestCase):
    def setUp(self):
        self.module = load_sync_module()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.source_dir = self.root / "output"
        self.target_dir = self.root / "GRScenes_assets"
        self.audit_jsonl = self.root / "logs" / "audit.jsonl"

    def write_source(self, category="chair", asset_id="abc123", annotation=None):
        annotation = annotation or {
            "category": category,
            "description": "A compact wooden chair.",
            "material": "Wood",
            "dimensions": "0.5 * 0.5 * 0.8",
            "mass": "3.0",
            "placement": "OnFloor, OnObject",
        }
        source_path = self.source_dir / category / f"{asset_id}_annotation.json"
        write_json(source_path, {f"{category}/{asset_id}": annotation})
        return source_path

    def write_target(self, category="chair", asset_id="abc123", overrides=None):
        data = {
            "uid": asset_id,
            "category": category,
            "description": "",
            "material": "",
            "dimensions": "",
            "mass": "",
            "placement": [],
            "asset_type": "rigid",
            "glb_size": None,
            "usd_size": 1.25,
            "urdf_size": None,
            "orientation": 0,
            "usd_material_softlink": True,
        }
        if overrides:
            data.update(overrides)
        target_path = (
            self.target_dir
            / category
            / asset_id
            / f"{asset_id}_annotation.json"
        )
        write_json(target_path, data)
        return target_path

    def read_audit(self):
        return [
            json.loads(line)
            for line in self.audit_jsonl.read_text(encoding="utf-8").splitlines()
        ]

    def test_dry_run_reports_updates_without_writing_target(self):
        self.write_source()
        target_path = self.write_target()
        before = target_path.read_text(encoding="utf-8")

        summary = self.module.sync_annotations(
            self.source_dir,
            self.target_dir,
            audit_jsonl=self.audit_jsonl,
            dry_run=True,
        )

        self.assertEqual(summary["source_files"], 1)
        self.assertEqual(summary["matched_target"], 1)
        self.assertEqual(summary["updated"], 1)
        self.assertEqual(summary["failed"], 0)
        self.assertEqual(target_path.read_text(encoding="utf-8"), before)

        audit = self.read_audit()
        self.assertEqual(audit[0]["action"], "updated")
        self.assertTrue(audit[0]["dry_run"])
        self.assertEqual(
            sorted(audit[0]["fields"].keys()),
            ["description", "dimensions", "mass", "material", "placement"],
        )
        self.assertEqual(audit[0]["fields"]["placement"]["new"], ["OnFloor", "OnObject"])

    def test_apply_updates_target_and_writes_backup_outside_dataset(self):
        self.write_source()
        target_path = self.write_target()
        backup_dir = self.root / "backup"

        summary = self.module.sync_annotations(
            self.source_dir,
            self.target_dir,
            audit_jsonl=self.audit_jsonl,
            backup_dir=backup_dir,
            dry_run=False,
        )

        self.assertEqual(summary["updated"], 1)
        updated = json.loads(target_path.read_text(encoding="utf-8"))
        self.assertEqual(updated["uid"], "abc123")
        self.assertEqual(updated["asset_type"], "rigid")
        self.assertEqual(updated["description"], "A compact wooden chair.")
        self.assertEqual(updated["material"], "Wood")
        self.assertEqual(updated["dimensions"], "0.5 * 0.5 * 0.8")
        self.assertEqual(updated["mass"], "3.0")
        self.assertEqual(updated["placement"], ["OnFloor", "OnObject"])

        backup_path = backup_dir / "chair" / "abc123" / "abc123_annotation.json"
        self.assertTrue(backup_path.exists())
        backup_data = json.loads(backup_path.read_text(encoding="utf-8"))
        self.assertEqual(backup_data["description"], "")

        audit = self.read_audit()
        self.assertEqual(audit[0]["backup"], str(backup_path))

    def test_default_mode_does_not_overwrite_non_empty_target_fields(self):
        self.write_source(
            annotation={
                "category": "chair",
                "description": "New description",
                "material": "New material",
                "dimensions": "1.0 * 1.0 * 1.0",
                "mass": "9.0",
                "placement": "OnTable",
            }
        )
        target_path = self.write_target(
            overrides={
                "description": "Existing description",
                "material": "Existing material",
                "dimensions": "0.1 * 0.1 * 0.1",
                "mass": "1.0",
                "placement": ["OnFloor"],
            }
        )

        summary = self.module.sync_annotations(
            self.source_dir,
            self.target_dir,
            audit_jsonl=self.audit_jsonl,
            backup_dir=self.root / "backup",
            dry_run=False,
        )

        self.assertEqual(summary["updated"], 0)
        self.assertEqual(summary["skipped"], 1)
        target = json.loads(target_path.read_text(encoding="utf-8"))
        self.assertEqual(target["description"], "Existing description")
        self.assertEqual(target["placement"], ["OnFloor"])

    def test_overwrite_mode_replaces_non_empty_target_fields(self):
        self.write_source(
            annotation={
                "category": "chair",
                "description": "New description",
                "material": "New material",
                "dimensions": "1.0 * 1.0 * 1.0",
                "mass": "9.0",
                "placement": "OnTable",
            }
        )
        target_path = self.write_target(
            overrides={
                "description": "Existing description",
                "placement": ["OnFloor"],
            }
        )

        summary = self.module.sync_annotations(
            self.source_dir,
            self.target_dir,
            audit_jsonl=self.audit_jsonl,
            backup_dir=self.root / "backup",
            dry_run=False,
            overwrite=True,
        )

        self.assertEqual(summary["updated"], 1)
        target = json.loads(target_path.read_text(encoding="utf-8"))
        self.assertEqual(target["description"], "New description")
        self.assertEqual(target["placement"], ["OnTable"])

    def test_source_key_must_match_source_path(self):
        write_json(
            self.source_dir / "chair" / "abc123_annotation.json",
            {
                "table/abc123": {
                    "category": "table",
                    "description": "Wrong path key",
                }
            },
        )
        self.write_target()

        summary = self.module.sync_annotations(
            self.source_dir,
            self.target_dir,
            audit_jsonl=self.audit_jsonl,
            dry_run=True,
        )

        self.assertEqual(summary["failed"], 1)
        audit = self.read_audit()
        self.assertEqual(audit[0]["action"], "failed")
        self.assertEqual(audit[0]["reason"], "source_key_path_mismatch")

    def test_apply_rejects_backup_dir_inside_target_dir(self):
        self.write_source()
        self.write_target()

        with self.assertRaisesRegex(ValueError, "backup_dir must be outside target_dir"):
            self.module.sync_annotations(
                self.source_dir,
                self.target_dir,
                audit_jsonl=self.audit_jsonl,
                backup_dir=self.target_dir / "_backup",
                dry_run=False,
            )

    def test_apply_rejects_existing_backup_file(self):
        self.write_source()
        self.write_target()
        backup_dir = self.root / "backup"
        stale_backup = backup_dir / "chair" / "abc123" / "abc123_annotation.json"
        write_json(stale_backup, {"stale": True})

        with self.assertRaisesRegex(ValueError, "backup target already exists"):
            self.module.sync_annotations(
                self.source_dir,
                self.target_dir,
                audit_jsonl=self.audit_jsonl,
                backup_dir=backup_dir,
                dry_run=False,
            )


if __name__ == "__main__":
    unittest.main()
