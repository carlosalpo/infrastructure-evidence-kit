# Assessment input — schema version 1

Use UTF-8 JSON without a BOM, unique keys, no non-finite numbers and at most 1,000,000 bytes / 32 nesting levels. All fields below are required; unknown fields and implicit type coercion are rejected.

IDs use a lowercase ASCII letter followed by up to 47 lowercase letters, digits or hyphens. Labels/titles contain 1–200 printable characters on one line. Observations/recommendations allow up to 1,000. Timestamps use exact UTC `YYYY-MM-DDTHH:MM:SSZ`, without fractional seconds or offset variants.

| Field | Shape |
| --- | --- |
| `schema_version` | Integer `1` |
| `id` | Assessment ID |
| `title` | Assessment title |
| `as_of` | Explicit review cutoff in UTC |
| `assets` | 1–128 objects: `id`, `label`, `kind` |
| `requirements` | 1–64 objects: `id`, `title`, `asset_kind`, `max_age_hours` |
| `evidence` | 0–256 objects: `id`, `asset_id`, `requirement_id`, `path`, `collected_at`, `exit_code` |
| `findings` | 0–128 objects: `id`, `asset_id`, `severity`, `title`, `observation`, `recommendation`, `evidence_ids` |

## Assets and requirements

Kinds are `network`, `compute` and `storage`. Every asset kind must have at least one declared requirement. Each requirement applies to all assets of that kind. `max_age_hours` is an integer from 1 to 87,600. A record exactly at the age limit is current; one second older is stale.

IDs must be unique within each collection. Reusing an ID across different collections is allowed. A requirement for a kind absent from the inventory creates no coverage rows.

## Evidence records

```json
{
  "id": "route-export",
  "asset_id": "router-edge",
  "requirement_id": "routing",
  "path": "routing.txt",
  "collected_at": "2026-10-29T17:00:00Z",
  "exit_code": 0
}
```

The asset and applicable requirement must exist. Exit codes are declared collector results, integers 0–255; the kit does not execute or attest that collector. Records cannot be dated after `as_of`. Two records for the same asset/requirement cannot share a timestamp; ambiguity is rejected rather than resolved by file order or ID.

Paths are relative to the explicit `--evidence-root`: at most 240 characters, 1–8 components, each starting with an ASCII letter/digit and followed by letters, digits, dot, underscore or hyphen (maximum 80 characters per component). No absolute paths, traversal, dotfiles, backslashes or child symlinks. The selected root must itself be a real directory. Paths that are absent yield a missing evidence state; unsafe or inaccessible paths fail the build.

Only regular UTF-8 text files without NUL bytes are supported, at most 1,000,000 bytes each and 16,000,000 selected bytes in total. A UTF-8 BOM in an evidence file is preserved but ignored for the empty-text check. Repeated selection of the same file counts toward the total each time; each record is retained separately. No directory auto-discovery or command execution occurs.

## Findings

Severity is author-declared: `info`, `low`, `medium`, `high` or `critical`. Every finding references 1–32 distinct evidence IDs, all belonging to its asset. Unknown or cross-asset references are rejected.

Support is `attached` when every referenced file exists and contains non-whitespace text. Otherwise it is `incomplete`. Attached stale/failed evidence remains explicitly labeled with its status. This reference check does not establish whether evidence proves the finding. A critical manual finding can coexist with complete collection coverage.

## Rendering and privacy

Report prose escapes Markdown structure and HTML characters. CSV labels beginning with a spreadsheet formula prefix (including after whitespace) receive a leading apostrophe. The canonical JSON and copied evidence preserve supplied information. These protections concern presentation; they are not data sanitization or a guarantee that every spreadsheet importer handles a field identically.
