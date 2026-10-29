"""Assessment coverage and deterministic evidence bundle generation."""

import csv
import html
import io
import re
from collections import Counter

from . import __version__
from .files import read_evidence
from .model import canonical, digest, json_bytes, timestamp, validate


def assess(data, content):
    requirements = {r["id"]: r for r in data["requirements"]}
    as_of = timestamp(data["as_of"])
    records, latest = [], {}
    for record in data["evidence"]:
        raw = content[record["id"]]
        age = int((as_of - timestamp(record["collected_at"])).total_seconds())
        if raw is None:
            status = "missing"
        elif record["exit_code"] != 0:
            status = "failed"
        elif not raw.decode("utf-8-sig").strip():
            status = "empty"
        elif age > requirements[record["requirement_id"]]["max_age_hours"] * 3600:
            status = "stale"
        else:
            status = "collected"
        entry = dict(
            record,
            status=status,
            age_seconds=age,
            bundle_path=f"evidence/{record['id']}.txt" if raw is not None else None,
            sha256=digest(raw) if raw is not None else None,
            bytes=len(raw) if raw is not None else None,
        )
        records.append(entry)
        pair = (record["asset_id"], record["requirement_id"])
        if pair not in latest or record["collected_at"] > latest[pair]["collected_at"]:
            latest[pair] = entry
    coverage = []
    for asset in data["assets"]:
        for req in data["requirements"]:
            if asset["kind"] != req["asset_kind"]:
                continue
            record = latest.get((asset["id"], req["id"]))
            coverage.append(
                {
                    "asset_id": asset["id"],
                    "asset_label": asset["label"],
                    "requirement_id": req["id"],
                    "requirement_title": req["title"],
                    "max_age_hours": req["max_age_hours"],
                    "status": record["status"] if record else "missing",
                    "evidence_id": record["id"] if record else None,
                    "age_seconds": record["age_seconds"] if record else None,
                }
            )
    record_index = {record["id"]: record for record in records}
    findings = []
    for finding in data["findings"]:
        attached = all(
            content[eid] is not None and content[eid].decode("utf-8-sig").strip()
            for eid in finding["evidence_ids"]
        )
        findings.append(
            dict(
                finding,
                support="attached" if attached else "incomplete",
                evidence_statuses={
                    eid: record_index[eid]["status"] for eid in finding["evidence_ids"]
                },
            )
        )
    counts = dict(sorted(Counter(check["status"] for check in coverage).items()))
    complete = all(c["status"] == "collected" for c in coverage) and all(
        f["support"] == "attached" for f in findings
    )
    return {
        "schema_version": 1,
        "assessment_id": data["id"],
        "as_of": data["as_of"],
        "result": "evidence-complete" if complete else "evidence-gaps",
        "scope": "collection-coverage-only",
        "summary": {
            "assets": len(data["assets"]),
            "checks": len(coverage),
            "collected": counts.get("collected", 0),
            "statuses": counts,
            "manual_findings": len(findings),
        },
        "coverage": coverage,
        "evidence": records,
        "findings": findings,
    }


def md(value):
    value = html.escape(str(value), quote=False)
    return re.sub(r"([\\`*{}\[\]()#+.!_|-])", r"\\\1", value)


def csv_cell(value):
    if value is None:
        return ""
    value = str(value)
    # Spreadsheet apps may treat quoted CSV fields as formulas too.
    return "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) else value


def coverage_csv(index):
    output = io.StringIO(newline="")
    fields = [
        "asset_id",
        "asset_label",
        "requirement_id",
        "requirement_title",
        "status",
        "evidence_id",
        "age_seconds",
        "max_age_hours",
    ]
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows({key: csv_cell(row[key]) for key in fields} for row in index["coverage"])
    return output.getvalue().encode()


