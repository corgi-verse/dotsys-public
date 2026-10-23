#!/usr/bin/env python3
"""Validate public creation submissions and curated registry. Does not execute artifacts."""
import argparse
import hashlib
from html.parser import HTMLParser
import importlib.util
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
FIELDS = {"schema", "id", "title", "author", "tool", "artifact", "editable", "process", "evidence", "license", "sources", "parent", "credits", "manifest", "package", "use"}
TOOL_FILES = {"tools/visual-concept-kit/" + name for name in ("kit.py", "README.md", "SKILL.md")}
# Only this fixed, maintainer-owned adapter is imported, never a submission path.
# Review repository code before running it; submitted artifacts remain inert data.
_spec = importlib.util.spec_from_file_location("reviewed_visual_kit", ROOT / "tools/visual-concept-kit/kit.py")
_kit = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_kit)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package_digest(package):
    return hashlib.sha256(json.dumps(package, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def read(path):
    if path.stat().st_size > 100_000:
        raise ValueError("Record too large")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate key")
            result[key] = value
        return result
    return json.loads(path.read_text(), object_pairs_hook=unique)


def file(root, value):
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value or Path(value).is_absolute() or ".." in Path(value).parts or Path(value).as_posix() != value:
        raise ValueError("Use a safe repository-relative file path")
    target = root / value
    current = root
    for part in Path(value).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("Symlink package paths are unsupported: " + value)
    if not target.is_file() or not target.resolve().is_relative_to(root.resolve()):
        raise ValueError("Missing or unsafe file: " + value)
    return target


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.references = []

    def handle_starttag(self, tag, attrs):
        # The renderer emits external CSS only. Reject the entire unsupported
        # inline surface, irrespective of encoded values, casing or media type.
        if tag == "style" or any(key == "style" for key, _ in attrs):
            raise ValueError("Inline CSS is unsupported; use the declared static stylesheet")
        stylesheet = tag == "link" and any(key == "rel" and value and "stylesheet" in value.lower().split() for key, value in attrs)
        for key, value in attrs:
            if key in {"src", "href", "poster", "data"} and value:
                self.references.append((value, tag == "a" and key == "href", stylesheet and key == "href"))
            elif key == "srcset" and value:
                self.references.extend((item.strip().split()[0], False, False) for item in value.split(",") if item.strip())


def static_css(source):
    """Accept the renderer's bounded, resource-free CSS dialect, not arbitrary CSS.

    A regex URL extractor cannot cover CSS tokenization/escapes. This adapter
    therefore rejects those forms instead of claiming they were fully parsed.
    The actual generated sheets need no CSS-loaded images, fonts or imports.
    """
    if "\\" in source or "/*" in source or "*/" in source or any(ord(char) < 32 and char not in "\n\r\t" for char in source):
        raise ValueError("Unsupported CSS escapes, comments or control characters")
    if any(rule.lower() != "media" for rule in re.findall(r"@\s*([^\s({;]+)", source)):
        raise ValueError("Unsupported CSS at-rule; imports and resource declarations are not allowed")
    allowed = {"media", "clamp", "min", "max", "calc", "var", "rgb", "rgba", "hsl", "hsla", "linear-gradient", "radial-gradient", "repeating-linear-gradient", "repeating-radial-gradient", "repeat", "minmax"}
    for function in re.findall(r"([\w-]+)\s*\(", source):
        if function.lower() not in allowed:
            raise ValueError("Unsupported CSS function/resource form: " + function)


def linked_files(root, relative):
    path = file(root, relative)
    references = []
    if path.suffix.lower() == ".html":
        parser = Links()
        parser.feed(path.read_text())
        references = parser.references
    elif path.suffix.lower() == ".css":
        static_css(path.read_text())
    found = set()
    for value, navigation, stylesheet in references:
        url = urlsplit(value)
        if url.scheme or url.netloc:
            if not (navigation and url.scheme == "https" and url.netloc and not url.username and not url.password):
                raise ValueError("External executable/asset or unsafe link: " + value)
            continue  # External reference pages are references, not frozen package bytes.
        if not url.path:
            continue
        decoded = unquote(url.path)
        target = (Path(relative).parent / decoded).as_posix()
        dependency = file(root, target)
        if stylesheet:
            static_css(dependency.read_text())  # Content role, not filename, selects CSS checks.
        found.add(target)
    return found


def visual_package(root, record):
    if record["tool"] != "visual-concept-kit@1.1.0":
        raise ValueError("Tool needs an explicitly reviewed package adapter")
    manifest_path = file(root, record["manifest"])
    if manifest_path.name != "manifest.json":
        raise ValueError("Expected visual-kit manifest.json")
    package = record["package"]
    if not isinstance(package, dict) or not 1 <= len(package) <= 100:
        raise ValueError("Expected bounded full-package hash inventory")
    for relative, expected in package.items():
        if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected) or digest(file(root, relative)) != expected:
            raise ValueError("Package hash mismatch: " + str(relative))
    kit_root = manifest_path.parent
    prefix = Path(record["manifest"]).parent
    # Validate every manifest path before the trusted renderer reopens the data.
    manifest = read(manifest_path)
    if not isinstance(manifest.get("files"), dict):
        raise ValueError("Missing visual-kit file inventory")
    required = {record[key] for key in ("manifest", "process", "evidence", "license")} | {"NOTICE"} | TOOL_FILES
    for relative in manifest["files"]:
        file(root, (prefix / relative).as_posix())
        required.add((prefix / relative).as_posix())
    if not required <= package.keys():
        raise ValueError("Package omits manifest, linked artifacts, process, evidence, notices or tool source")
    if record["artifact"] != (prefix / "sheet.html").as_posix() or record["editable"] != (prefix / "brief.json").as_posix():
        raise ValueError("Artifact/editable input must match the visual-kit manifest")
    checked, _ = _kit.reopen(kit_root)
    if checked["tool"] != record["tool"]:
        raise ValueError("Submission and manifest tool versions differ")
    # Every local HTML/CSS dependency, including nested stylesheets, must be covered.
    for relative in package:
        if not linked_files(root, relative) <= package.keys():
            raise ValueError("Linked file missing from reviewed package: " + relative)
    return manifest


def submission(root, record):
    if not isinstance(record, dict) or set(record) != FIELDS or record["schema"] != "dotsys.creation/2":
        raise ValueError("Unsupported submission fields/schema")
    if not re.fullmatch(r"[a-z][a-z0-9-]{2,63}", record["id"]):
        raise ValueError("Invalid id")
    for key in ("title", "author", "tool", "use"):
        if not isinstance(record[key], str) or not record[key].strip() or len(record[key]) > 2000:
            raise ValueError("Missing bounded text: " + key)
    if not re.search(r"@\d+\.\d+\.\d+$", record["tool"]):
        raise ValueError("Tool must identify an exact semantic version")
    for key in ("artifact", "editable", "process", "evidence", "license", "manifest"):
        file(root, record[key])
    visual_package(root, record)
    for key in ("credits", "sources"):
        if not isinstance(record[key], list) or not record[key] or not all(isinstance(x, str) and x.strip() for x in record[key]):
            raise ValueError("Sources and credits must be explicit nonempty lists")
    if record["parent"] is not None and (not isinstance(record["parent"], str) or record["parent"] == record["id"]):
        raise ValueError("Invalid adaptation parent")
    return record


def registry(root):
    index = read(file(root, "creations/registry.json"))
    if set(index) != {"schema", "entries"} or index["schema"] != "dotsys.exchange/1":
        raise ValueError("Unsupported registry")
    records = {}
    for entry in index["entries"]:
        if set(entry) != {"submission", "review"}:
            raise ValueError("Registry entry needs submission and review")
        submission_path = file(root, entry["submission"])
        record = submission(root, read(submission_path))
        review = read(file(root, entry["review"]))
        if set(review) != {"schema", "status", "reviewer", "date", "scope", "checks", "submission_sha256", "package_sha256"} or review["schema"] != "dotsys.creation-review/2" or review["status"] != "accepted":
            raise ValueError("Only accepted, reviewed entries may be curated")
        if review["submission_sha256"] != digest(submission_path) or review["package_sha256"] != package_digest(record["package"]) or not review["reviewer"] or not review["scope"]:
            raise ValueError("Review must bind exact submission and full package; renewed review required")
        required = {"rights", "privacy", "actual_use", "editable_source", "credit", "recovery"}
        if set(review["checks"]) != required or any(value != "PASS" for value in review["checks"].values()):
            raise ValueError("Required review checks incomplete")
        if record["id"] in records:
            raise ValueError("Duplicate creation id")
        records[record["id"]] = record
    for record in records.values():
        parent = record["parent"]
        seen = {record["id"]}
        while parent:
            if parent not in records or parent in seen:
                raise ValueError("Missing parent or adaptation cycle")
            seen.add(parent)
            parent = records[parent]["parent"]
        if record["parent"]:
            ancestor = records[record["parent"]]
            if ancestor["id"] not in record["credits"] or ancestor["author"] not in record["credits"]:
                raise ValueError("Adaptation must preserve parent id and author credit")
            parent_manifest = read(file(root, ancestor["manifest"]))
            child_manifest = read(file(root, record["manifest"]))
            expected = {"id": parent_manifest["id"], "revision": parent_manifest["revision"], "manifest_sha256": digest(file(root, ancestor["manifest"]))}
            if child_manifest["parent"] != expected or child_manifest["revision"] != parent_manifest["revision"] + 1:
                raise ValueError("Adaptation manifest must bind exact curated parent")
        elif read(file(root, record["manifest"]))["parent"] is not None:
            raise ValueError("Original submission cannot hide a manifest parent")
    return records


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--submission", type=Path, help="Validate a proposed record without curating it")
    args = parser.parse_args()
    try:
        if args.submission:
            result = submission(ROOT, read(args.submission))
            print("PASS: valid proposed submission " + result["id"] + "; maintainer review still required")
        else:
            result = registry(ROOT)
            print("PASS: curated full packages, submission-bound reviews and exact parent credit: " + ", ".join(result))
    except (OSError, ValueError, TypeError, KeyError) as error:
        parser.exit(1, "Exchange error: " + str(error) + "\n")
