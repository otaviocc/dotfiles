---
name: organize-tv
description: Organize TV show files into a Jellyfin-compatible library structure (TV Shows/Title (year)/Season NN/). Use when asked to rename, sort, or clean up a TV show collection.
---

# Organize TV Shows

Algorithmically parses scene-style TV filenames and organizes them into the Jellyfin convention:

```
TV Shows/
  Show Name (year)/
    Season 01/
      Show Name (year) - s01e01 - Episode Title.mkv
      Show Name (year) - s01e01 - Episode Title.eng.srt
```

Handles show folders (with or without Season subfolders) and loose episode files. Detects multi-episode files (S01E01E02), editions, and strips release junk. Selects the longest title variant when multiple quality copies exist.

## Prerequisites

- Python 3 (stdlib only, no pip dependencies)

## Usage

```bash
python3 scripts/organize-tv.py --root /path/to/tv
```

The script defaults to **dry-run** — it shows what would be moved without changing anything. Review the output, then confirm with the user before applying.

```bash
python3 scripts/organize-tv.py --root /path/to/tv --apply
```

## Flags

| Flag | Description |
|------|-------------|
| `--root DIR` | Library root directory (default: current directory) |
| `--apply` | Execute moves (default: dry-run) |
| `--minimal` | Drop episode titles from filenames (e.g. `Show (year) - s01e01.mkv`) |
| `--sub-lang CODE` | Language code for subtitle files (default: `en`) |

## Workflow

1. Ask the user for the TV library path
2. Run without `--apply` first (dry-run)
3. Present the planned moves to the user
4. Only run with `--apply` after explicit confirmation
