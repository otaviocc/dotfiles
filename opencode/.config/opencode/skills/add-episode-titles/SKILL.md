---
name: add-episode-titles
description: Add missing episode titles to Jellyfin-organized TV show filenames (e.g. "Show (year) - s01e01.mkv" -> "Show (year) - s01e01 - Episode Title.mkv") using the TVMaze API. Use when asked to add, backfill, fill in, or complete episode names/titles for TV files.
---

# Add Episode Titles

Backfills episode titles into TV filenames that are missing them, following the Jellyfin show-naming convention:

```
TV Shows/
  Show Name (year)/
    Season 01/
      Show Name (year) - s01e01.mkv
        -> Show Name (year) - s01e01 - Episode Title.mkv
```

Operates only on files already in the organized `Show Name (year) - sNNeNN.ext` format (e.g. produced by `organize-tv`). Files that already carry an episode title are left alone. Episode names are looked up from the TVMaze API — free, no API key required. Subtitle files next to a renamed video are renamed to stay paired with it.

## Prerequisites

- Python 3 (stdlib only, no pip dependencies)
- Network access to `api.tvmaze.com`

## Usage

```bash
python3 scripts/add-episode-titles.py --root /path/to/tv
```

The script defaults to **dry-run** — it shows what would be renamed without changing anything. Review the output, then confirm with the user before applying.

```bash
python3 scripts/add-episode-titles.py --root /path/to/tv --apply
```

## Flags

| Flag | Description |
|------|-------------|
| `--root DIR` | Library root directory (default: current directory) |
| `--apply` | Execute the renames (default: dry-run) |
| `--multi-ep-first` | Use the first episode's title for multi-episode files (`s01e01-e02`); skipped by default |
| `--threshold FLOAT` | Minimum title similarity (0–1) to accept a TVMaze show match (default: `0.75`) |
| `--timeout SECONDS` | HTTP timeout for TVMaze requests (default: `15`) |

## Workflow

1. Ask the user for the TV library path
2. Run without `--apply` first (dry-run)
3. Present the planned renames to the user
4. Only run with `--apply` after explicit confirmation

## Notes

- The show is resolved against TVMaze by title; a nearby premiere year gives a matching bonus, and the title must clear `--threshold` (default 0.75). Unmatched shows and episodes are reported and skipped, never guessed.
- Runs after `organize-tv` when `--minimal` was used, or whenever a source release lacked episode titles.
- Matching is done once per show, so a full library takes roughly 0.7s per show (two API calls, rate-limited).
- Existing filenames are never overwritten; conflicts are reported and skipped.
