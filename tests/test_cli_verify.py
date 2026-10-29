import json
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from evidencekit.bundle import build
from evidencekit.cli import main, write_bundle
from evidencekit.model import InputError, digest, json_bytes
from evidencekit.verify import verify


@pytest.fixture
def bundle(assessment, evidence_root, tmp_path):
    files, _ = build(assessment, "a" * 64, evidence_root)
    output = tmp_path / "bundle"
    write_bundle(output, files)
    return output


def test_verify_complete_bundle(bundle):
    assert verify(bundle) == {
        "valid": True,
        "scope": "file-integrity-only",
        "checked_files": 8,
        "issues": [],
    }


def test_detect_changed_evidence(bundle):
    (bundle / "evidence/route-export.txt").write_text("changed")
    result = verify(bundle)
    assert not result["valid"]
    assert "mismatch" in result["issues"][0]


def test_verification_read_limit_uses_declared_size(bundle, monkeypatch):
    from evidencekit.files import read_beneath

    path = bundle / "evidence/route-export.txt"
    declared = path.stat().st_size
    path.write_bytes(b"x" * 1_000_001)
    limits = {}

    def bounded(root, name, maximum=1_000_000):
        limits[name] = maximum
        return read_beneath(root, name, maximum)

    monkeypatch.setattr("evidencekit.verify.read_beneath", bounded)
    assert not verify(bundle)["valid"]
    assert limits["evidence/route-export.txt"] == declared


@pytest.mark.parametrize("filename", ["evidence/route-export.txt", "index.json", "report.md"])
def test_detect_missing_artifact(bundle, filename):
    (bundle / filename).unlink()
    assert not verify(bundle)["valid"]


def test_extra_file_fails_verification(bundle):
    (bundle / "unexpected.txt").write_text("extra")
    assert not verify(bundle)["valid"]


def test_extra_nested_file_fails_verification(bundle):
    (bundle / "evidence/unexpected.txt").write_text("extra")
    assert not verify(bundle)["valid"]


def test_missing_manifest(bundle):
    (bundle / "manifest.json").unlink()
    assert not verify(bundle)["valid"]


def test_symlink_artifact_rejected(bundle, tmp_path):
    target = bundle / "report.md"
    target.unlink()
    outside = tmp_path / "outside"
    outside.write_text("outside")
    target.symlink_to(outside)
    with pytest.raises(InputError):
        verify(bundle)


def test_symlink_evidence_directory_rejected(bundle, tmp_path):
    import shutil

    shutil.rmtree(bundle / "evidence")
    (bundle / "evidence").symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(InputError):
        verify(bundle)


@pytest.mark.parametrize(
    "path",
    ["../../outside", "/etc/passwd", "evidence/../report.md", "evidence/.hidden.txt", "other.txt"],
)
def test_manifest_paths_are_untrusted(bundle, path):
    manifest_path = bundle / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["files"][path] = {"bytes": 0, "sha256": "a" * 64}
    manifest_path.write_bytes(json_bytes(manifest))
    with pytest.raises(InputError):
        verify(bundle)


@pytest.mark.parametrize("size", [True, -1, 8_000_001, "100"])
def test_manifest_sizes_are_strict(bundle, size):
    path = bundle / "manifest.json"
    manifest = json.loads(path.read_text())
    manifest["files"]["report.md"]["bytes"] = size
    path.write_bytes(json_bytes(manifest))
    with pytest.raises(InputError):
        verify(bundle)


def test_rewriting_manifest_is_not_authentication(bundle):
    content = b"changed deliberately\n"
    (bundle / "evidence/route-export.txt").write_bytes(content)
    path = bundle / "manifest.json"
    manifest = json.loads(path.read_text())
    manifest["files"]["evidence/route-export.txt"] = {
        "sha256": digest(content),
        "bytes": len(content),
    }
    path.write_bytes(json_bytes(manifest))
    # Integrity is internal consistency only. There is deliberately no signature claim.
    assert verify(bundle)["valid"]


def test_gap_bundle_can_have_valid_integrity(assessment, evidence_root, tmp_path):
    (evidence_root / "routing.txt").unlink()
    files, index = build(assessment, "a" * 64, evidence_root)
    assert index["result"] == "evidence-gaps"
    output = tmp_path / "gaps"
    write_bundle(output, files)
    assert verify(output)["valid"]


def test_cli_codes_and_no_overwrite(assessment, evidence_root, tmp_path, capsys):
    source = tmp_path / "input.json"
    source.write_bytes(json_bytes(assessment))
    output = tmp_path / "out"
    args = [
        "build",
        "--input",
        str(source),
        "--evidence-root",
        str(evidence_root),
        "--output",
        str(output),
    ]
    assert main(args) == 0
    assert "4/4 collected" in capsys.readouterr().out
    original = (output / "manifest.json").read_bytes()
    assert main(args) == 2
    assert (output / "manifest.json").read_bytes() == original
    assert main(["verify", "--bundle", str(output)]) == 0
    (output / "report.md").write_text("altered")
    assert main(["verify", "--bundle", str(output)]) == 1


def test_cli_gap_exit_one(assessment, evidence_root, tmp_path):
    (evidence_root / "routing.txt").unlink()
    path = tmp_path / "input.json"
    path.write_bytes(json_bytes(assessment))
    assert (
        main(
            [
                "build",
                "--input",
                str(path),
                "--evidence-root",
                str(evidence_root),
                "--output",
                str(tmp_path / "out"),
            ]
        )
        == 1
    )


def test_permissions(bundle):
    assert stat.S_IMODE(bundle.stat().st_mode) == 0o700
    for path in bundle.rglob("*"):
        assert stat.S_IMODE(path.stat().st_mode) == (0o700 if path.is_dir() else 0o600)


def test_partial_write_has_no_manifest(assessment, evidence_root, tmp_path, monkeypatch):
    import os

    original_open = os.open

    def fail(path, *args, **kwargs):
        if isinstance(path, Path) and path.name == "report.md":
            raise OSError("simulated write error")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr("evidencekit.cli.os.open", fail)
    source = tmp_path / "input.json"
    source.write_bytes(json_bytes(assessment))
    output = tmp_path / "partial"
    assert (
        main(
            [
                "build",
                "--input",
                str(source),
                "--evidence-root",
                str(evidence_root),
                "--output",
                str(output),
            ]
        )
        == 2
    )
    assert not (output / "manifest.json").exists()


def test_no_network_or_processes_during_build(assessment, evidence_root, tmp_path, monkeypatch):
    def deny(*args, **kwargs):
        pytest.fail("Unexpected network or process creation")

    monkeypatch.setattr("socket.socket", deny)
    monkeypatch.setattr("socket.create_connection", deny)
    monkeypatch.setattr("subprocess.Popen", deny)
    files, _ = build(assessment, "a" * 64, evidence_root)
    output = tmp_path / "offline"
    write_bundle(output, files)
    assert verify(output)["valid"]


def test_module_cli(bundle):
    result = subprocess.run(
        [sys.executable, "-m", "evidencekit.cli", "verify", "--bundle", str(bundle)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_io_error_omits_personal_path(tmp_path, capsys):
    assert (
        main(
            [
                "build",
                "--input",
                str(tmp_path / "private-client.json"),
                "--evidence-root",
                str(tmp_path),
                "--output",
                str(tmp_path / "output"),
            ]
        )
        == 2
    )
    assert "private-client" not in capsys.readouterr().err
