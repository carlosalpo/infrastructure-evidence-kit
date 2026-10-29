"""Run installed CLI scenarios and retain reproducible results."""

import argparse
import json
import shutil
import subprocess
from pathlib import Path

CASES = {
    "complete": (0, {"collected": 4}),
    "gaps": (1, {"collected": 1, "missing": 1, "stale": 1, "failed": 1}),
    "latest-failed": (1, {"collected": 3, "failed": 1}),
    "missing-file": (1, {"collected": 3, "missing": 1}),
    "empty-file": (1, {"collected": 3, "empty": 1}),
    "invalid-path": (2, None),
}


def run(command, output):
    result = subprocess.run(command, capture_output=True, text=True)
    output.with_suffix(".stdout.txt").write_text(result.stdout)
    output.with_suffix(".stderr.txt").write_text(result.stderr)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[1]
    results = []
    for name, (expected, counts) in CASES.items():
        target = args.output / name
        result = run(
            [
                "iek",
                "build",
                "--input",
                str(root / "examples" / f"{name}.json"),
                "--evidence-root",
                str(root / "examples/evidence"),
                "--output",
                str(target),
            ],
            args.output / f"{name}-build",
        )
        assert result.returncode == expected, (name, result.stderr)
        if counts is None:
            assert not target.exists()
        else:
            index = json.loads((target / "index.json").read_text())
            assert index["summary"]["statuses"] == counts, name
            checked = run(
                ["iek", "verify", "--bundle", str(target)], args.output / f"{name}-verify"
            )
            assert checked.returncode == 0, checked.stderr
            assert json.loads(checked.stdout)["valid"]
        results.append(
            {
                "case": name,
                "expected_exit": expected,
                "actual_exit": result.returncode,
                "verified": True,
            }
        )
        print(f"PASS {name}: build exit {expected}; expected coverage verified")

    target = args.output / "tampered"
    shutil.copytree(args.output / "complete", target)
    with (target / "evidence/route-export.txt").open("ab") as handle:
        handle.write(b"DELIBERATE DEMONSTRATION MODIFICATION\n")
    result = run(["iek", "verify", "--bundle", str(target)], args.output / "tampered-verify")
    assert result.returncode == 1
    assert not json.loads(result.stdout)["valid"]
    results.append({"case": "tampered", "expected_exit": 1, "actual_exit": 1, "verified": True})
    print("PASS tampered: verify exit 1; changed evidence detected")

    target = args.output / "historical-lab"
    result = run(
        [
            "iek",
            "build",
            "--input",
            str(root / "examples/historical-lab/assessment.json"),
            "--evidence-root",
            str(root / "examples/historical-lab/evidence"),
            "--output",
            str(target),
        ],
        args.output / "historical-lab-build",
    )
    assert result.returncode == 0, result.stderr
    index = json.loads((target / "index.json").read_text())
    assert index["summary"]["statuses"] == {"collected": 3}
    checked = run(["iek", "verify", "--bundle", str(target)], args.output / "historical-lab-verify")
    assert checked.returncode == 0
    results.append(
        {"case": "historical-lab", "expected_exit": 0, "actual_exit": 0, "verified": True}
    )
    print("PASS historical-lab: build and verify exit 0; archived public records bundled")
    (args.output / "summary.json").write_text(json.dumps(results, indent=2) + "\n")


if __name__ == "__main__":
    main()
