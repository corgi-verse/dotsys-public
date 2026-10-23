#!/usr/bin/env python3
"""Validate public creation submissions and curated registry. Does not execute artifacts."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
FIELDS = {"schema", "id", "title", "author", "tool", "artifact", "editable", "process", "license", "sources", "parent", "credits", "artifact_sha256", "use"}


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
    if not isinstance(value, str) or not value or Path(value).is_absolute() or ".." in Path(value).parts:
        raise ValueError("Use a safe repository-relative file path")
    target = root / value
    if target.is_symlink() or not target.is_file() or not target.resolve().is_relative_to(root.resolve()):
        raise ValueError("Missing or unsafe file: " + value)
    return target


def submission(root, record):
    if not isinstance(record, dict) or set(record) != FIELDS or record["schema"] != "dotsys.creation/1":
        raise ValueError("Unsupported submission fields/schema")
    if not re.fullmatch(r"[a-z][a-z0-9-]{2,63}", record["id"]):
        raise ValueError("Invalid id")
    for key in ("title", "author", "tool", "use"):
        if not isinstance(record[key], str) or not record[key].strip() or len(record[key]) > 2000:
            raise ValueError("Missing bounded text: " + key)
    if not re.search(r"@\d+\.\d+\.\d+$", record["tool"]):
        raise ValueError("Tool must identify an exact semantic version")
    for key in ("artifact", "editable", "process", "license"):
        file(root, record[key])
    if hashlib.sha256(file(root, record["artifact"]).read_bytes()).hexdigest() != record["artifact_sha256"]:
        raise ValueError("Artifact hash mismatch")
    for key in ("credits", "sources"):
        if not isinstance(record[key], list) or not record[key] or not all(isinstance(x, str) and x.strip() for x in record[key]):
            raise ValueError("Sources and credits must be explicit nonempty lists")
    if record["parent"] is not None and (not isinstance(record["parent"], str) or record["parent"] == record["id"]):
        raise ValueError("Invalid adaptation parent")
    return record


def registry(root):
    index = read(root / "creations/registry.json")
    if set(index) != {"schema", "entries"} or index["schema"] != "dotsys.exchange/1":
        raise ValueError("Unsupported registry")
    records = {}
    for entry in index["entries"]:
        if set(entry) != {"submission", "review"}:
            raise ValueError("Registry entry needs submission and review")
        record = submission(root, read(file(root, entry["submission"])))
        review = read(file(root, entry["review"]))
        if set(review) != {"status", "reviewer", "date", "scope", "checks", "artifact_sha256"} or review["status"] != "accepted":
            raise ValueError("Only accepted, reviewed entries may be curated")
        if review["artifact_sha256"] != record["artifact_sha256"] or not review["reviewer"] or not review["scope"]:
            raise ValueError("Review must bind exact artifact and reviewer/scope")
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
            print("PASS: curated entries, exact artifact reviews and parent credit: " + ", ".join(result))
    except (OSError, ValueError, TypeError, KeyError) as error:
        parser.exit(1, "Exchange error: " + str(error) + "\n")
