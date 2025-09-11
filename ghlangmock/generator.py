"""Dummy file generator.

Creates dummy files with sizes proportional to language ratios, using either a
seed text looped as payload or cryptographically secure random ASCII data.
"""

from __future__ import annotations

import math
import shutil
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from tqdm import tqdm

from .languages import primary_extension
from .seed import generate_secure_ascii


def _ensure_clean_dir(dest_dir: Path, overwrite: bool) -> None:
    """Create a clean destination directory, ensuring parent exists."""
    # First, ensure the parent directory exists.
    parent = dest_dir.parent
    if not parent.exists():
        # This case should ideally be handled by the CLI caller, but we can be robust.
        parent.mkdir(parents=True, exist_ok=True)

    if dest_dir.is_dir():
        if overwrite:
            shutil.rmtree(dest_dir)
        elif any(dest_dir.iterdir()):
            raise FileExistsError(
                f"Destination directory '{dest_dir}' is not empty. Use --overwrite to clear it."
            )
    elif dest_dir.exists():
        # It's a file or something else, which is not usable.
        raise FileExistsError(f"Destination path '{dest_dir}' exists and is not a directory.")

    dest_dir.mkdir()


def _repeat_seed_to_length(seed: str, length: int) -> bytes:
    if length <= 0:
        return b""
    if not seed:
        return generate_secure_ascii(length)
    repeated = (seed * (math.ceil(length / len(seed)))).encode("ascii")
    return repeated[:length]


def _split_into_files(total_bytes: int, max_files: int, min_file_bytes: int) -> List[int]:
    """Split ``total_bytes`` into at most ``max_files`` parts >= ``min_file_bytes``.

    Returns a list of file sizes whose sum equals ``total_bytes``. Uses near-even
    distribution while honoring minimum size.
    """
    if total_bytes <= 0:
        return []
    if max_files <= 0:
        max_files = 1
    num_files = min(max_files, total_bytes // max(1, min_file_bytes) or 1)
    base = total_bytes // num_files
    sizes = [base] * num_files
    remainder = total_bytes - base * num_files
    idx = 0
    while remainder > 0:
        sizes[idx] += 1
        remainder -= 1
        idx = (idx + 1) % num_files
    # * Ensure minimum size by borrowing from larger entries if needed
    for i in range(len(sizes)):
        if sizes[i] < min_file_bytes and len(sizes) > 1:
            need = min_file_bytes - sizes[i]
            for j in range(len(sizes)):
                if j == i:
                    continue
                can_take = max(0, sizes[j] - min_file_bytes)
                take = min(need, can_take)
                sizes[j] -= take
                sizes[i] += take
                need -= take
                if need == 0:
                    break
    return [s for s in sizes if s > 0]


def generate_dummy_files(
    dest_dir: Path,
    language_to_bytes: Dict[str, int],
    *,
    seed_text: str,
    random_fallback: bool,
    max_files_per_language: int,
    min_file_bytes: int,
    overwrite: bool,
) -> List[Path]:
    """Generate dummy files matching target language sizes.

    Args:
        dest_dir: Destination directory to populate.
        language_to_bytes: Target bytes per language.
        seed_text: ASCII text used to fill files; repeated to required sizes.
        random_fallback: If True, use secure random ASCII when seed is empty.
        max_files_per_language: Upper bound on file count per language.
        min_file_bytes: Minimum size of any generated file.
        overwrite: If True, clear non-empty destination directory first.

    Returns:
        List of generated file paths.
    """
    _ensure_clean_dir(dest_dir, overwrite)
    created: List[Path] = []
    total_bytes_to_generate = sum(language_to_bytes.values())

    with tqdm(
        total=total_bytes_to_generate,
        desc=f"Generating in {dest_dir.name}",
        unit="B",
        unit_scale=True,
        unit_divisor=1024,
        ncols=100,
    ) as pbar:
        for language, total_bytes in sorted(language_to_bytes.items()):
            if total_bytes <= 0:
                continue
            ext = primary_extension(language)
            sizes = _split_into_files(
                total_bytes, max_files_per_language, min_file_bytes
            )
            for idx, size in enumerate(sizes, start=1):
                file_name = f"{language.replace(' ', '_')}_{idx}{ext}"
                file_path = dest_dir / file_name
                payload = _repeat_seed_to_length(
                    seed_text if not random_fallback else "", size
                )
                file_path.write_bytes(payload)
                created.append(file_path)
                pbar.update(size)
    return created


