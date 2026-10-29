# Synthetic infrastructure handoff

Infrastructure Evidence Kit — collection review

Assessment: `demo-handoff` · As of: `2026-10-29T18:00:00Z` · Tool: `0.1.0`

Result: **evidence-complete**

**4 / 4 evidence checks collected**, across 3 assets. Manual findings: 1.

Collection coverage is not infrastructure health, compliance or proof of a claim. Timestamps and exit codes are supplied by the input author; the tool does not run commands or authenticate their origin.

## Coverage

The latest declared attempt wins for each asset/requirement. A newer failed, empty or missing attempt does not fall back to an older successful one.

| Asset | Requirement | Status | Latest evidence | Age (seconds) | Max age (hours) |
| --- | --- | --- | --- | ---: | ---: |
| Demo compute node (`compute-a`) | Capacity export | collected | [capacity-export](evidence/capacity-export.txt) | 3600 | 24 |
| Demo edge router (`router-edge`) | Backup job record | collected | [backup-export](evidence/backup-export.txt) | 7200 | 168 |
| Demo edge router (`router-edge`) | Routing observation | collected | [route-export](evidence/route-export.txt) | 3600 | 24 |
| Demo storage pool (`storage-a`) | Replication job record | collected | [replication-export](evidence/replication-export.txt) | 3600 | 24 |

## Manual findings

These are author-supplied observations. Attached evidence establishes a reference, not the truth, severity or validity of a conclusion.

### Review projected capacity

ID: `capacity-review` · Asset: `compute-a` · Declared severity: **medium** · Support: **attached**

The synthetic export reports 82 percent utilization\. A single sample does not establish a trend\.

Recommendation: Review growth history and planned workloads before deciding on expansion\.

Evidence:
- [capacity-export](evidence/capacity-export.txt) · collected · collected `2026-10-29T17:00:00Z`


## Evidence inventory

| ID | Asset | Requirement | Status | Bytes | SHA-256 |
| --- | --- | --- | --- | ---: | --- |
| `backup-export` | `router-edge` | `backup` | collected | 78 | 140938dde6c12b58b2911357c21ae96d75493ac3a3457a75e7dff79aa1890bc7 |
| `capacity-export` | `compute-a` | `capacity` | collected | 74 | fbf4f2952779b24f3f8527a7ba61cb485697b49e0ec5ef62573118c7fa141f20 |
| `replication-export` | `storage-a` | `replication` | collected | 87 | 09a228b234416a6a5ef611c2bfa58cd5b464cb50561d617f4aecc86bf14d66c6 |
| `route-export` | `router-edge` | `routing` | collected | 63 | 3835ecfe3c5429cdac5e888ca3fbb0f39db1a568f84dd43ce2b1373a9038ac19 |

## Integrity and handling

Run `iek verify --bundle <directory>` before consuming a copied bundle. Verification checks file-set and hash consistency, not identity, authorship, collection time, device health or authenticity. The manifest is unsigned.

Evidence files are copied byte for byte from explicit local inputs. This tool does not sanitize secrets or certify that a package is safe to publish. Review the actual files before sharing.
