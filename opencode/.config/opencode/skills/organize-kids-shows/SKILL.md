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
| `--bare-number-episodes` | Treat trailing bare numbers (e.g. `PAW Patrol 1`) as season 1 episodes (off by default) |

## Workflow

1. Ask the user for the kids shows library path
2. Run without `--apply` first (dry-run)
3. Present the planned moves to the user
4. Only run with `--apply` after explicit confirmation

## Notes

- `--bare-number-episodes` is off by default to avoid treating movies as episodes. Enable it when the library contains shows with bare-number filenames.
