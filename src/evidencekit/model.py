"""Strict assessment input and bounded JSON helpers."""

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

MAX_JSON = 1_000_000
ID = re.compile(r"[a-z][a-z0-9-]{0,47}\Z")
SEGMENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}\Z")
KINDS = ("network", "compute", "storage")


class InputError(ValueError):
    """Invalid or unsupported input, with bounded explanations."""


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode()


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InputError("Duplicate JSON keys are not accepted.")
        result[key] = value
    return result


def _constant(value):
    raise InputError("Non-finite numbers are not accepted.")


def parse_json(raw):
    if len(raw) > MAX_JSON:
        raise InputError("JSON exceeds the 1,000,000-byte limit.")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_constant)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise InputError(
            "Expected bounded UTF-8 JSON with unique keys and finite numbers."
        ) from exc
    pending = [(value, 0)]
    while pending:
        current, depth = pending.pop()
        if depth > 32:
            raise InputError("JSON nesting exceeds 32 levels.")
        if isinstance(current, (list, dict)):
            children = current.values() if isinstance(current, dict) else current
            pending.extend((child, depth + 1) for child in children)
    return value


def load(path: Path):
    with path.open("rb") as handle:
        raw = handle.read(MAX_JSON + 1)
    data = parse_json(raw)
    validate(data)
    return canonical(data), digest(raw)


def fields(value, keys, location):
    if not isinstance(value, dict) or set(value) != set(keys.split()):
        raise InputError(f"{location}: fields must match the specification exactly.")


def identifier(value, location):
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise InputError(
            f"{location}: use a lowercase letter and up to 47 letters, digits or hyphens."
        )


def text(value, location, maximum=200):
    if not isinstance(value, str) or not 1 <= len(value) <= maximum or not value.isprintable():
        raise InputError(f"{location}: expected 1..{maximum} printable characters on one line.")


def items(value, location, minimum=0, maximum=128):
    if not isinstance(value, list) or not minimum <= len(value) <= maximum:
        raise InputError(f"{location}: expected {minimum}..{maximum} list items.")
    return value


def timestamp(value):
    if not isinstance(value, str) or not re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", value
    ):
        raise InputError("Timestamps must use UTC YYYY-MM-DDTHH:MM:SSZ.")
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise InputError("Timestamp has an invalid calendar date or time.") from exc


def relative_path(value):
    if not isinstance(value, str) or len(value) > 240:
        raise InputError("Evidence path must be a bounded relative path.")
    parts = value.split("/")
    if not 1 <= len(parts) <= 8 or any(not SEGMENT.fullmatch(part) for part in parts):
        raise InputError(
            "Evidence paths require plain relative components; no traversal or dotfiles."
        )
    return parts


def index(values, location):
    result = {}
    for value in values:
        identifier(value["id"], location)
        if value["id"] in result:
            raise InputError(f"{location}: IDs must be unique within this collection.")
        result[value["id"]] = value
    return result


def validate(data):
    fields(
        data, "schema_version id title as_of assets requirements evidence findings", "assessment"
    )
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise InputError("schema_version must be integer 1.")
    identifier(data["id"], "assessment.id")
    text(data["title"], "assessment.title")
    as_of = timestamp(data["as_of"])
    for asset in items(data["assets"], "assets", 1):
        fields(asset, "id label kind", "asset")
        text(asset["label"], "asset.label")
        if asset["kind"] not in KINDS:
            raise InputError("asset.kind must be network, compute or storage.")
    assets = index(data["assets"], "assets")
    for req in items(data["requirements"], "requirements", 1, 64):
        fields(req, "id title asset_kind max_age_hours", "requirement")
        text(req["title"], "requirement.title")
        if req["asset_kind"] not in KINDS:
            raise InputError("requirement.asset_kind must be network, compute or storage.")
        if type(req["max_age_hours"]) is not int or not 1 <= req["max_age_hours"] <= 87600:
            raise InputError("requirement.max_age_hours must be integer 1..87600.")
    requirements = index(data["requirements"], "requirements")
    if not {a["kind"] for a in assets.values()} <= {r["asset_kind"] for r in requirements.values()}:
        raise InputError("Every asset kind must have at least one declared evidence requirement.")
    seen_times = set()
    for record in items(data["evidence"], "evidence", maximum=256):
        fields(record, "id asset_id requirement_id path collected_at exit_code", "evidence record")
        identifier(record["asset_id"], "evidence.asset_id")
        identifier(record["requirement_id"], "evidence.requirement_id")
        asset = assets.get(record["asset_id"])
        req = requirements.get(record["requirement_id"])
        if not asset or not req or asset["kind"] != req["asset_kind"]:
            raise InputError(
                "Evidence must reference an existing asset and applicable requirement."
            )
        relative_path(record["path"])
        if timestamp(record["collected_at"]) > as_of:
            raise InputError("Evidence cannot be dated after the assessment as_of time.")
        key = (record["asset_id"], record["requirement_id"], record["collected_at"])
        if key in seen_times:
            raise InputError("Evidence for the same asset/requirement cannot have tied timestamps.")
        seen_times.add(key)
        if type(record["exit_code"]) is not int or not 0 <= record["exit_code"] <= 255:
            raise InputError("evidence.exit_code must be integer 0..255.")
    records = index(data["evidence"], "evidence")
    for finding in items(data["findings"], "findings"):
        fields(
            finding, "id asset_id severity title observation recommendation evidence_ids", "finding"
        )
        identifier(finding["asset_id"], "finding.asset_id")
        if finding["asset_id"] not in assets:
            raise InputError("Finding asset does not exist.")
        if finding["severity"] not in ("info", "low", "medium", "high", "critical"):
            raise InputError("Finding severity must be info, low, medium, high or critical.")
        text(finding["title"], "finding.title")
        text(finding["observation"], "finding.observation", 1000)
        text(finding["recommendation"], "finding.recommendation", 1000)
        ids = items(finding["evidence_ids"], "finding.evidence_ids", 1, 32)
        for eid in ids:
            identifier(eid, "finding.evidence_ids[]")
            if eid not in records or records[eid]["asset_id"] != finding["asset_id"]:
                raise InputError("Finding evidence must exist and refer to the same asset.")
        if len(set(ids)) != len(ids):
            raise InputError("Finding evidence IDs must not repeat.")
    index(data["findings"], "findings")


def canonical(data):
    result = json.loads(json_bytes(data))
    for key in ("assets", "requirements", "evidence", "findings"):
        result[key].sort(key=lambda obj: obj["id"])
    for finding in result["findings"]:
        finding["evidence_ids"].sort()
    return result
