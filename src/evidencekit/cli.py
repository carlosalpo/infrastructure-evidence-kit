"""Build explicit local evidence packages or verify a received copy."""

import argparse
import os
import sys
from pathlib import Path

from . import __version__
from .bundle import build
from .model import InputError, json_bytes, load
from .verify import verify


def write_bundle(output, files):
    output.mkdir(mode=0o700, parents=False, exist_ok=False)
    if any(name.startswith("evidence/") for name in files):
        (output / "evidence").mkdir(mode=0o700)
    for name, raw in files.items():
        descriptor = os.open(output / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(raw)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Traceable infrastructure evidence packages.")
    parser.add_argument(
        "--version", action="version", version=f"infrastructure-evidence-kit {__version__}"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    builder = commands.add_parser("build")
    builder.add_argument("--input", required=True, type=Path)
    builder.add_argument("--evidence-root", required=True, type=Path)
    builder.add_argument("--output", required=True, type=Path)
    verifier = commands.add_parser("verify")
    verifier.add_argument("--bundle", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "verify":
            result = verify(args.bundle)
            print(json_bytes(result).decode(), end="")
            return 0 if result["valid"] else 1
        data, source_hash = load(args.input)
        files, index = build(data, source_hash, args.evidence_root)
        write_bundle(args.output, files)
        summary = index["summary"]
        print(
            f"{index['result'].upper()} | {summary['collected']}/{summary['checks']} collected | "
            "collection coverage only; not device health"
        )
        return 0 if index["result"] == "evidence-complete" else 1
    except InputError as exc:
        print(f"Input error: {exc}", file=sys.stderr)
    except FileExistsError:
        print(
            "Output exists; choose a new directory. Existing files were not overwritten.",
            file=sys.stderr,
        )
    except OSError:
        print(
            "File operation failed. Check paths and permissions. A partial output may remain; "
            "verify it before use.",
            file=sys.stderr,
        )
    return 2


if __name__ == "__main__":
    sys.exit(main())
