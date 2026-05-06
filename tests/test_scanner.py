from pathlib import Path

from ghlangmock.scanner import (
    compute_target_sizes,
    scan_repository,
    _parse_submodule_paths_from_git_index,
)


def test_scan_repository_counts(tmp_path: Path):
    src = tmp_path / "repo"; src.mkdir()
    (src / ".gitignore").write_text("build/\n", encoding="utf-8")
    (src / "app.py").write_text("print('x')\n", encoding="utf-8")
    (src / "lib.ts").write_text("export const x=1;\n", encoding="utf-8")
    build = src / "build"; build.mkdir()
    (build / "ignored.js").write_text("console.log(1)\n", encoding="utf-8")

    stats = scan_repository(src)
    assert stats.total_recognized_bytes > 0
    ratios = stats.ratios()
    assert set(ratios) == {"Python", "TypeScript"}
    assert 0.0 < ratios["Python"] < 1.0


def test_compute_target_sizes_rounding():
    from types import SimpleNamespace
    stats = SimpleNamespace(
        ratios=lambda: {"Python": 0.3333, "TypeScript": 0.6667}
    )
    alloc = compute_target_sizes(stats, 10)
    assert sum(alloc.values()) == 10
    # TypeScript should get at least as many bytes as Python
    assert alloc["TypeScript"] >= alloc["Python"]


def test_scan_repository_excludes_paths_from_gitmodules(tmp_path: Path):
    src = tmp_path / "repo"; src.mkdir()
    (src / ".gitmodules").write_text(
        '[submodule "vendor/templates"]\n'
        "  path = vendor/templates\n"
        "  url = https://example.com/vendor/templates.git\n",
        encoding="utf-8",
    )
    (src / "root.py").write_text("print('root')\n", encoding="utf-8")
    submodule_dir = src / "vendor" / "templates"
    submodule_dir.mkdir(parents=True)
    (submodule_dir / "ignored.py").write_text("print('submodule')\n", encoding="utf-8")

    stats = scan_repository(src)
    expected_total = (src / "root.py").stat().st_size

    assert stats.total_recognized_bytes == expected_total
    assert stats.bytes_by_language["Python"] == expected_total


def test_scan_repository_includes_nested_paths_without_submodule_metadata(tmp_path: Path):
    src = tmp_path / "repo"; src.mkdir()
    (src / "root.py").write_text("print('root')\n", encoding="utf-8")
    nested_dir = src / "vendor" / "templates"
    nested_dir.mkdir(parents=True)
    (nested_dir / "included.py").write_text("print('nested')\n", encoding="utf-8")

    stats = scan_repository(src)
    expected_total = (src / "root.py").stat().st_size + (nested_dir / "included.py").stat().st_size

    assert stats.total_recognized_bytes == expected_total
    assert stats.bytes_by_language["Python"] == expected_total


def test_parse_submodule_paths_from_git_index_detects_gitlinks():
    output = (
        "160000 d34db33fd34db33fd34db33fd34db33fd34db33f 0\tvendor/templates\n"
        "100644 aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa 0\tmain.py\n"
    )

    assert _parse_submodule_paths_from_git_index(output) == {"vendor/templates"}


