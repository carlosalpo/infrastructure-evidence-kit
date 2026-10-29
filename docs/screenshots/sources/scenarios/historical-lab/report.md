# Archived Network Lab Factory evidence handoff

Infrastructure Evidence Kit — collection review

Assessment: `archived-lab-handoff` · As of: `2026-10-29T18:00:00Z` · Tool: `0.1.0`

Result: **evidence-complete**

**3 / 3 evidence checks collected**, across 1 assets. Manual findings: 1.

Collection coverage is not infrastructure health, compliance or proof of a claim. Timestamps and exit codes are supplied by the input author; the tool does not run commands or authenticate their origin.

## Coverage

The latest declared attempt wins for each asset/requirement. A newer failed, empty or missing attempt does not fall back to an older successful one.

| Asset | Requirement | Status | Latest evidence | Age (seconds) | Max age (hours) |
| --- | --- | --- | --- | ---: | ---: |
| Published synthetic dual\-WAN laboratory (`dual-wan-lab`) | Baseline test report | collected | [baseline-record](evidence/baseline-record.txt) | 1225 | 168 |
| Published synthetic dual\-WAN laboratory (`dual-wan-lab`) | Fault test report | collected | [fault-record](evidence/fault-record.txt) | 1167 | 168 |
| Published synthetic dual\-WAN laboratory (`dual-wan-lab`) | Recovery test report | collected | [recovery-record](evidence/recovery-record.txt) | 1113 | 168 |

## Manual findings

These are author-supplied observations. Attached evidence establishes a reference, not the truth, severity or validity of a conclusion.

### Recorded behavior during a controlled fault

ID: `controlled-fault` · Asset: `dual-wan-lab` · Declared severity: **info** · Support: **attached**

The archived fault report records two lost adjacencies while twelve loopback probes pass\. This is a cited historical lab observation, not a new measurement\.

Recommendation: Use the source project validation record for test scope\. Do not infer convergence time or production availability from this package\.

Evidence:
- [fault-record](evidence/fault-record.txt) · collected · collected `2026-10-29T17:40:33Z`
- [recovery-record](evidence/recovery-record.txt) · collected · collected `2026-10-29T17:41:27Z`


## Evidence inventory

| ID | Asset | Requirement | Status | Bytes | SHA-256 |
| --- | --- | --- | --- | ---: | --- |
| `baseline-record` | `dual-wan-lab` | `baseline` | collected | 2376 | 8f28bd149eb3764fce1ec21bfcc1bb6a964aa92244f9515403a635f36c6254d2 |
| `fault-record` | `dual-wan-lab` | `fault` | collected | 2376 | d69fe202345038e255cf1e8e3354ed253d777f18506ea70f2c7ac6ccdfad3ae0 |
| `recovery-record` | `dual-wan-lab` | `recovery` | collected | 2376 | d550b766417d31007e6de13925735a6fe2ffad57b97891db82bcf38ab533e1ec |

## Integrity and handling

Run `iek verify --bundle <directory>` before consuming a copied bundle. Verification checks file-set and hash consistency, not identity, authorship, collection time, device health or authenticity. The manifest is unsigned.

Evidence files are copied byte for byte from explicit local inputs. This tool does not sanitize secrets or certify that a package is safe to publish. Review the actual files before sharing.
