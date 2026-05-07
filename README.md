## ghlangmock

The tool is designed to copy langbar from a closed source project to a open portfolio version of the project ([Example](https://github.com/Artemonim/portfolio-mock-Timeformer)).

This tool creates dummy files with language-appropriate extensions (e.g., .py, .js). It fills them with ASCII text so that the final byte size for each language group matches the language distribution in your source repository. You can control the total size of all generated files (e.g., to 10000 bytes) using the `--total-bytes` option. This allows you to accurately mock your project's language bar on GitHub.

### Install

```bash
pip install -e .[dev]
```

Or from the repo root for local development:

```bash
pip install -U pip
pip install -e .
pip install pytest pytest-cov
```

### Usage

```bash
ghlangmock <SOURCE_DIR> <DEST_PARENT_DIR> [--seed PATH] [--random|-Random] [--total-bytes N] [--max-files-per-language K] [--min-file-bytes M] [--no-overwrite]
```

- `SOURCE_DIR`: Path to the repository to scan (respects .gitignore files).
- `DEST_PARENT_DIR`: Existing directory under which the tool creates the `dummy-code/` subdirectory. Pass the parent folder (for example `../my-portfolio`), not the final `dummy-code` path, otherwise you will end up with `dummy-code/dummy-code`.
- `--seed PATH`: ASCII text file whose contents are repeated into dummy files.
- `--random`, `-Random`: Use cryptographically secure random ASCII (overrides seed).
- `--total-bytes N`: Target total bytes in the generated directory (default: 100000).
- `--max-files-per-language K`: Split each language into up to K files (default: 1).
- `--min-file-bytes M`: Minimum file size in bytes when splitting (default: 1).
- `--no-overwrite`: Prevent clearing the destination directory. By default, the destination is always cleared before generation.

### Example

```bash
ghlangmock . ../app_showreel
```

This command scans the current directory and writes generated files into `../app_showreel/dummy-code/`.

### Testing

```bash
pytest
```

Coverage is configured to fail below 75% by default.

### Notes

- Sensitive information is never read or embedded; only file sizes and extensions are considered.
- Only ASCII payloads are written to generated files.
- For ambiguous extensions (for example `.rs`), generated payloads include short Linguist-friendly language hints while still preserving exact per-file byte sizes.
- Registered git submodules are excluded from scanning. The tool reads submodule paths from `.gitmodules` and (when Git metadata is available) from git index `gitlink` entries (`git ls-files --stage`, mode `160000`).
- If Git metadata is unavailable, `.gitmodules` still drives exclusion; if both sources are unavailable, all directories are treated as regular folders.


