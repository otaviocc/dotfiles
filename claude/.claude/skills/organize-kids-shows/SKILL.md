---
name: organize-kids-shows
description: Organize kids show files into a Jellyfin-compatible library structure. Use when asked to tidy, rename, or sort a children's TV show collection.
---

# Organize Kids Shows

Variant of organize-tv tailored for kids shows. Organizes files into:

```
Kids Shows/
  Show Name (year)/
    Season 01/
      Show Name (year) - s01e01 - Episode Title.mkv
```

No edition tags (kids content rarely has them). Supports `--bare-number-episodes` for files named `Show 1`, `Show 2`, etc.

## Prerequisites

- Python 3 (stdlib only, no pip dependencies)

## Usage

Paths below are relative to this skill's directory.

```bash
python3 scripts/organize-kids-shows.py --root /path/to/kids
```

The script defaults to **dry-run** — it shows what would be moved without changing anything. Review the output, then confirm with the user before applying.

```bash
python3 scripts/organize-kids-shows.py --root /path/to/kids --apply
```

## Flags

| Flag | Description |
|------|-------------|
| `--root DIR` | Library root directory (default: current directory) |
| `--apply` | Execute moves (default: dry-run) |
| `--sub-lang CODE` | Language code for subtitle files (default: none) |
| `--bare-number-episodes` | Treat trailing bare numbers (e.g. `PAW Patrol 1`) as episode numbers (off by default) |

## Workflow

1. Ask the user for the kids shows library path
2. Run without `--apply` first (dry-run)
3. Present the planned moves to the user
4. Only run with `--apply` after explicit confirmation

## Notes

- Shows with no year in the name are filed under a year-less folder (`Peppa Pig/Season 03/...`), with release junk stripped from the title rather than carried into the folder name.
- `--bare-number-episodes` is off by default to avoid treating movies as episodes. A folder whose files carry no episode markers at all is reported and **left untouched**, with a hint to re-run with the flag if those files really are episodes.
- Season numbers come from the filename's `sNNeNN` marker, falling back to a `Season NN` parent folder.
- Files with no detectable episode number that sit *alongside* real episodes are filed as **Season 00 specials**, numbered in filename order and keeping their original name as the title, so bonus features are no longer left behind in the source folder.
- Nothing is overwritten. Two files that resolve to the same destination are reported before anything moves, and the larger one wins.
- Case-only renames work correctly on case-insensitive filesystems, and moves use `shutil.move` so a library spanning multiple mounts works.
- Empty leftover folders are removed after a successful `--apply`.
