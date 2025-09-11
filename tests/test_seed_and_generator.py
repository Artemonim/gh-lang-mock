from pathlib import Path

from ghlangmock.generator import generate_dummy_files
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


