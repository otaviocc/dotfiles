---
name: add-episode-titles
description: Add missing episode titles and/or the premiere year to Jellyfin-organized TV show filenames using the TVMaze API. Use when asked to add, backfill, fill in, or complete episode names/titles, or when files are missing the year in their filename or show folder.
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

Also adds the premiere year when it is missing from the filename and/or show folder, resolving it from the TVMaze API:

```
TV Shows/
  Show Name/                       Show Name (year)/
    Season 01/                       Season 01/
      Show Name - s01e01 - Title.mkv   Show Name (year) - s01e01 - Title.mkv
```

This works even when the episode already has a title — if the year is absent, it is resolved from TVMaze and added to both the filename and the parent directory. Operates on files in the `Show Name (year) - sNNeNN.ext` or `Show Name - sNNeNN - Title.ext` format (e.g. produced by `organize-tv`). Episode names are looked up from the TVMaze API — free, no API key required. Subtitle files next to a renamed video are renamed to stay paired with it.

## Prerequisites

- Python 3 (stdlib only, no pip dependencies)
- Network access to `api.tvmaze.com`

## Usage

Paths below are relative to this skill's directory.

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
- When a file or its show folder is missing the year, it is resolved from TVMaze and added to both the filename and the parent directory — even when the episode already carries a title. This lets you run `organize-tv` first (which may produce year-less folders from scene releases) and backfill the year here. If the matched show has no premiere date on TVMaze, those files are reported under `no year` and left untouched rather than renamed to `Show (None) - ...`.
- When no match clears the threshold, the three closest TVMaze candidates are printed with their similarity scores, so you can tell the user whether lowering `--threshold` would help or whether the show is genuinely absent.
- Episode titles come from a remote API and routinely contain characters that are not legal in a filename. `/`, `\` and `|` become `-`; `:`, `?`, `"`, `*`, `<`, `>` are dropped. `"Hide and Seek: Part 1/2"` becomes `Hide and Seek Part 1-2`, never a stray subdirectory.
- Matching is done once per show, so a full library takes roughly 0.7s per show (two API calls, rate-limited). Network errors are retried before the show is given up on.
- Existing filenames are never overwritten; conflicts are reported and skipped before anything is renamed.
- Runs after `organize-tv` when `--minimal` was used, or whenever a source release lacked episode titles. Also useful after any `organize-tv` run that produced year-less folders, to backfill the premiere year from TVMaze.
