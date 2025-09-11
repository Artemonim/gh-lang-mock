"""Seed data readers and secure ASCII generator.

Provides:
- read_seed_text: read ASCII text from a file and normalize line endings.
- generate_secure_ascii: produce cryptographically-secure random ASCII data.
"""

from __future__ import annotations

import secrets
from pathlib import Path
from typing import Iterable


ASCII_PRINTABLE = (
    "!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~\n"
)


def read_seed_text(path: Path) -> str:
    """Read ASCII seed text from ``path``.

    The function converts any newline variant (CR, LF, CRLF) and any non-printable
    or non-ASCII bytes into a single ``\n`` separator, with consecutive separators
    deduplicated. Printable ASCII (32..126) is preserved.

    Args:
        path: Path to a text file.

    Returns:
        A string containing only ASCII printable characters and ``\n``.
        Returns an empty string if the file is empty or cannot be read.
    """
    try:
        raw = path.read_bytes()
    except OSError:
        return ""

    out_chars: list[str] = []
    for b in raw:
        if b in (0x0D, 0x0A):
            if out_chars and out_chars[-1] != "\n":
                out_chars.append("\n")
            elif not out_chars:
                # * Avoid leading newline
                continue
            continue
        if 32 <= b <= 126:
            out_chars.append(chr(b))
        else:
            # * Replace any non-printable/non-ASCII with a single newline
            if out_chars and out_chars[-1] != "\n":
                out_chars.append("\n")
    return "".join(out_chars)


def generate_secure_ascii(num_bytes: int) -> bytes:
    """Generate ``num_bytes`` of cryptographically secure ASCII bytes.

    Args:
        num_bytes: Number of bytes to generate.

    Returns:
        Byte string of length ``num_bytes`` consisting of printable ASCII.

    Raises:
        ValueError: If ``num_bytes`` is negative.
    """
    if num_bytes < 0:
        raise ValueError("num_bytes must be non-negative")
    alphabet = ASCII_PRINTABLE
    # * Use secrets.choice for cryptographically secure randomness
    return bytes("".join(secrets.choice(alphabet) for _ in range(num_bytes)), "ascii")


