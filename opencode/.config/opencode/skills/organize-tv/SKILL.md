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
      Show Name (year) - s01e01 - Episode Title.srt
```

Handles show folders (with or without Season subfolders) and loose episode files. Detects multi-episode files (S01E01E02), editions, and strips release junk. Selects the longest title variant when multiple quality copies exist.

## Prerequisites

- Python 3 (stdlib only, no pip dependencies)

## Usage

Paths below are relative to this skill's directory.

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
| `--sub-lang CODE` | Language code for subtitle files, e.g. `en` → `... - s01e01.en.srt` (default: none) |
| `--bare-number-episodes` | Treat a trailing bare number (`Show Name 3`) as an episode number (off by default) |

## Workflow

1. Ask the user for the TV library path
2. Run without `--apply` first (dry-run)
3. Present the planned moves to the user
4. Only run with `--apply` after explicit confirmation

## Notes

- Most scene TV releases carry no year (`Severance.S01.1080p.ATVP.WEB-DL`). Those are filed under a year-less folder (`Severance/Season 01/Severance - s01e01 - Title.mkv`), which Jellyfin still matches, and the run reports which shows would benefit from having the year added. Only releases where no show name can be recovered at all are left untouched.
- Season numbers come from the filename's `sNNeNN` marker, falling back to a `Season NN` parent folder when the filename does not carry one.
- `--bare-number-episodes` is off by default so movies and specials are not mistaken for episodes. Turn it on for sources named `Show Name 1`, `Show Name 2`, etc. When it is on, the season still comes from the containing `Season NN` folder.
- Files with no detectable episode number are filed as **Season 00 specials**, numbered in filename order, keeping their original name as the episode title so they stay identifiable. A video and its subtitle are given the same number so the pair stays together.
- Nothing is overwritten. Two files that resolve to the same destination are reported before anything moves, and the larger one wins — this is the usual outcome when a library holds two quality copies of one episode.
- Case-only renames (`show (2019)` → `Show (2019)`) work correctly on case-insensitive filesystems.
- Moves use `shutil.move`, so a library spanning multiple mounts works.
- Empty leftover folders are removed after a successful `--apply`.

## Related

- Run `add-episode-titles` afterwards to backfill titles from TVMaze when the source release had none, or when `--minimal` was used.
