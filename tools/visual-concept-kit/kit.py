#!/usr/bin/env python3
"""Visual Concept Kit 1.1.0. Standard-library renderer for a dot/Codex workflow."""
import argparse
import hashlib
import html
import json
from pathlib import Path
import re
import shutil
import struct
import sys
import zlib

VERSION = "visual-concept-kit@1.1.0"
KEYS = {"id", "title", "intent", "image_description", "qualities", "palette", "materials", "lighting", "locked", "chair_upholstery", "sources"}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key: " + key)
            result[key] = value
        return result
    if path.stat().st_size > 100_000:
        raise ValueError("Record too large")
    return json.loads(path.read_text(), object_pairs_hook=unique)


def text(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 2000:
        raise ValueError("Expected nonempty bounded text")
    return html.escape(value)


def validate(brief, legacy=False):
    expected = KEYS - {"image_description"} if legacy else KEYS
    if not isinstance(brief, dict) or set(brief) != expected:
        raise ValueError("Unsupported brief fields")
    if not re.fullmatch(r"[a-z][a-z0-9-]{2,63}", brief["id"]):
        raise ValueError("Invalid id")
    for key in (("title", "intent") if legacy else ("title", "intent", "image_description")):
        text(brief[key])
    for key in ("qualities", "materials", "lighting", "locked"):
        if not isinstance(brief[key], list) or not 1 <= len(brief[key]) <= 12:
            raise ValueError("Expected a bounded list: " + key)
        for value in brief[key]:
            text(value)
    for choice in brief["palette"] + [brief["chair_upholstery"]]:
        if set(choice) != {"name", "color", "role"}:
            raise ValueError("Invalid palette choice")
        text(choice["name"])
        text(choice["role"])
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", choice["color"]):
            raise ValueError("Expected six-digit hex color")
    if not 2 <= len(brief["palette"]) <= 8 or not 1 <= len(brief["sources"]) <= 12:
        raise ValueError("Palette or source count out of bounds")
    for source in brief["sources"]:
        if set(source) != {"title", "url", "credit", "rights"}:
            raise ValueError("Source needs title, url, credit, rights")
        for value in source.values():
            text(value)
        if not source["url"].startswith("https://"):
            raise ValueError("Reference URLs must use HTTPS")


def local_file(root, relative):
    if not isinstance(relative, str) or not relative or "\\" in relative or "\x00" in relative or Path(relative).is_absolute() or ".." in Path(relative).parts or Path(relative).as_posix() != relative:
        raise ValueError("Unsafe relative path")
    path = root / relative
    current = root
    for part in Path(relative).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("Unsafe symlink path")
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("Missing file or unsafe symlink: " + relative)
    return path


def png_dimensions(path):
    if path.stat().st_size > 25_000_000:
        raise ValueError("Provide a PNG concept image under 25 MB")
    with path.open("rb") as stream:
        header = stream.read(33)
    if len(header) != 33 or header[:16] != b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" or zlib.crc32(header[12:29]) != int.from_bytes(header[29:33], "big"):
        raise ValueError("Missing or invalid PNG IHDR metadata")
    width, height = struct.unpack(">II", header[16:24])
    if not 1 <= width <= 32768 or not 1 <= height <= 32768 or width * height > 100_000_000:
        raise ValueError("PNG dimensions outside supported bounds")
    return width, height


def reopen(root):
    record = load(local_file(root, "manifest.json"))
    if set(record) != {"schema", "tool", "id", "revision", "parent", "change", "files"} or record["schema"] != "dotsys.visual-kit/1" or record["tool"] not in {VERSION, "visual-concept-kit@1.0.0"}:
        raise ValueError("Unsupported manifest")
    if not isinstance(record["revision"], int) or record["revision"] < 1:
        raise ValueError("Invalid revision")
    expected = {"brief.json", "brief.md", "sheet.html", "sheet.css", "concept.png"}
    if set(record["files"]) != expected:
        raise ValueError("Incomplete artifact")
    for relative, expected_hash in record["files"].items():
        if digest(local_file(root, relative)) != expected_hash:
            raise ValueError("Hash mismatch: " + relative)
    brief = load(root / "brief.json")
    validate(brief, legacy=record["tool"] == "visual-concept-kit@1.0.0")
    png_dimensions(local_file(root, "concept.png"))
    if brief["id"] != record["id"]:
        raise ValueError("Identity mismatch")
    return record, brief


def build(brief_path, image, output, parent=None, change=None):
    brief = load(brief_path)
    validate(brief)
    width, height = png_dimensions(image)
    lineage = None
    revision = 1
    if parent:
        record, previous = reopen(parent)
        if record["tool"] != VERSION:
            raise ValueError("Migrate the legacy brief to an independent 1.1 direction before a controlled remix")
        changed = {key for key in brief if brief[key] != previous[key]}
        if change != "chair_upholstery" or changed != {change}:
            raise ValueError("Controlled remix must change only chair_upholstery")
        if digest(image) == record["files"]["concept.png"]:
            raise ValueError("Remix requires a newly edited image, not the original")
        revision = record["revision"] + 1
        lineage = {"id": record["id"], "revision": record["revision"], "manifest_sha256": digest(parent / "manifest.json")}
    elif change:
        raise ValueError("A change requires a verified parent")
    output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(image, output / "concept.png")
    (output / "brief.json").write_text(json.dumps(brief, indent=2) + "\n")
    palette = brief["palette"] + [brief["chair_upholstery"]]
    groups = [("Materials", brief["materials"]), ("Light", brief["lighting"]), ("Keep this direction", brief["locked"])]
    markdown = ["# " + brief["title"], "", brief["intent"], "", "## Feel", *["- " + x for x in brief["qualities"]], "", "## Palette", *[f'- {p["name"]}: {p["color"]} — {p["role"]}' for p in palette]]
    for title, values in groups:
        markdown += ["", "## " + title, *["- " + x for x in values]]
    markdown += ["", "## Sources and rights", *[f'- {s["title"]} — {s["url"]}; {s["credit"]}; {s["rights"]}' for s in brief["sources"]], "", "Concept hypothesis. Not a built room or acoustic specification.", f"Produced with {VERSION}. Revision {revision}."]
    (output / "brief.md").write_text("\n".join(markdown) + "\n")
    sections = "".join(f'<section><h2>{title}</h2><ul>' + "".join(f"<li>{text(x)}</li>" for x in values) + "</ul></section>" for title, values in groups)
    swatches = "".join(f'<li><span class="swatch s{i}" aria-hidden="true"></span><strong>{text(p["name"])}</strong><code>{p["color"].upper()}</code><small>{text(p["role"])}</small></li>' for i, p in enumerate(palette))
    sources = "".join(f'<li><a href="{html.escape(s["url"], quote=True)}">{text(s["title"])}</a> — {text(s["credit"])}. {text(s["rights"])}</li>' for s in brief["sources"])
    lineage_text = f'Revision {revision} · ' + ("Controlled variation: chair upholstery only" if parent else "Original direction")
    image_alt = text(brief["image_description"].replace("{chair_upholstery}", brief["chair_upholstery"]["name"]))
    sheet = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{text(brief["title"])} · Direction sheet</title><link rel="stylesheet" href="sheet.css"></head><body>
<a class="skip" href="#main">Skip to direction</a><main id="main"><header><p class="eyebrow">DOTSYS / VISUAL CONCEPT KIT / 01</p><h1>{text(brief["title"])}</h1><p class="intent">{text(brief["intent"])}</p><p class="meta">{lineage_text}</p></header>
<figure><img src="concept.png" width="{width}" height="{height}" alt="{image_alt}"><figcaption>Visual hypothesis · {" / ".join(text(x) for x in brief["qualities"])}</figcaption></figure>
<section class="palette"><h2>Color, with a purpose.</h2><ul>{swatches}</ul></section><div class="decisions">{sections}</div>
<section class="sources"><h2>References &amp; authorship</h2><ul>{sources}</ul></section><footer><p>Concept direction only. Not a built interior, acoustic design or product endorsement.</p><nav aria-label="Editable files"><a href="brief.json" download>Editable brief (.json)</a><a href="brief.md" download>Readable brief (.md)</a><a href="manifest.json">Hashes &amp; parent credit</a></nav><p>{VERSION} · Save the whole folder, reopen sheet.html, verify with kit.py reopen.</p></footer></main></body></html>'''
    (output / "sheet.html").write_text(sheet)
    css = '''*{box-sizing:border-box}body{margin:0;background:#f6f0e5;color:#1c3444;font:16px/1.65 Arial,sans-serif}main{max-width:1180px;margin:auto;padding:64px 48px}header{max-width:850px;padding-bottom:32px}.eyebrow{font-size:11px;letter-spacing:.16em;color:#476c5b}h1,h2{font-family:Georgia,serif;font-weight:400;line-height:1.1}h1{font-size:clamp(44px,6vw,76px);letter-spacing:-.045em;margin:20px 0}h2{font-size:30px;margin:0 0 22px}.intent{font-size:20px;max-width:680px}.meta,figcaption,small{color:#53645f;font-size:13px}figure{margin:0 0 48px}img{display:block;width:100%;height:auto;border-radius:3px}figcaption{padding-top:12px}.palette ul{display:grid;grid-template-columns:repeat(5,1fr);gap:18px;list-style:none;padding:0}.palette li{display:flex;flex-direction:column}.swatch{height:70px;border:1px solid #1c34441c;margin-bottom:12px;border-radius:3px}code{font-size:12px;padding:4px 0}.decisions{display:grid;grid-template-columns:repeat(3,1fr);gap:36px;border-block:1px solid #cbd1c3;margin:44px 0;padding:36px 0}.decisions ul,.sources ul{padding-left:18px}li{margin-bottom:10px}.sources{max-width:850px;font-size:14px}.sources a,a{color:inherit;text-underline-offset:4px;overflow-wrap:anywhere}footer{margin-top:40px;font-size:12px;color:#53645f}nav{display:flex;flex-wrap:wrap;gap:22px;margin:24px 0}a:focus-visible{outline:3px solid #bc6c41;outline-offset:5px}.skip{position:absolute;top:-100px}.skip:focus{top:10px}@media(max-width:700px){main{padding:32px 22px}.palette ul{grid-template-columns:repeat(2,1fr)}.decisions{grid-template-columns:1fr;gap:24px}.intent{font-size:18px}h2{font-size:28px}}@media print{main{padding:0}body{background:white}.skip{display:none}figure{break-inside:avoid}.decisions{break-inside:avoid}a{color:#1c3444}}'''
    css += "".join(f'.s{i}{{background:{p["color"]}}}' for i, p in enumerate(palette))
    (output / "sheet.css").write_text(css + "\n")
    files = {p.name: digest(p) for p in sorted(output.iterdir())}
    record = {"schema": "dotsys.visual-kit/1", "tool": VERSION, "id": brief["id"], "revision": revision, "parent": lineage, "change": change, "files": files}
    (output / "manifest.json").write_text(json.dumps(record, indent=2) + "\n")
    return reopen(output)[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("build")
    create.add_argument("brief", type=Path)
    create.add_argument("--image", type=Path, required=True)
    create.add_argument("--out", type=Path, required=True)
    create.add_argument("--parent", type=Path)
    create.add_argument("--change", choices=["chair_upholstery"])
    verify = commands.add_parser("reopen")
    verify.add_argument("folder", type=Path)
    args = parser.parse_args()
    try:
        record = reopen(args.folder)[0] if args.command == "reopen" else build(args.brief, args.image, args.out, args.parent, args.change)
        print(json.dumps({"verified": True, "id": record["id"], "revision": record["revision"], "tool": record["tool"], "files": record["files"], "parent": record["parent"]}, indent=2))
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(1, "Kit error: " + str(error) + "\n")


if __name__ == "__main__":
    main()
