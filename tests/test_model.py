import copy
import json

import pytest

from evidencekit.model import MAX_JSON, InputError, load, parse_json, validate


def test_valid_model(assessment):
    validate(assessment)


@pytest.mark.parametrize("version", [True, 1.0, "1", 0, 2, None])
def test_strict_version(assessment, version):
    assessment["schema_version"] = version
    with pytest.raises(InputError):
        validate(assessment)


@pytest.mark.parametrize("name", ["", "UPPER", "../x", "a/b", "with space", "x\n", "a" * 49, 1])
def test_bad_identifier(assessment, name):
    assessment["id"] = name
    with pytest.raises(InputError):
        validate(assessment)


@pytest.mark.parametrize("value", ["", "a\nline", "x\x00", "a" * 201, None])
def test_bounded_single_line_text(assessment, value):
    assessment["title"] = value
    with pytest.raises(InputError):
        validate(assessment)


@pytest.mark.parametrize(
    "value",
    ["2026-10-29", "2026-10-29T18:00:00+00:00", "2026-02-30T18:00:00Z", "2026-10-29T18:00:60Z", 1],
)
def test_invalid_timestamps(assessment, value):
    assessment["as_of"] = value
    with pytest.raises(InputError):
        validate(assessment)


def test_future_record_rejected(assessment):
    assessment["evidence"][0]["collected_at"] = "2026-10-30T00:00:00Z"
    with pytest.raises(InputError, match="after"):
        validate(assessment)


@pytest.mark.parametrize("section", ["assets", "requirements", "evidence", "findings"])
def test_duplicate_ids(assessment, section):
    assessment[section].append(copy.deepcopy(assessment[section][0]))
    with pytest.raises(InputError):
        validate(assessment)


def test_tied_attempts_rejected(assessment):
    row = copy.deepcopy(assessment["evidence"][0])
    row["id"] = "different-id"
    assessment["evidence"].append(row)
    with pytest.raises(InputError, match="tied"):
        validate(assessment)


@pytest.mark.parametrize(
    "path",
    [
        "../secret",
        "/etc/passwd",
        "a/../../b",
        "a//b",
        "a/./b",
        "a\\b",
        ".hidden",
        "a/.hidden",
        "file://host/a",
        "a/",
        "a ",
        "a" * 241,
    ],
)
def test_path_boundaries(assessment, path):
    assessment["evidence"][0]["path"] = path
    with pytest.raises(InputError):
        validate(assessment)


@pytest.mark.parametrize("exit_code", [True, -1, 256, "0", 0.0])
def test_exit_code_types(assessment, exit_code):
    assessment["evidence"][0]["exit_code"] = exit_code
    with pytest.raises(InputError):
        validate(assessment)


@pytest.mark.parametrize("age", [True, 0, -1, 87601, "24"])
def test_max_age_types(assessment, age):
    assessment["requirements"][0]["max_age_hours"] = age
    with pytest.raises(InputError):
        validate(assessment)


def test_unknown_fields_never_silently_ignored(assessment):
    assessment["secret"] = "PRIVATE_TEST_SENTINEL"
    with pytest.raises(InputError) as error:
        validate(assessment)
    assert "PRIVATE_TEST_SENTINEL" not in str(error.value)


def test_asset_without_applicable_requirement(assessment):
    assessment["requirements"] = [assessment["requirements"][0]]
    with pytest.raises(InputError, match="Every asset"):
        validate(assessment)


@pytest.mark.parametrize(
    "key,value",
    [("asset_id", "missing"), ("requirement_id", "missing"), ("requirement_id", "capacity")],
)
def test_record_references(assessment, key, value):
    assessment["evidence"][0][key] = value
    with pytest.raises(InputError):
        validate(assessment)


@pytest.mark.parametrize(
    "ids", [["missing"], ["route-export"], ["capacity-export", "capacity-export"], []]
)
def test_finding_references_same_asset(assessment, ids):
    assessment["findings"][0]["evidence_ids"] = ids
    with pytest.raises(InputError):
        validate(assessment)


@pytest.mark.parametrize(
    "raw",
    [
        b'{"a":1,"a":2}',
        b'{"a":NaN}',
        b'{"a":Infinity}',
        b'{"a":-Infinity}',
        b"\xff",
        b"{",
        b"[" * 2000 + b"]" * 2000,
    ],
)
def test_malformed_json(raw):
    with pytest.raises(InputError):
        parse_json(raw)


def test_load_size_limit(tmp_path):
    source = tmp_path / "large.json"
    source.write_bytes(b" " * (MAX_JSON + 1))
    with pytest.raises(InputError):
        load(source)


def test_collection_bounds(assessment):
    assessment["assets"] *= 43
    with pytest.raises(InputError):
        validate(assessment)


def test_missing_field(assessment):
    del assessment["evidence"][0]["path"]
    with pytest.raises(InputError):
        validate(assessment)


def test_original_source_hash(assessment, tmp_path):
    from evidencekit.model import digest

    raw = (json.dumps(assessment, indent=4) + "\r\n").encode()
    path = tmp_path / "assessment.json"
    path.write_bytes(raw)
    _, source_hash = load(path)
    assert source_hash == digest(raw)
