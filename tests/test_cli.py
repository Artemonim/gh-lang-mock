from pathlib import Path
import sys

import pytest

from ghlangmock.cli import main


def test_cli_end_to_end(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    # Prepare a tiny repo with two languages
    src = tmp_path / "src"; src.mkdir()
    (src / ".gitignore").write_text("ignored/\n", encoding="utf-8")
    (src / "a.py").write_text("print('x')\n", encoding="utf-8")
    (src / "b.ts").write_text("export const x=1;\n", encoding="utf-8")
    (src / "ignored").mkdir()
    (src / "ignored" / "c.js").write_text("console.log('y')\n", encoding="utf-8")

    dest = tmp_path / "dest"

    # Run CLI with a small total to speed up tests
    # We pass --no-overwrite=False, which is the default, to be explicit
    rc = main([str(src), str(dest), "--total-bytes", "16"])
    assert rc == 0
    output_dir = dest / "dummy-code"
    assert output_dir.exists()
    assert output_dir.is_dir()

    # Check that no files were created in the parent directory
    parent_contents = [p for p in dest.iterdir() if p.name != "dummy-code"]
    assert not parent_contents, "Files were incorrectly created in the parent directory"

    files = list(output_dir.iterdir())
    assert files, "Expected some files generated"
    total = sum(p.stat().st_size for p in files)
    assert total == 16


