# Infrastructure Evidence Kit

[![CI](https://github.com/carlosalpo/infrastructure-evidence-kit/actions/workflows/ci.yml/badge.svg)](https://github.com/carlosalpo/infrastructure-evidence-kit/actions/workflows/ci.yml)

**Turn scattered infrastructure exports into a traceable assessment package.**

Declare the assets in scope, the evidence each asset type needs, when it was collected and which files support your observations. The kit packages those explicit local files, identifies collection gaps and produces a review with evidence links, a coverage CSV and an integrity manifest.

The included gap scenario has a current routing export, a missing backup record, an old capacity sample and a failed replication-export attempt. The report shows **1 of 4 evidence checks collected** and explains the remaining three states. A separate verification command detects modified, missing or extra files in a copied package.

This is an **offline evidence organizer** for infrastructure reviews and handoffs. It does not connect to devices, execute collection commands, interpret configurations or certify infrastructure health. A collected report can contain failed device checks; collection coverage and operational results are different measures.

![Conceptual infrastructure evidence kit](docs/illustrations/infrastructure-evidence-kit-cover.png)

*Concept illustration, not a test capture or product interface. [Illustration context](docs/illustrations/README.md).*

## Quick start

Python 3.11 or newer on **Linux or macOS**. No runtime dependencies or device credentials. Filesystem safeguards use POSIX directory descriptors; native Windows is outside v0.1 support.

```sh
git clone https://github.com/carlosalpo/infrastructure-evidence-kit.git
cd infrastructure-evidence-kit
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .

iek build --input examples/complete.json \
  --evidence-root examples/evidence --output complete-demo
iek verify --bundle complete-demo
```

Open `complete-demo/report.md`. Follow its links to the exact exported bytes. Every build requires a **new output directory** with an existing parent; the tool never overwrites a prior run.

```sh
# Expected build exit 1: a valid package with collection gaps
iek build --input examples/gaps.json \
  --evidence-root examples/evidence --output gap-demo

# Expected verify exit 0: the gap package still has valid internal integrity
iek verify --bundle gap-demo
```

## Coverage with an explicit meaning

Each asset is matched to every requirement for its declared kind: `network`, `compute` or `storage`. These are organizational categories; there are no vendor-specific parsers. The latest declared attempt for each asset/requirement determines its status:

| Status | Meaning |
| --- | --- |
| `missing` | No record, or the selected file is absent |
| `failed` | A file exists, but the declared collector exit code is nonzero |
| `empty` | The latest successful export contains no non-whitespace text |
| `stale` | The latest successful nonempty export exceeds the requirement's age limit |
| `collected` | A nonempty file from the latest attempt is within the declared age limit and has exit code 0 |

A newer failed or missing attempt **does not fall back** to an older success. All supplied records remain in the inventory, and available files are retained even when stale or failed. Assessment time is explicit in the input, so an archived review can be reproduced without depending on today's clock.

Manual findings link to evidence IDs for the same asset. The report shows whether those files are attached and lists their collection states. The tool does not verify the finding's truth, declared severity or recommendation. No findings does not imply a clean assessment.

## What the package contains

| File | Purpose |
| --- | --- |
| `assessment.json` | Canonical input, including assets, requirements and manual findings |
| `index.json` | Coverage states, evidence inventory, ages, hashes and finding references |
| `coverage.csv` | Spreadsheet-friendly collection matrix with formula-prefix protection |
| `report.md` | Review summary, evidence links, findings and file inventory |
| `evidence/<id>.txt` | Exact bytes of the explicitly selected UTF-8 exports |
| `manifest.json` | Version, source/canonical hashes, result and every artifact's hash and byte length |

The manifest is written last. An interrupted build may leave a partial directory; run `iek verify` before consuming a package. The verifier requires the declared file set and checks each artifact's bytes. **The manifest is unsigned**: somebody who changes both a file and its manifest can create another internally consistent package. Verification is not authentication or chain-of-custody certification.

Files are copied without redaction. Generated reports contain supplied labels and observations. Review actual input and output before sharing a real assessment; the examples in this repository contain synthetic data or already-public laboratory reports.

## Reproducible scenarios

| Scenario | Expected behavior |
| --- | --- |
| Complete synthetic assessment | Build exit 0, 4/4 collected; verify exit 0 |
| Mixed collection gaps | Build exit 1, one collected plus missing/stale/failed states |
| Newer failed attempt | Build exit 1; older success does not mask the failure |
| Missing evidence file | Build exit 1; linked finding is marked incomplete |
| Empty export | Build exit 1 with `empty` |
| Unsafe relative path | Exit 2 before output creation |
| Deliberately modified package | Verify exit 1 for changed evidence |
| Archived public-lab handoff | Three historical reports packaged and verified, without new lab access |

The [historical integration](examples/historical-lab/README.md) reuses baseline, fault and recovery reports from [Network Lab Factory v0.1.1](https://github.com/carlosalpo/network-lab-factory/releases/tag/v0.1.1), with original bytes and source references. Its 3/3 collection result includes a report with failed network checks, demonstrating why collection coverage must not be labeled device health.

## Command contract

`iek build --input <assessment.json> --evidence-root <directory> --output <new-directory>`

- **0:** all applicable evidence checks are collected and all finding references have nonempty attached files. Manual finding severity does not change this result.
- **1:** a valid package was generated, but coverage or finding attachments have gaps.
- **2:** invalid input, unsafe/unsupported files, CLI misuse or file-operation failure. No valid new package should be assumed.

`iek verify --bundle <directory>`

- **0:** declared files match their hashes and byte lengths, with no missing/extra files.
- **1:** integrity mismatch or missing package/completion manifest.
- **2:** malformed/unsupported manifest, unsafe filesystem structure or file-operation failure.

## Development and validation

```sh
python -m pip install '.[dev]'
ruff check src tests scripts
ruff format --check src tests scripts
pytest -q
python scripts/check_examples.py --output reports/example-matrix
```

Tests cover the input contract, freshness boundaries, latest-attempt precedence, missing/empty exports, finding references, deterministic output, original-byte preservation, tampering detection, unsafe paths, symlinks, special files, resource limits, escaped report text, CSV formula prefixes, output permissions and interrupted writes. CI runs on Python 3.11, 3.12 and 3.13 on Linux.

See [input specification](docs/input-spec.md), [design decisions](docs/design.md), [validation record](docs/validation.md) and [security notes](SECURITY.md).

## En español

Una herramienta para organizar evidencias de infraestructura, detectar vacíos de recolección y entregar hallazgos con respaldo trazable. Genera un paquete reproducible y permite comprobar si sus archivos cambiaron. No confunde disponibilidad de evidencias con salud de los equipos ni valida automáticamente las conclusiones del autor.

Created by **Carlos Alvarado**. MIT licensed.
