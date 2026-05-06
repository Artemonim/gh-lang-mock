"""Scan a repository and compute language byte ratios.

Respects `.gitignore` files using gitwildmatch semantics via ``pathspec``.
Counts bytes by file extension mapped to language names. Unrecognized files are
ignored for ratio calculations to mirror Linguist-like behavior.
"""

from __future__ import annotations

import configparser
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Mapping, Optional, Set, Tuple

from tqdm import tqdm

from .ignore import build_ignore_spec, is_ignored
from .languages import detect_language


@dataclass(frozen=True)
class LanguageStats:
    """Holds raw byte counts by language and total recognized bytes."""

    bytes_by_language: Mapping[str, int]
    total_recognized_bytes: int

    def ratios(self) -> Mapping[str, float]:
        """Compute per-language ratios in the range [0,1]."""
        total = self.total_recognized_bytes
        if total <= 0:
            return {lang: 0.0 for lang in self.bytes_by_language}
        return {lang: count / total for lang, count in self.bytes_by_language.items()}


def _iter_files(source_dir: Path) -> Iterable[Path]:
    for path in source_dir.rglob("*"):
        try:
            if path.is_file():
                yield path
        except OSError:
            # * Skip entries that cannot be stat'ed (e.g., locked/system-managed paths)
            continue


def _to_rel_posix(source_dir: Path, path: Path) -> Optional[str]:
    try:
        rel = path.resolve().relative_to(source_dir.resolve())
    except (OSError, ValueError):
        return None
    return str(rel).replace("\\", "/")


def _normalize_submodule_path(raw_path: str) -> str:
    normalized = raw_path.strip().replace("\\", "/").strip("/")
    parts = [part for part in normalized.split("/") if part and part != "."]
    return "/".join(parts)


def _read_submodule_paths_from_gitmodules(source_dir: Path) -> Set[str]:
    gitmodules_path = source_dir / ".gitmodules"
    if not gitmodules_path.is_file():
        return set()

    parser = configparser.ConfigParser()
    try:
        parser.read(gitmodules_path, encoding="utf-8")
    except (configparser.Error, OSError):
        return set()

    submodule_paths: Set[str] = set()
    for section_name in parser.sections():
        if not section_name.startswith("submodule "):
            continue
        if not parser.has_option(section_name, "path"):
            continue
        raw_path = parser.get(section_name, "path", fallback="")
        normalized_path = _normalize_submodule_path(raw_path)
        if normalized_path:
            submodule_paths.add(normalized_path)
    return submodule_paths


def _parse_submodule_paths_from_git_index(stdout: str) -> Set[str]:
    submodule_paths: Set[str] = set()
    for line in stdout.splitlines():
        if not line:
            continue
        metadata, separator, git_path = line.partition("\t")
        if not separator:
            continue
        mode = metadata.split(" ", maxsplit=1)[0]
        if mode != "160000":
            continue
        normalized_path = _normalize_submodule_path(git_path)
        if normalized_path:
            submodule_paths.add(normalized_path)
    return submodule_paths


def _read_submodule_paths_from_git_index(source_dir: Path) -> Set[str]:
    try:
        proc = subprocess.run(
            ["git", "-C", str(source_dir), "ls-files", "--stage"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return set()
    return _parse_submodule_paths_from_git_index(proc.stdout)


def _discover_submodule_paths(source_dir: Path) -> Set[str]:
    # * Explicit behavior when Git metadata is missing:
    # * - use `.gitmodules` paths if the file exists;
    # * - otherwise treat all directories as regular.
    submodule_paths = _read_submodule_paths_from_gitmodules(source_dir)
    submodule_paths.update(_read_submodule_paths_from_git_index(source_dir))
    return submodule_paths


def scan_repository(source_dir: Path) -> LanguageStats:
    """Scan ``source_dir`` and compute LanguageStats.

    Args:
        source_dir: Root of the repository to scan.

    Returns:
        LanguageStats with byte counts per language for recognized files.
    """
    source_dir = source_dir.resolve()
    spec = build_ignore_spec(source_dir)
    submodule_paths = tuple(sorted(_discover_submodule_paths(source_dir)))
    submodule_prefixes = tuple(f"{path}/" for path in submodule_paths)
    counts: Dict[str, int] = defaultdict(int)
    total = 0

    all_files = list(_iter_files(source_dir))
    for file_path in tqdm(
        all_files, desc=f"Scanning {source_dir.name}", unit="file", ncols=100
    ):
        rel_path = _to_rel_posix(source_dir, file_path)
        if rel_path is None:
            continue
        if rel_path in submodule_paths or rel_path.startswith(submodule_prefixes):
            continue
        if is_ignored(source_dir, spec, file_path):
            continue
        language = detect_language(file_path)
        if language is None:
            continue
        try:
            size = file_path.stat().st_size
        except OSError:
            # * Skip unreadable files
            continue
        counts[language] += int(size)
        total += int(size)

    return LanguageStats(bytes_by_language=dict(counts), total_recognized_bytes=total)


def compute_target_sizes(stats: LanguageStats, target_total_bytes: int) -> Dict[str, int]:
    """Convert ratios to per-language target sizes in bytes.

    The function ensures the sum of allocated bytes equals ``target_total_bytes``
    by distributing rounding remainders.

    Args:
        stats: LanguageStats from the source.
        target_total_bytes: Desired total size of generated files.

    Returns:
        A mapping of language to target bytes.
    """
    if target_total_bytes < 0:
        raise ValueError("target_total_bytes must be non-negative")
    ratios = stats.ratios()
    # * Initial floor allocation
    allocations: Dict[str, int] = {}
    remainders: Dict[str, float] = {}
    allocated = 0
    for lang, ratio in ratios.items():
        exact = ratio * target_total_bytes
        floor_val = int(exact)
        allocations[lang] = floor_val
        remainders[lang] = exact - floor_val
        allocated += floor_val

    # * Distribute leftover bytes by largest remainder
    leftover = target_total_bytes - allocated
    for lang, _ in sorted(remainders.items(), key=lambda kv: kv[1], reverse=True):
        if leftover <= 0:
            break
        allocations[lang] += 1
        leftover -= 1

    # * If there are no recognized languages, return empty mapping
    if not allocations:
        return {}
    return allocations


