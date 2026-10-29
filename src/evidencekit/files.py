"""Bounded reads through a directory descriptor, without following child symlinks."""

import os
import stat
from pathlib import Path

from .model import InputError, relative_path

MAX_FILE = 1_000_000
MAX_TOTAL = 16_000_000


class SizeLimitError(InputError):
    """A file contains more bytes than the reader's explicit limit."""


def read_beneath(root: Path, relative: str, maximum=MAX_FILE):
    parts = relative_path(relative)
    # The caller explicitly selects the root. No child symlink may escape it.
    descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        file_descriptor = os.open(
            parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=descriptor
        )
        try:
            if not stat.S_ISREG(os.fstat(file_descriptor).st_mode):
                raise InputError("Evidence and bundle artifacts must be regular files.")
            with os.fdopen(file_descriptor, "rb", closefd=False) as handle:
                raw = handle.read(maximum + 1)
            if len(raw) > maximum:
                raise SizeLimitError("Evidence or bundle artifact exceeds its size limit.")
            return raw
        finally:
            os.close(file_descriptor)
    finally:
        os.close(descriptor)


def read_evidence(root: Path, records):
    try:
        root_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        os.close(root_fd)
    except OSError as exc:
        raise InputError("Evidence root must be an accessible, real directory.") from exc
    content = {}
    total = 0
    for record in records:
        try:
            raw = read_beneath(root, record["path"])
        except FileNotFoundError:
            content[record["id"]] = None
            continue
        except OSError as exc:
            raise InputError(
                "Cannot safely read an evidence file; check type and permissions."
            ) from exc
        try:
            decoded = raw.decode("utf-8")
        except UnicodeError as exc:
            raise InputError("v0.1 supports UTF-8 text exports only.") from exc
        if "\x00" in decoded:
            raise InputError("Text exports must not contain NUL bytes.")
        total += len(raw)
        if total > MAX_TOTAL:
            raise InputError("Total selected evidence exceeds 16,000,000 bytes.")
        content[record["id"]] = raw
    return content
