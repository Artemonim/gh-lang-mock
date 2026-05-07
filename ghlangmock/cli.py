"""Command-line interface for ghlangmock.

Scans a source directory for language ratios and generates dummy files in the
destination directory to mirror those ratios.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
import importlib.resources as ir

from .scanner import scan_repository, compute_target_sizes
from .seed import read_seed_text
from .generator import generate_dummy_files, split_dummy_files_by_max_lines


def _positive_int(value: str) -> int:
    try:
        ivalue = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if ivalue < 0:
        raise argparse.ArgumentTypeError("must be non-negative")
    return ivalue


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ghlangmock",
        description=(
            "Generate dummy files whose total byte sizes per language mirror a source repo, "
            "similar to GitHub Linguist's language breakdown."
        ),
    )
    parser.add_argument("source", type=Path, help="Source repository directory to scan")
    parser.add_argument(
        "destination",
        type=Path,
        help="Path where the 'dummy-code' directory will be generated",
    )
    parser.add_argument("--seed", type=Path, default=None, help="Path to ASCII seed text file")
    parser.add_argument("--random", "-Random", action="store_true", help="Use cryptographically secure random ASCII (overrides seed)")
    parser.add_argument(
        "--total-bytes",
        type=_positive_int,
        default=100000,
        help=(
            "Total bytes to generate. Default equals total recognized bytes in source. "
            "When 0, generates an empty destination."
        ),
    )
    parser.add_argument(
        "--min-file-bytes",
        type=_positive_int,
        default=1,
        help="Minimum file size when splitting (default 1)",
    )
    parser.add_argument(
        "--max-lines-per-file",
        type=_positive_int,
        default=500,
        help=(
            "Split generated dummy files so that each file contains at most this many lines. "
            "Use 0 to disable line-based splitting (default: 500)."
        ),
    )
    parser.add_argument(
        "--no-overwrite",
        dest="overwrite",
        action="store_false",
        help="Prevent clearing the destination directory if it is non-empty",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    source: Path = args.source
    destination: Path = args.destination.resolve() / "dummy-code"
    if not source.exists() or not source.is_dir():
        parser.error(f"Source directory '{source}' does not exist or is not a directory")

    print(f"Scanning '{source.resolve()}'...")
    stats = scan_repository(source)

    # * Determine target total bytes
    target_total = (
        args.total_bytes if args.total_bytes is not None else stats.total_recognized_bytes
    )
    allocations = compute_target_sizes(stats, target_total)

    if not allocations:
        print("No recognized language files found in source. Nothing to generate.")
        # Ensure the directory exists even if empty
        destination.mkdir(parents=True, exist_ok=True)
        return 0

    # * Resolve seed: prefer explicit path; else packaged default asset
    seed_text = ""
    random_mode = False
    seed_path: Path | None = None
    if args.seed is not None:
        seed_path = Path(args.seed)
    else:
        try:
            seed_path = Path(ir.files("ghlangmock").joinpath("assets", "seed.txt"))
        except Exception:
            seed_path = None

    if seed_path is not None:
        seed_text = read_seed_text(seed_path)
        if not seed_text:
            random_mode = True
    else:
        random_mode = True

    if args.random:
        random_mode = True
        print("Using cryptographically secure random ASCII for file content.")
    elif seed_text:
        print(f"Using seed text from '{seed_path.resolve()}'.")
    else:
        print("Seed not found or empty, falling back to random ASCII for file content.")

    print(f"Generating dummy files in '{destination.resolve()}'...")
    created_files = generate_dummy_files(
        destination,
        allocations,
        seed_text=seed_text,
        random_fallback=random_mode,
        max_files_per_language=1,
        min_file_bytes=args.min_file_bytes,
        overwrite=args.overwrite,
    )
    if args.max_lines_per_file is not None:
        split_dummy_files_by_max_lines(created_files, args.max_lines_per_file)
    print("Done.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())


