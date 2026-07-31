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
    Movie Name (year).eng.srt
```

Handles both release folders (containing video + subtitles) and loose video files. Strips quality tags, codec info, release group names, and noise words. Detects editions (Director's Cut, Extended, Unrated, etc.) and emits `{edition-...}` tags.

## Prerequisites

- Python 3 (stdlib only, no pip dependencies)

## Usage

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
| `--sub-lang CODE` | Language code for subtitle files, e.g. `en` → `Movie (year).en.srt` (default: none) |
| `--no-editions` | Skip `{edition-...}` tags in folder/file names |

## Workflow

1. Ask the user for the movie library path
2. Run without `--apply` first (dry-run)
3. Present the planned moves to the user
4. Only run with `--apply` after explicit confirmation
