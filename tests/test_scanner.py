from pathlib import Path

from ghlangmock.scanner import scan_repository, compute_target_sizes


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


