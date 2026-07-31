---
name: organize-music
description: Organize music files into an Artist/Album/Track structure based on audio metadata tags. Use when asked to sort, tidy, or organize a music library.
---

# Organize Music

Reads audio metadata (artist, album, title, track number, disc number) via mutagen and moves files into a clean hierarchy:

```
Music/
  Artist Name/
    Album Name/
      01 Track Title.flac
      02 Another Track.flac
```

Files with missing tags are skipped. Empty directories left behind after moves are cleaned up automatically.

## Prerequisites

- Python 3
- `mutagen` (`pip install mutagen`)

## Usage

```bash
python3 scripts/organize-music.py --root /path/to/music
```

The script defaults to **dry-run** — it shows what would be moved without changing anything. Review the output, then confirm with the user before applying.

```bash
python3 scripts/organize-music.py --root /path/to/music --apply
```

## Flags

| Flag | Description |
|------|-------------|
| `--root DIR` | Directory to scan (default: current directory) |
| `--apply` | Execute moves (default: dry-run) |

## Workflow

1. Ask the user for the music library path
2. Run without `--apply` first (dry-run)
3. Present the planned moves to the user
4. Only run with `--apply` after explicit confirmation

## Notes

- Files are skipped if the `artist` or `album` tag is missing. If `title` is missing, the original filename stem is used.
- Track numbers are zero-padded to 2 or 3 digits depending on the highest track in each album.
- Disc numbers > 1 produce a `Disc-Track` prefix (e.g. `2-01 Track Title.flac`).
