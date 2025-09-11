from pathlib import Path

from ghlangmock.ignore import build_ignore_spec, is_ignored


def test_ignore_respects_nested(tmp_path: Path):
    src = tmp_path / "src"
    a = src / "a"; a.mkdir(parents=True)
    b = src / "b"; b.mkdir(parents=True)
    # root .gitignore ignores *.log and b directory
    (src / ".gitignore").write_text("*.log\n/b\n", encoding="utf-8")
    # nested override to unignore a/special.log
    (a / ".gitignore").write_text("!special.log\n", encoding="utf-8")

    spec = build_ignore_spec(src)
    assert is_ignored(src, spec, src / "file.log")
    assert is_ignored(src, spec, b / "anything.txt")
    assert not is_ignored(src, spec, a / "special.log")


