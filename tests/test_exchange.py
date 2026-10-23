import copy
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("exchange", ROOT / "tools/validate_exchange.py")
exchange = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exchange)


class ExchangeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="dotsys-exchange-test-")
        self.root = Path(self.temporary.name)
        index = exchange.read(ROOT / "creations/registry.json")
        files = {"creations/registry.json"}
        for entry in index["entries"]:
            files.update(entry.values())
            files.update(exchange.read(ROOT / entry["submission"])["package"])
        for relative in files:
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)

    def tearDown(self):
        self.temporary.cleanup()

    def rebind_fixture(self, version, changed):
        """Recompute test-fixture acceptance so stale hashes cannot mask closure bugs."""
        path = self.root / ("creations/quiet-listening-room/" + version + "/submission.json")
        record = exchange.read(path)
        manifest_path = self.root / record["manifest"]
        manifest = exchange.read(manifest_path)
        manifest["files"][changed] = exchange.digest(manifest_path.parent / changed)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
        record["package"] = {key: exchange.digest(self.root / key) for key in record["package"]}
        path.write_text(json.dumps(record, indent=2) + "\n")
        review_path = path.parent / "review.json"
        review = exchange.read(review_path)
        review["submission_sha256"] = exchange.digest(path)
        review["package_sha256"] = exchange.package_digest(record["package"])
        review_path.write_text(json.dumps(review, indent=2) + "\n")

    def test_recomputed_acceptance_rejects_every_inline_css_form(self):
        folder = self.root / "creations/quiet-listening-room/clay"
        saved = {name: (folder / name).read_bytes() for name in ["sheet.html", "manifest.json", "submission.json", "review.json"]}
        extra = folder / "unreviewed.png"
        extra.write_bytes(b"original uncovered local asset")
        cases = [
            '<div style="background:url(unreviewed.png)">x</div>',
            '<DIV StYlE="background:URL(https://example.com/remote.png)">x</DIV>',
            '<div style="background&#58;url&#40;unreviewed%2Epng&#41;">x</div>',
            r'<div style="background:u\72l(unreviewed.png)">x</div>',
            '<div style>x</div>',
            '<style>body{background:url(unreviewed.png)}</style>',
            '<STYLE media="print">@IMPORT "https://example.com/remote.css";</STYLE>',
            r'<style>body{background:u\000072l(unreviewed.png)}</style>',
            r'<style>@\69mport "remote.css";</style>',
            '<style>body{background:u/**/rl(unreviewed.png)}</style>',
            '<svg><style>rect{fill:url(unreviewed.png)}</style></svg>',
            '<style/>',
        ]
        for payload in cases:
            with self.subTest(payload=payload):
                for name, data in saved.items():
                    (folder / name).write_bytes(data)
                (folder / "sheet.html").write_bytes(saved["sheet.html"].replace(b"</body>", payload.encode() + b"</body>"))
                self.rebind_fixture("clay", "sheet.html")
                with self.assertRaisesRegex(ValueError, "Inline CSS"):
                    exchange.registry(self.root)
                extra.write_bytes(b"changed uncovered asset")
                with self.assertRaisesRegex(ValueError, "Inline CSS"):
                    exchange.registry(self.root)
        for name, data in saved.items():
            (folder / name).write_bytes(data)
        self.assertEqual(len(exchange.registry(self.root)), 2)

    def test_recomputed_acceptance_rejects_unsupported_stylesheet_resource_syntax(self):
        folder = self.root / "creations/quiet-listening-room/clay"
        saved = {name: (folder / name).read_bytes() for name in ["sheet.css", "manifest.json", "submission.json", "review.json"]}
        cases = [
            'body{background:url(unreviewed.png)}',
            'body{background:URL("unreviewed space.png")}',
            'body{background:url(unreviewed%2Epng)}',
            '@IMPORT "https://example.com/remote.css";',
            r'body{background:u\72l(unreviewed.png)}',
            r'@\69mport "remote.css";',
            r'body{background:url(\75nreviewed.png)}',
            'body{background:u/**/rl(unreviewed.png)}',
            'body{background:image-set("unreviewed.png" 1x)}',
            'body{background:-webkit-image-set("unreviewed.png" 1x)}',
        ]
        for payload in cases:
            with self.subTest(payload=payload):
                for name, data in saved.items():
                    (folder / name).write_bytes(data)
                (folder / "sheet.css").write_text(payload)
                self.rebind_fixture("clay", "sheet.css")
                with self.assertRaisesRegex(ValueError, "Unsupported CSS"):
                    exchange.registry(self.root)
        for name, data in saved.items():
            (folder / name).write_bytes(data)
        self.assertEqual(len(exchange.registry(self.root)), 2)

    def test_stylesheet_content_role_and_extension_case_cannot_skip_checks(self):
        for name in ["theme.CSS", "theme", "theme.html"]:
            with self.subTest(name=name):
                (self.root / name).write_text('body{background:URL(unreviewed.png)}')
                (self.root / "linked.html").write_text('<link rel="StyleSheet" href="' + name + '">')
                with self.assertRaisesRegex(ValueError, "Unsupported CSS"):
                    exchange.linked_files(self.root, "linked.html")

    def test_registry_has_real_original_and_credited_adaptation(self):
        records = exchange.registry(ROOT)
        self.assertEqual(records["quiet-listening-room-clay"]["parent"], "quiet-listening-room-jade")
        self.assertIn("quiet-listening-room-jade", records["quiet-listening-room-clay"]["credits"])

    def test_proposal_hash_missing_file_and_parent_errors(self):
        original = exchange.read(ROOT / "creations/quiet-listening-room/original/submission.json")
        self.assertEqual(exchange.submission(ROOT, original)["id"], "quiet-listening-room-jade")
        for field, value in [("package", {}), ("editable", "missing.json"), ("process", "../private.md"), ("tool", "latest"), ("parent", original["id"])]:
            bad = copy.deepcopy(original)
            bad[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                exchange.submission(ROOT, bad)

    def test_every_covered_file_tamper_invalidates_acceptance(self):
        records = exchange.registry(self.root)
        covered = set().union(*(record["package"] for record in records.values()))
        self.assertTrue(any(path.endswith("concept.png") for path in covered))
        self.assertTrue(any(path.endswith("PROCESS.md") for path in covered))
        for relative in sorted(covered):
            with self.subTest(file=relative):
                path = self.root / relative
                previous = path.read_bytes()
                try:
                    path.write_bytes(previous + b"\nchanged without review\n")
                    with self.assertRaises(ValueError):
                        exchange.registry(self.root)
                finally:
                    path.write_bytes(previous)
        self.assertEqual(exchange.registry(self.root).keys(), records.keys())

    def test_recomputed_image_manifest_inventory_cannot_reuse_review(self):
        path = self.root / "creations/quiet-listening-room/original/submission.json"
        record = exchange.read(path)
        image = self.root / "creations/quiet-listening-room/original/concept.png"
        image.write_bytes(image.read_bytes() + b"\nchanged image bytes\n")
        manifest_path = self.root / record["manifest"]
        manifest = exchange.read(manifest_path)
        manifest["files"]["concept.png"] = exchange.digest(image)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
        record["package"] = {key: exchange.digest(self.root / key) for key in record["package"]}
        path.write_text(json.dumps(record, indent=2) + "\n")
        exchange.submission(self.root, record)  # New proposal is valid; old acceptance is not.
        with self.assertRaisesRegex(ValueError, "renewed review"):
            exchange.registry(self.root)

    def test_changed_credit_or_package_inventory_requires_new_review(self):
        path = self.root / "creations/quiet-listening-room/original/submission.json"
        original = path.read_bytes()
        for field, value in [("author", "Different author"), ("credits", ["Changed credit"]), ("sources", ["Changed source"]), ("use", "Different execution route")]:
            with self.subTest(field=field):
                record = json.loads(original)
                record[field] = value
                path.write_text(json.dumps(record) + "\n")
                with self.assertRaisesRegex(ValueError, "renewed review"):
                    exchange.registry(self.root)
        path.write_bytes(original)
        record = json.loads(original)
        del record["package"]["creations/quiet-listening-room/original/concept.png"]
        with self.assertRaisesRegex(ValueError, "omits"):
            exchange.submission(self.root, record)

    def test_manifest_and_dependency_paths_and_symlinks_fail_closed(self):
        record = exchange.read(self.root / "creations/quiet-listening-room/original/submission.json")
        for relative in ["../outside", "/etc/passwd", "creations/../LICENSE", "creations//file", "creations\\file"]:
            with self.subTest(path=relative), self.assertRaises(ValueError):
                exchange.file(self.root, relative)
        alias = self.root / "alias"
        alias.symlink_to(self.root / "creations", target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "Symlink"):
            exchange.file(self.root, "alias/quiet-listening-room/original/concept.png")
        for relative, content in [("linked.html", '<img src="../../outside.png">'), ("external.html", '<img src="https://example.com/image.png">'), ("linked.css", '@import "missing.css";')]:
            (self.root / relative).write_text(content)
            with self.subTest(dependency=relative), self.assertRaises(ValueError):
                exchange.linked_files(self.root, relative)
        (self.root / "extra.png").write_bytes(b"unreviewed")
        manifest_path = self.root / record["manifest"]
        manifest = exchange.read(manifest_path)
        sheet = self.root / record["artifact"]
        sheet.write_text(sheet.read_text().replace('src="concept.png"', 'src="extra.png"'))
        # Keep the new dependency in the artifact folder, outside its declared inventory.
        shutil.copyfile(self.root / "extra.png", sheet.parent / "extra.png")
        manifest["files"]["sheet.html"] = exchange.digest(sheet)
        manifest_path.write_text(json.dumps(manifest) + "\n")
        record["package"] = {key: exchange.digest(self.root / key) for key in record["package"]}
        with self.assertRaisesRegex(ValueError, "Linked file missing"):
            exchange.submission(self.root, record)

    def test_stale_review_and_hidden_parent_are_rejected(self):
        index = exchange.read(self.root / "creations/registry.json")
        review_path = self.root / index["entries"][0]["review"]
        review = exchange.read(review_path)
        review["package_sha256"] = "0" * 64
        review_path.write_text(json.dumps(review))
        with self.assertRaisesRegex(ValueError, "renewed review"):
            exchange.registry(self.root)
        shutil.copyfile(ROOT / index["entries"][0]["review"], review_path)
        child_path = self.root / index["entries"][1]["submission"]
        child = exchange.read(child_path)
        child["parent"] = None
        child_path.write_text(json.dumps(child) + "\n")
        child_review_path = self.root / index["entries"][1]["review"]
        child_review = exchange.read(child_review_path)
        child_review["submission_sha256"] = exchange.digest(child_path)
        child_review_path.write_text(json.dumps(child_review) + "\n")
        with self.assertRaisesRegex(ValueError, "hide a manifest parent"):
            exchange.registry(self.root)


if __name__ == "__main__":
    unittest.main()
