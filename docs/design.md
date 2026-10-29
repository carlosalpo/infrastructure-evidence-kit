# Design and operational boundaries

## One review, one explicit evidence set

Infrastructure handoffs often mix exports, screenshots and conclusions without a clear statement of what was expected. This kit declares the inventory and evidence requirements first, then evaluates collection coverage. Findings remain manual and link to retained files.

The runtime reads only the explicitly named exports beneath the selected root. It does not discover devices, SSH, call cloud APIs, invoke subprocesses or assess the meaning of a configuration. Files are read into bounded memory once and those exact bytes are used for both hashing and output. Concurrently changing source files are not a point-in-time infrastructure snapshot; provide stable exports.

## Deterministic review time and latest-attempt precedence

The input fixes `as_of`, and every record declares a collection timestamp. Age is calculated in whole seconds. This avoids an archived package changing result because it is rebuilt a week later. For a new assessment, update the cutoff and supply new observations rather than relabel an old report as current.

For each asset/requirement, the latest timestamp wins. Status precedence for that record is missing file → failed collector → empty content → stale → collected. An earlier successful record stays in the inventory but cannot mask a later failed attempt. Tied timestamps for the same pair are rejected.

There is no percent-health score. Summary counts refer solely to the declared collection requirements. A finding may reference an older file; its age and status are shown separately. Any missing/empty finding attachment creates an evidence-gap result even if the latest coverage records are complete.

## Local filesystem boundary

The implementation uses POSIX `dir_fd` traversal, `O_NOFOLLOW`, regular-file checks and nonblocking opens for potential special files. Each path component is validated before opening. It refuses child symlinks, path traversal, FIFOs and other nonregular exports. The selected root itself cannot be a symlink; ancestor resolution used to locate that explicit root is an operating-system concern.

Output is a fresh directory (0700) with files (0600) on supported POSIX systems. The manifest is written last with exclusive file creation. This is not a crash-durable directory transaction: failures can leave partial files. Existing output is never merged or overwritten. Use `verify` on received/copied packages, and handle them in a private working directory rather than a location writable by untrusted concurrent processes.

## Integrity is not authenticity

The manifest inventories every emitted artifact except itself. Verification checks the expected paths, sizes and SHA-256 bytes and rejects missing/extra artifacts. The manifest schema and path vocabulary are validated before reading its referenced files. Evidence subdirectories may not contain links or nested directories.

The verifier bounds each read to the declared size plus one byte, so an oversized altered artifact is detected without reading it in full. Declared artifacts are limited to 8 MB each and 48 MB in total; these verification bounds cover generated metadata as well as evidence.

The manifest is unsigned. A deliberately updated file and manifest can pass verification; a regression test demonstrates that boundary. It does not prove origin, collection timestamps, collector exit codes, device state or chain of custody. For authentic provenance, use an external signing and retention process appropriate to your organization; that process is outside v0.1.

## Scope tradeoffs

- Generic UTF-8 exports make the kit independent of device vendors. It does not parse vendor schemas or accept binary screenshots/PDFs in this release.
- Files are preserved byte for byte, including failures. The tool does not remove credentials or confidential data.
- One requirement applies to an entire asset kind. Per-asset exceptions and automatic collector integrations are future extensions, not current features.
- Offline generation and verification are supported on Linux/macOS; native Windows requires a separately designed filesystem implementation.
- Inputs are sorted by ID and manifests have no generated wall-clock timestamps or machine-specific paths. Original input hashes differ when input whitespace/order differs, while canonical artifacts remain stable.
