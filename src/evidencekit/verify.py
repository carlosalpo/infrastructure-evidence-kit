"""Verify internal file-set and byte integrity, never authenticity."""

import os
import re
import stat

from . import __version__
from .files import SizeLimitError, read_beneath
from .model import InputError, digest, fields, identifier, parse_json, timestamp

REQUIRED = {"assessment.json", "index.json", "coverage.csv", "report.md"}
HASH = re.compile(r"[a-f0-9]{64}\Z")
EVIDENCE = re.compile(r"evidence/[a-z][a-z0-9-]{0,47}\.txt\Z")
MAX_ARTIFACT = 8_000_000
MAX_BUNDLE = 48_000_000


def check_manifest(manifest):
    fields(
        manifest,
        "schema_version tool version assessment_id as_of result input_sha256 "
        "canonical_sha256 files",
        "manifest",
    )
    if type(manifest["schema_version"]) is not int or manifest["schema_version"] != 1:
        raise InputError("Unsupported bundle schema version.")
    if manifest["tool"] != "infrastructure-evidence-kit" or manifest["version"] != __version__:
        raise InputError("Unsupported bundle tool or version.")
    identifier(manifest["assessment_id"], "manifest.assessment_id")
    timestamp(manifest["as_of"])
    if manifest["result"] not in ("evidence-complete", "evidence-gaps"):
        raise InputError("Unsupported bundle result.")
    for key in ("input_sha256", "canonical_sha256"):
        if not isinstance(manifest[key], str) or not HASH.fullmatch(manifest[key]):
            raise InputError("Manifest hashes must be lowercase SHA-256 strings.")
    files = manifest["files"]
    if not isinstance(files, dict) or not 4 <= len(files) <= 260 or not REQUIRED <= set(files):
        raise InputError("Manifest must declare the four core artifacts and at most 256 exports.")
    total = 0
    for name, metadata in files.items():
        if name not in REQUIRED and not EVIDENCE.fullmatch(name):
            raise InputError("Manifest contains an unsupported artifact path.")
        fields(metadata, "sha256 bytes", "manifest artifact")
        if not isinstance(metadata["sha256"], str) or not HASH.fullmatch(metadata["sha256"]):
            raise InputError("Artifact hash must be a lowercase SHA-256 string.")
        if type(metadata["bytes"]) is not int or not 0 <= metadata["bytes"] <= MAX_ARTIFACT:
            raise InputError("Invalid artifact size.")
        total += metadata["bytes"]
    if total > MAX_BUNDLE:
        raise InputError("Declared bundle exceeds the verification size limit.")
    if files["assessment.json"]["sha256"] != manifest["canonical_sha256"]:
        raise InputError("Canonical assessment hash disagrees with its artifact hash.")


def inventory(root):
    files = set()
    if not stat.S_ISDIR(root.lstat().st_mode):
        raise InputError("Bundle root must be a real directory, not a symlink.")
    with os.scandir(root) as entries:
        for count, entry in enumerate(entries, 1):
            if count > 270:
                raise InputError("Bundle contains unexpected top-level entries.")
            if entry.name == "evidence" and entry.is_dir(follow_symlinks=False):
                with os.scandir(entry.path) as children:
                    for child_count, child in enumerate(children, 1):
                        if child_count > 256 or not child.is_file(follow_symlinks=False):
                            raise InputError("Evidence directory contains unsupported entries.")
                        files.add("evidence/" + child.name)
            elif entry.is_file(follow_symlinks=False):
                files.add(entry.name)
            else:
                raise InputError("Bundle contains a symlink or unsupported filesystem entry.")
    return files


def verify(root):
    try:
        raw = read_beneath(root, "manifest.json")
    except FileNotFoundError:
        return {
            "valid": False,
            "scope": "file-integrity-only",
            "checked_files": 0,
            "issues": ["Bundle or completion manifest is missing."],
        }
    manifest = parse_json(raw)
    check_manifest(manifest)
    actual = inventory(root)
    expected = set(manifest["files"]) | {"manifest.json"}
    issues = []
    if actual != expected:
        issues.append("Bundle file set differs from the manifest (missing or extra artifacts).")
    checked = 0
    for name, metadata in manifest["files"].items():
        try:
            content = read_beneath(root, name, metadata["bytes"])
        except FileNotFoundError:
            issues.append(f"Artifact is missing at verification time: {name}.")
            continue
        except SizeLimitError:
            checked += 1
            issues.append(f"Artifact bytes or hash mismatch: {name}.")
            continue
        checked += 1
        if len(content) != metadata["bytes"] or digest(content) != metadata["sha256"]:
            issues.append(f"Artifact bytes or hash mismatch: {name}.")
    return {
        "valid": not issues,
        "scope": "file-integrity-only",
        "checked_files": checked,
        "issues": issues,
    }
