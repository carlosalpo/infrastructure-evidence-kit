# Validation record

Validation covers local file ingestion, assessment coverage, packaging and integrity verification. No new device access, network scan or live infrastructure measurement is performed by this project.

## Verified release candidate — 2026-10-29

- Code commit: `bf2287757bd86cf590c89d91f39a5b52abcded43`.
- Installed package on macOS, Python 3.12.14: **133 tests passed**, Ruff checks and formatting passed.
- All eight installed-CLI scenarios passed with their expected exit codes and collection states.
- [GitHub Actions run 40941599326](https://github.com/carlosalpo/infrastructure-evidence-kit/actions/runs/40941599326) passed on Python **3.11, 3.12 and 3.13**.
- Complete example: 4/4 collected; gap example: 1/4 collected, with missing, stale and failed states.
- Modified evidence: `verify` returned exit 1 and identified the affected artifact. Reads stop at the declared size plus one byte for oversized artifacts.
- Archived lab: three original public reports packaged with valid internal integrity; no network or device commands were run.

## Test scope

The test suite exercises schema and reference errors, timestamp/age boundaries, latest-attempt precedence, file-byte preservation, findings with missing attachments, malformed JSON, path traversal, symlinks, FIFOs, file/aggregate limits, deterministic output, report escaping, CSV prefixes, permissions, refused overwrites and partial writes. It blocks socket and subprocess creation during a build/verify test.

Eight executable scenarios run through the installed CLI: complete, mixed gaps, latest failed attempt, missing file, empty file, unsafe path, modified bundle and historical public-lab handoff. Every generated valid package is verified; the deliberately modified copy is expected to fail verification.

CI repeats tests and scenarios on Python 3.11, 3.12 and 3.13 on Linux. Local validation uses macOS. The historical integration packages three already-public reports with their original hashes; it is not an independent replay of the original laboratory tests. See [fixture provenance](../examples/historical-lab/provenance.json).

Screenshots of this project must identify their source commit and show actual local outputs. They must not imply live device collection or health/compliance certification.

The [five-image gallery](screenshots/README.md) records a separate execution of the final installed code, with commands, original outputs, fixture provenance and a SHA-256 inventory. All five images were visually reviewed before publication.
