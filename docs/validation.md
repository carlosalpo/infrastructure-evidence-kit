# Validation record

Validation covers local file ingestion, assessment coverage, packaging and integrity verification. No new device access, network scan or live infrastructure measurement is performed by this project.

The test suite exercises schema and reference errors, timestamp/age boundaries, latest-attempt precedence, file-byte preservation, findings with missing attachments, malformed JSON, path traversal, symlinks, FIFOs, file/aggregate limits, deterministic output, report escaping, CSV prefixes, permissions, refused overwrites and partial writes. It blocks socket and subprocess creation during a build/verify test.

Eight executable scenarios run through the installed CLI: complete, mixed gaps, latest failed attempt, missing file, empty file, unsafe path, modified bundle and historical public-lab handoff. Every generated valid package is verified; the deliberately modified copy is expected to fail verification.

CI repeats tests and scenarios on Python 3.11, 3.12 and 3.13 on Linux. Local validation uses macOS. The historical integration packages three already-public reports with their original hashes; it is not an independent replay of the original laboratory tests. See [fixture provenance](../examples/historical-lab/provenance.json).

Screenshots of this project must identify their source commit and show actual local outputs. They must not imply live device collection or health/compliance certification.
