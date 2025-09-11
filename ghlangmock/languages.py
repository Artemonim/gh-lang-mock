"""Language mapping utilities.

This module defines a pragmatic subset of GitHub Linguist's extension-to-language
mapping and provides helpers for determining a file's language and the primary
extension for a language.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional


# * A pragmatic extension-to-language mapping that covers common cases.
EXTENSION_TO_LANGUAGE: Dict[str, str] = {
    # * Programming languages
    ".py": "Python",
    ".pyw": "Python",
    ".pyx": "Cython",
    ".js": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".scala": "Scala",
    ".go": "Go",
    ".rb": "Ruby",
    ".php": "PHP",
    ".rs": "Rust",
    ".swift": "Swift",
    ".cs": "C#",
    ".c": "C",
    ".h": "C",
    ".cpp": "C++",
    ".cxx": "C++",
    ".cc": "C++",
    ".hpp": "C++",
    ".hh": "C++",
    ".mm": "Objective-C++",
    ".m": "Objective-C",
    ".sh": "Shell",
    ".ps1": "PowerShell",
    ".psm1": "PowerShell",
    ".bat": "Batchfile",
    ".pl": "Perl",
    ".r": "R",
    ".dart": "Dart",
    ".lua": "Lua",
    ".hs": "Haskell",
    ".erl": "Erlang",
    ".ex": "Elixir",
    ".exs": "Elixir",

    # * Markup / data formats often counted by Linguist
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".less": "Less",
    ".xml": "XML",
    ".xhtml": "XML",
    ".json": "JSON",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".toml": "TOML",
    ".ini": "INI",
    ".md": "Markdown",
    ".rst": "reStructuredText",
    ".vue": "Vue",
    ".svelte": "Svelte",
}


# * Primary extension per language for dummy file generation
PRIMARY_EXTENSION: Dict[str, str] = {
    "Python": ".py",
    "Cython": ".pyx",
    "JavaScript": ".js",
    "TypeScript": ".ts",
    "Java": ".java",
    "Kotlin": ".kt",
    "Scala": ".scala",
    "Go": ".go",
    "Ruby": ".rb",
    "PHP": ".php",
    "Rust": ".rs",
    "Swift": ".swift",
    "C#": ".cs",
    "C": ".c",
    "C++": ".cpp",
    "Objective-C++": ".mm",
    "Objective-C": ".m",
    "Shell": ".sh",
    "PowerShell": ".ps1",
    "Batchfile": ".bat",
    "Perl": ".pl",
    "R": ".r",
    "Dart": ".dart",
    "Lua": ".lua",
    "Haskell": ".hs",
    "Erlang": ".erl",
    "Elixir": ".ex",
    # * Markup / data
    "HTML": ".html",
    "CSS": ".css",
    "SCSS": ".scss",
    "Less": ".less",
    "XML": ".xml",
    "JSON": ".json",
    "YAML": ".yml",
    "TOML": ".toml",
    "INI": ".ini",
    "Markdown": ".md",
    "reStructuredText": ".rst",
    "Vue": ".vue",
    "Svelte": ".svelte",
}


def detect_language(file_path: Path) -> Optional[str]:
    """Detect a file's language from its extension.

    Args:
        file_path: Path to the file.

    Returns:
        The language name if recognized, otherwise None.
    """
    suffix = file_path.suffix.lower()
    return EXTENSION_TO_LANGUAGE.get(suffix)


def primary_extension(language: str) -> str:
    """Get the primary extension for a language.

    Args:
        language: Language name.

    Returns:
        The canonical extension for the language (including the dot).

    Raises:
        KeyError: If no primary extension is known for the language.
    """
    return PRIMARY_EXTENSION[language]


