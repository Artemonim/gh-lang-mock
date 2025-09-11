"""Ignore handling using .gitignore semantics.

This module builds a PathSpec matcher from all `.gitignore` files under the
source directory and provides helpers to test whether a path is ignored.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from pathspec import PathSpec


def _prefix_patterns(patterns: Iterable[str], prefix: str) -> List[str]:
    """Prefix .gitignore patterns with a directory prefix.

    The function preserves negations and comments while translating anchored
    patterns to be relative to the source root.

    Args:
        patterns: Lines from a `.gitignore` file.
        prefix: Relative directory prefix from the source root to the directory
            containing `.gitignore`. Use '' for the root.

    Returns:
        A list of normalized patterns prefixed with ``prefix``.
    """
    normalized: List[str] = []
    if prefix and not prefix.endswith("/"):
        prefix = f"{prefix}/"

    for raw in patterns:
        line = raw.rstrip("\n")
        if not line or line.lstrip().startswith("#"):
            continue
        negated = line.startswith("!")
        body = line[1:] if negated else line
        if body.startswith("/"):
            body = body[1:]
        # * Join with prefix so nested .gitignore rules are relative to their directory
        joined = f"{prefix}{body}" if prefix else body
        normalized.append(f"!{joined}" if negated else joined)
    return normalized


def build_ignore_spec(source_dir: Path) -> PathSpec:
    """Build a ``PathSpec`` for the repository.

    The spec includes rules from all `.gitignore` files under ``source_dir`` and
    excludes the Git metadata directory by default.

    Args:
        source_dir: Repository root path.

    Returns:
        A ``PathSpec`` object using gitwildmatch syntax.
    """
    source_dir = source_dir.resolve()
    lines: List[str] = [".git/", ".hg/", ".svn/"]  # * Default VCS dirs
    for path in source_dir.rglob(".gitignore"):
        rel_parent = str(path.parent.relative_to(source_dir)).replace("\\", "/")
        parent_prefix = "" if rel_parent == "." else rel_parent
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            file_lines = f.readlines()
        lines.extend(_prefix_patterns(file_lines, parent_prefix))
    return PathSpec.from_lines("gitwildmatch", lines)


def is_ignored(source_dir: Path, spec: PathSpec, path: Path) -> bool:
    """Check if a path is ignored according to ``spec``.

    Args:
        source_dir: Repository root path.
        spec: Compiled PathSpec.
        path: Path to test.

    Returns:
        True if the path is ignored, False otherwise.
    """
    rel = str(path.resolve().relative_to(source_dir.resolve())).replace("\\", "/")
    return spec.match_file(rel)


