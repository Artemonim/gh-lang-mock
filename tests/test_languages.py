from pathlib import Path

from ghlangmock.languages import detect_language, primary_extension


def test_detect_language_common():
    assert detect_language(Path("a.py")) == "Python"
    assert detect_language(Path("b.TS")) == "TypeScript"  # suffix is lowercased
    assert detect_language(Path("c.cpp")) == "C++"
    assert detect_language(Path("index.html")) == "HTML"


def test_primary_extension_roundtrip():
    lang = detect_language(Path("script.js"))
    assert lang is not None
    ext = primary_extension(lang)
    assert ext.startswith(".")


