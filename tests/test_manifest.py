from pathlib import Path
import unittest


class ManifestTests(unittest.TestCase):
    def test_manifest_and_root_loader_exist(self):
        root = Path(__file__).resolve().parents[1]
        manifest = (root / "plugin.yaml").read_text(encoding="utf-8")
        self.assertIn("name: hermes-memory-policy-gate", manifest)
        self.assertIn("author: Mani Saint-Victor, MD / bionicbutterfly13", manifest)
        self.assertTrue((root / "__init__.py").exists())


if __name__ == "__main__":
    unittest.main()
