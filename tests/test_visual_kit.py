import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("kit", ROOT / "tools/visual-concept-kit/kit.py")
kit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kit)
ORIGINAL = ROOT / "creations/quiet-listening-room/original"
CLAY = ROOT / "creations/quiet-listening-room/clay"


class VisualKitTests(unittest.TestCase):
    def test_saved_outputs_and_parent(self):
        original, brief = kit.reopen(ORIGINAL)
        remix, adapted = kit.reopen(CLAY)
        self.assertEqual({k for k in brief if brief[k] != adapted[k]}, {"chair_upholstery"})
        self.assertEqual(remix["parent"]["manifest_sha256"], kit.digest(ORIGINAL / "manifest.json"))
        self.assertNotEqual(original["files"]["concept.png"], remix["files"]["concept.png"])

    def test_roundtrip_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "saved"
            kit.build(ORIGINAL / "brief.json", ORIGINAL / "concept.png", out)
            self.assertEqual(kit.reopen(out)[1], kit.reopen(ORIGINAL)[1])
            with self.assertRaises(FileExistsError):
                kit.build(ORIGINAL / "brief.json", ORIGINAL / "concept.png", out)
            (out / "brief.md").write_text("tampered")
            with self.assertRaisesRegex(ValueError, "Hash mismatch"):
                kit.reopen(out)

    def test_remix_rejects_extra_changes_and_same_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            brief = kit.load(CLAY / "brief.json")
            brief["intent"] = "An unauthorized second change"
            input_path = folder / "brief.json"
            input_path.write_text(json.dumps(brief))
            with self.assertRaisesRegex(ValueError, "only chair"):
                kit.build(input_path, CLAY / "concept.png", folder / "out", ORIGINAL, "chair_upholstery")
            with self.assertRaisesRegex(ValueError, "newly edited image"):
                kit.build(CLAY / "brief.json", ORIGINAL / "concept.png", folder / "out", ORIGINAL, "chair_upholstery")

    def test_untrusted_input_and_paths(self):
        brief = kit.load(ORIGINAL / "brief.json")
        bad = copy.deepcopy(brief)
        bad["chair_upholstery"]["color"] = "red;display:none"
        with self.assertRaises(ValueError):
            kit.validate(bad)
        with self.assertRaises(ValueError):
            kit.local_file(ORIGINAL, "../PROCESS.md")
        self.assertEqual(kit.text("<script>run()</script>"), "&lt;script&gt;run()&lt;/script&gt;")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "duplicate.json"
            path.write_text('{"a":1,"a":2}')
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                kit.load(path)


if __name__ == "__main__":
    unittest.main()
