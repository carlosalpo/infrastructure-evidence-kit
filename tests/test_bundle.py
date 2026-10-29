import copy
import csv
import io
import json
import os

import pytest

from evidencekit.bundle import build
from evidencekit.model import InputError, digest

SOURCE_HASH = "a" * 64


def status(index, asset="router-edge", requirement="routing"):
    return next(
        c
        for c in index["coverage"]
        if c["asset_id"] == asset and c["requirement_id"] == requirement
    )


def test_complete_bundle_and_manual_finding(assessment, evidence_root):
    files, index = build(assessment, SOURCE_HASH, evidence_root)
    assert index["result"] == "evidence-complete"
    assert index["summary"]["collected"] == index["summary"]["checks"] == 4
    assert index["findings"][0]["support"] == "attached"
    assert files["evidence/route-export.txt"] == (evidence_root / "routing.txt").read_bytes()
    manifest = json.loads(files["manifest.json"])
    assert set(manifest["files"]) == set(files) - {"manifest.json"}
    for name, metadata in manifest["files"].items():
        assert digest(files[name]) == metadata["sha256"]
        assert len(files[name]) == metadata["bytes"]


@pytest.mark.parametrize(
    "collected,expected", [("2026-10-28T18:00:00Z", "collected"), ("2026-10-28T17:59:59Z", "stale")]
)
def test_age_boundary(assessment, evidence_root, collected, expected):
    assessment["evidence"][0]["collected_at"] = collected
    _, index = build(assessment, SOURCE_HASH, evidence_root)
    assert status(index)["status"] == expected


def test_new_failed_attempt_never_falls_back(assessment, evidence_root):
    latest = dict(
        assessment["evidence"][0],
        id="latest",
        collected_at="2026-10-29T17:30:00Z",
        exit_code=1,
        path="routing-failed.txt",
    )
    assessment["evidence"].append(latest)
    _, index = build(assessment, SOURCE_HASH, evidence_root)
    assert status(index)["status"] == "failed"
    assert status(index)["evidence_id"] == "latest"
    assert index["result"] == "evidence-gaps"


def test_new_missing_attempt_never_falls_back(assessment, evidence_root):
    assessment["evidence"].append(
        dict(
            assessment["evidence"][0],
            id="latest",
            collected_at="2026-10-29T17:30:00Z",
            path="missing.txt",
        )
    )
    _, index = build(assessment, SOURCE_HASH, evidence_root)
    assert status(index)["status"] == "missing"
    assert status(index)["evidence_id"] == "latest"


def test_no_record_is_missing(assessment, evidence_root):
    assessment["evidence"] = [r for r in assessment["evidence"] if r["id"] != "route-export"]
    _, index = build(assessment, SOURCE_HASH, evidence_root)
    assert status(index)["status"] == "missing"
    assert status(index)["evidence_id"] is None


def test_missing_file_marks_finding_incomplete(assessment, evidence_root):
    (evidence_root / "capacity.json").unlink()
    files, index = build(assessment, SOURCE_HASH, evidence_root)
    assert index["findings"][0]["support"] == "incomplete"
    assert "evidence/capacity-export.txt" not in files
    assert index["result"] == "evidence-gaps"


@pytest.mark.parametrize("raw", [b"", b" \n\t", "\u2003".encode(), b"\xef\xbb\xbf \n"])
def test_empty_exports(assessment, evidence_root, raw):
    (evidence_root / "routing.txt").write_bytes(raw)
    _, index = build(assessment, SOURCE_HASH, evidence_root)
    assert status(index)["status"] == "empty"


def test_failed_precedes_empty_and_stale(assessment, evidence_root):
    assessment["evidence"][0].update(
        exit_code=1, path="empty.txt", collected_at="2026-10-01T00:00:00Z"
    )
    _, index = build(assessment, SOURCE_HASH, evidence_root)
    assert status(index)["status"] == "failed"


def test_severity_is_not_an_automatic_health_verdict(assessment, evidence_root):
    assessment["findings"][0]["severity"] = "critical"
    _, index = build(assessment, SOURCE_HASH, evidence_root)
    assert index["result"] == "evidence-complete"
    assert index["scope"] == "collection-coverage-only"