def report(data, index):
    summary = index["summary"]
    lines = [
        f"# {md(data['title'])}",
        "",
        "Infrastructure Evidence Kit — collection review",
        "",
        f"Assessment: `{data['id']}` · As of: `{data['as_of']}` · Tool: `{__version__}`",
        "",
        f"Result: **{index['result']}**",
        "",
        f"**{summary['collected']} / {summary['checks']} evidence checks collected**, "
        f"across {summary['assets']} assets. Manual findings: {summary['manual_findings']}.",
        "",
        "Collection coverage is not infrastructure health, compliance or proof of a claim. "
        "Timestamps and exit codes are supplied by the input author; the tool does not run "
        "commands or authenticate their origin.",
        "",
        "## Coverage",
        "",
        "The latest declared attempt wins for each asset/requirement. A newer failed, empty "
        "or missing attempt does not fall back to an older successful one.",
        "",
        "| Asset | Requirement | Status | Latest evidence | Age (seconds) | Max age (hours) |",
        "| --- | --- | --- | --- | ---: | ---: |",
    ]
    records = {r["id"]: r for r in index["evidence"]}
    for row in index["coverage"]:
        record = records.get(row["evidence_id"])
        link = "none"
        if record:
            link = (
                f"[{record['id']}]({record['bundle_path']})"
                if record["bundle_path"]
                else f"`{record['id']}` (file missing)"
            )
        lines.append(
            f"| {md(row['asset_label'])} (`{row['asset_id']}`) | "
            f"{md(row['requirement_title'])} | {row['status']} | {link} | "
            f"{row['age_seconds'] if row['age_seconds'] is not None else '—'} | "
            f"{row['max_age_hours']} |"
        )
    lines += [
        "",
        "## Manual findings",
        "",
        "These are author-supplied observations. Attached evidence establishes a reference, "
        "not the truth, severity or validity of a conclusion.",
        "",
    ]
    if not index["findings"]:
        lines.append("No manual findings supplied. This does not imply a clean assessment.")
    for finding in index["findings"]:
        lines += [
            f"### {md(finding['title'])}",
            "",
            f"ID: `{finding['id']}` · Asset: `{finding['asset_id']}` · "
            f"Declared severity: **{finding['severity']}** · Support: **{finding['support']}**",
            "",
            md(finding["observation"]),
            "",
            f"Recommendation: {md(finding['recommendation'])}",
            "",
            "Evidence:",
        ]
        for eid in finding["evidence_ids"]:
            record = records[eid]
            link = f"[{eid}]({record['bundle_path']})" if record["bundle_path"] else f"`{eid}`"
            lines.append(f"- {link} · {record['status']} · collected `{record['collected_at']}`")
        lines.append("")
    lines += [
        "",
        "## Evidence inventory",
        "",
        "| ID | Asset | Requirement | Status | Bytes | SHA-256 |",
        "| --- | --- | --- | --- | ---: | --- |",
    ]
    for record in index["evidence"]:
        lines.append(
            f"| `{record['id']}` | `{record['asset_id']}` | `{record['requirement_id']}` | "
            f"{record['status']} | {record['bytes'] if record['bytes'] is not None else '—'} | "
            f"{record['sha256'] or 'not available'} |"
        )
    lines += [
        "",
        "## Integrity and handling",
        "",
        "Run `iek verify --bundle <directory>` before consuming a copied bundle. "
        "Verification checks file-set and hash consistency, not identity, authorship, "
        "collection time, device health or authenticity. The manifest is unsigned.",
        "",
        "Evidence files are copied byte for byte from explicit local inputs. "
        "This tool does not sanitize secrets or certify that a package is safe to publish. "
        "Review the actual files before sharing.",
        "",
    ]
    return "\n".join(lines).encode()


def build(data, source_hash, root):
    validate(data)
    data = canonical(data)
    content = read_evidence(root, data["evidence"])
    index = assess(data, content)
    files = {
        "assessment.json": json_bytes(data),
        "index.json": json_bytes(index),
        "coverage.csv": coverage_csv(index),
        "report.md": report(data, index),
    }
    for eid, raw in content.items():
        if raw is not None:
            files[f"evidence/{eid}.txt"] = raw
    manifest = {
        "schema_version": 1,
        "tool": "infrastructure-evidence-kit",
        "version": __version__,
        "assessment_id": data["id"],
        "as_of": data["as_of"],
        "result": index["result"],
        "input_sha256": source_hash,
        "canonical_sha256": digest(json_bytes(data)),
        "files": {
            name: {"sha256": digest(raw), "bytes": len(raw)} for name, raw in sorted(files.items())
        },
    }
    files["manifest.json"] = json_bytes(manifest)
    return files, index
