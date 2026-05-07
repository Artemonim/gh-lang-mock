from pathlib import Path

from ghlangmock.generator import generate_dummy_files, split_dummy_files_by_max_lines
from ghlangmock.seed import read_seed_text, generate_secure_ascii


def test_read_seed_text_filters_and_normalizes(tmp_path: Path):
    p = tmp_path / "seed.txt"
    p.write_bytes(b"A\r\nB\x00C\n\xff")
    text = read_seed_text(p)
    assert text == "A\nB\nC\n"


def test_generate_secure_ascii_length():
    data = generate_secure_ascii(32)
    assert isinstance(data, (bytes, bytearray))
    assert len(data) == 32


def test_generate_dummy_files_with_seed(tmp_path: Path):
    dest = tmp_path / "out"
    mapping = {"Python": 10, "TypeScript": 5}
    files = generate_dummy_files(
        dest,
        mapping,
        seed_text="ABC",
        random_fallback=False,
        max_files_per_language=2,
        min_file_bytes=1,
        overwrite=True,
    )
    assert len(files) >= 2
    total = sum(f.stat().st_size for f in files)
    assert total == 15
    # ensure extensions correspond
    assert any(f.suffix == ".py" for f in files)
    assert any(f.suffix == ".ts" for f in files)


def test_generate_dummy_files_includes_rust_hint_without_size_shift(tmp_path: Path):
    dest = tmp_path / "out"
    mapping = {"Rust": 40}
    files = generate_dummy_files(
        dest,
        mapping,
        seed_text="ABC",
        random_fallback=False,
        max_files_per_language=1,
        min_file_bytes=1,
        overwrite=True,
    )
    assert len(files) == 1
    rust_file = files[0]
    assert rust_file.suffix == ".rs"
    payload = rust_file.read_bytes()
    assert len(payload) == 40
    assert payload.startswith(b"fn main() {")


def test_generate_dummy_files_truncates_hint_for_tiny_files(tmp_path: Path):
    dest = tmp_path / "out"
    mapping = {"Rust": 4}
    files = generate_dummy_files(
        dest,
        mapping,
        seed_text="ABC",
        random_fallback=False,
        max_files_per_language=1,
        min_file_bytes=1,
        overwrite=True,
    )
    assert len(files) == 1
    payload = files[0].read_bytes()
    assert len(payload) == 4
    assert payload == b"fn m"


def test_split_dummy_files_by_max_lines_splits_and_preserves_size(tmp_path: Path):
    original = tmp_path / "dummy.py"
    # * 12 lines ensure multiple chunks when max_lines_per_file is 5
    original.write_text("line\n" * 12, encoding="ascii")
    original_size = original.stat().st_size

    result_files = split_dummy_files_by_max_lines([original], max_lines_per_file=5)

    # * Expect three files: 5 + 5 + 2 lines
    assert len(result_files) == 3
    # * Original file is replaced with a numbered sequence dummy_1.py, dummy_2.py, dummy_3.py
    names = sorted(p.name for p in result_files)
    assert names == ["dummy_1.py", "dummy_2.py", "dummy_3.py"]
    # * Total size is preserved across all parts
    total_size = sum(p.stat().st_size for p in result_files)
    assert total_size == original_size
    # * Each file respects the max line bound
    for p in result_files:
        with p.open(encoding="ascii") as fh:
            assert sum(1 for _ in fh) <= 5


def test_split_dummy_files_with_non_positive_limit_is_noop(tmp_path: Path):
    original = tmp_path / "dummy.py"
    original.write_text("line\n" * 3, encoding="ascii")

    result_files_zero = split_dummy_files_by_max_lines([original], max_lines_per_file=0)
    result_files_negative = split_dummy_files_by_max_lines([original], max_lines_per_file=-1)

    assert result_files_zero == [original]
    assert result_files_negative == [original]