def test_reordered_input_is_deterministic(assessment, evidence_root):
    original = copy.deepcopy(assessment)
    before, _ = build(assessment, SOURCE_HASH, evidence_root)
    assert assessment == original
    for key in ("assets", "requirements", "evidence", "findings"):
        assessment[key].reverse()
    after, _ = build(assessment, SOURCE_HASH, evidence_root)
    assert before == after


def test_markdown_injection_escaped(assessment, evidence_root):
    assessment["title"] = "<script>alert(1)</script> [click](https://example.test)"
    assessment["assets"][0]["label"] = "label | injected"
    files, _ = build(assessment, SOURCE_HASH, evidence_root)
    report = files["report.md"].decode()
    assert "<script>" not in report
    assert "[click](https://example.test)" not in report
    assert "label \\| injected" in report


@pytest.mark.parametrize("label", ["=1+1", "+1+1", "-1+1", "@SUM(A1)", "  =1+1"])
def test_csv_formula_guard(assessment, evidence_root, label):
    assessment["assets"][0]["label"] = label
    files, _ = build(assessment, SOURCE_HASH, evidence_root)
    rows = list(csv.DictReader(io.StringIO(files["coverage.csv"].decode())))
    assert all(r["asset_label"] == "'" + label for r in rows if r["asset_id"] == "router-edge")


def test_evidence_is_preserved_not_redacted(assessment, evidence_root):
    raw = b"PRIVATE_TEST_SENTINEL\r\n"
    (evidence_root / "routing.txt").write_bytes(raw)
    files, _ = build(assessment, SOURCE_HASH, evidence_root)
    assert files["evidence/route-export.txt"] == raw
    assert raw.strip() not in files["report.md"]


def test_symlink_file_rejected(assessment, evidence_root, tmp_path):
    target = evidence_root / "routing.txt"
    target.unlink()
    outside = tmp_path / "outside"
    outside.write_text("outside")
    target.symlink_to(outside)
    with pytest.raises(InputError):
        build(assessment, SOURCE_HASH, evidence_root)


def test_symlink_directory_rejected(assessment, evidence_root, tmp_path):
    (evidence_root / "escape").symlink_to(tmp_path, target_is_directory=True)
    (tmp_path / "outside.txt").write_text("outside")
    assessment["evidence"][0]["path"] = "escape/outside.txt"
    with pytest.raises(InputError):
        build(assessment, SOURCE_HASH, evidence_root)


def test_fifo_rejected_without_blocking(assessment, evidence_root):
    path = evidence_root / "routing.txt"
    path.unlink()
    os.mkfifo(path)
    with pytest.raises(InputError):
        build(assessment, SOURCE_HASH, evidence_root)


def test_missing_root_is_input_error(assessment, tmp_path):
    with pytest.raises(InputError):
        build(assessment, SOURCE_HASH, tmp_path / "missing-root")


def test_non_utf8_rejected(assessment, evidence_root):
    (evidence_root / "routing.txt").write_bytes(b"\xff")
    with pytest.raises(InputError):
        build(assessment, SOURCE_HASH, evidence_root)


def test_oversized_file_rejected(assessment, evidence_root):
    (evidence_root / "routing.txt").write_bytes(b"a" * 1_000_001)
    with pytest.raises(InputError):
        build(assessment, SOURCE_HASH, evidence_root)


def test_total_evidence_limit(assessment, evidence_root):
    (evidence_root / "routing.txt").write_bytes(b"a" * 1_000_000)
    for i in range(1, 17):
        assessment["evidence"].append(
            dict(
                assessment["evidence"][0],
                id=f"history-{i}",
                collected_at=f"2026-10-28T00:{i:02}:00Z",
            )
        )
    with pytest.raises(InputError, match="Total selected"):
        build(assessment, SOURCE_HASH, evidence_root)


def test_nul_export_rejected(assessment, evidence_root):
    (evidence_root / "routing.txt").write_bytes(b"binary\x00content")
    with pytest.raises(InputError, match="NUL"):
        build(assessment, SOURCE_HASH, evidence_root)


def test_nested_regular_export_allowed(assessment, evidence_root):
    folder = evidence_root / "nested"
    folder.mkdir()
    (folder / "route.txt").write_text("nested observation\n")
    assessment["evidence"][0]["path"] = "nested/route.txt"
    files, index = build(assessment, SOURCE_HASH, evidence_root)
    assert files["evidence/route-export.txt"] == b"nested observation\n"
    assert status(index)["status"] == "collected"
