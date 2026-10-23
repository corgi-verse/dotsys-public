import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import struct
import zlib

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

    def test_new_brief_description_and_png_dimensions_are_used(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            brief = kit.load(ORIGINAL / "brief.json")
            brief["title"] = "A different room"
            brief["image_description"] = 'A sunlit reading corner with a blue textile and "oak" chair.'
            input_path = folder / "input.json"
            input_path.write_text(json.dumps(brief))
            # A valid tiny RGB PNG, generated as deterministic test data (not a concept).
            width, height = 3, 2
            def chunk(kind, data):
                return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
            png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress((b"\x00" + b"\xaa\xbb\xcc" * width) * height)) + chunk(b"IEND", b"")
            image = folder / "tiny.png"
            image.write_bytes(png)
            kit.build(input_path, image, folder / "out")
            output = (folder / "out/sheet.html").read_text()
            self.assertIn('width="3" height="2"', output)
            self.assertIn('alt="A sunlit reading corner with a blue textile and &quot;oak&quot; chair.', output)
            self.assertNotIn("A quiet listening room", output)
            self.assertEqual(kit.png_dimensions(image), (3, 2))
            broken = bytearray(png)
            broken[20] ^= 1
            image.write_bytes(broken)
            with self.assertRaisesRegex(ValueError, "IHDR"):
                kit.png_dimensions(image)
            missing = dict(brief)
            del missing["image_description"]
            with self.assertRaises(ValueError):
                kit.validate(missing)


if __name__ == "__main__":
    unittest.main()
