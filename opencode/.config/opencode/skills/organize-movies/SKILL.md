---
name: organize-movies
description: Organize movie files into a Jellyfin-compatible library structure (Movies/Title (year)/). Use when asked to rename, sort, or clean up a movie collection.
---

# Organize Movies

Algorithmically parses scene-style movie filenames and organizes them into the Jellyfin convention:

```
Movies/
  Movie Name (year)/
    Movie Name (year).mkv
    Movie Name (year).english.srt
```

Handles both release folders (containing video + subtitles, including a nested `Subs/` directory) and loose video files. Strips quality tags, codec info, release group names, and noise words. Detects editions (Director's Cut, Extended, Unrated, etc.) and emits `{edition-...}` tags.

## Prerequisites

- Python 3 (stdlib only, no pip dependencies)

## Usage

Paths below are relative to this skill's directory.

```bash
python3 scripts/organize-movies.py --root /path/to/movies
```

The script defaults to **dry-run** — it shows what would be moved without changing anything. Review the output, then confirm with the user before applying.

```bash
python3 scripts/organize-movies.py --root /path/to/movies --apply
```

## Flags

| Flag | Description |
|------|-------------|
| `--root DIR` | Library root directory (default: current directory) |
| `--apply` | Execute moves (default: dry-run) |
| `--sub-lang CODE` | Force a language code on subtitle files, e.g. `en` → `Movie (year).en.srt` (default: keep whatever the file already carries) |
| `--no-editions` | Skip `{edition-...}` tags in folder/file names |

## Workflow

1. Ask the user for the movie library path
2. Run without `--apply` first (dry-run)
3. Present the planned moves to the user
4. Only run with `--apply` after explicit confirmation

## Notes

- Release folders are walked recursively, so subtitles in a nested `Subs/` directory are collected instead of being left behind.
- Without `--sub-lang`, a language code already present on a subtitle (`2_English.srt` → `.english.srt`) is preserved, which keeps multi-language subtitle sets distinguishable. `--sub-lang` overrides that for every subtitle.
- The release year is the last year-like token before the quality tail, so titles containing a number are safe (`Blade Runner 2049 2017` → year 2017).
- Nothing is overwritten. Two files that resolve to the same destination are reported before anything moves, and the larger one wins.
- Case-only renames work correctly on case-insensitive filesystems, and moves use `shutil.move` so a library spanning multiple mounts works.
- Files with no detectable year are reported and left alone.
- Empty leftover folders are removed after a successful `--apply`.
