"""Scan a repository and compute language byte ratios.

Respects `.gitignore` files using gitwildmatch semantics via ``pathspec``.
Counts bytes by file extension mapped to language names. Unrecognized files are
ignored for ratio calculations to mirror Linguist-like behavior.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Mapping, Tuple

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
        if path.is_file():
            yield path


def scan_repository(source_dir: Path) -> LanguageStats:
    """Scan ``source_dir`` and compute LanguageStats.

    Args:
        source_dir: Root of the repository to scan.

    Returns:
        LanguageStats with byte counts per language for recognized files.
    """
    source_dir = source_dir.resolve()
    spec = build_ignore_spec(source_dir)
    counts: Dict[str, int] = defaultdict(int)
    total = 0

    all_files = list(_iter_files(source_dir))
    for file_path in tqdm(
        all_files, desc=f"Scanning {source_dir.name}", unit="file", ncols=100
    ):
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


