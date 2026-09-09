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

Paths below are relative to this skill's directory.

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
| `--albumartist` | Use the `albumartist` tag for the top-level folder, falling back to `artist` |

## Workflow

1. Ask the user for the music library path
2. Run without `--apply` first (dry-run)
3. Present the planned moves to the user
4. Only run with `--apply` after explicit confirmation

## Notes

- Files are skipped if the `artist` or `album` tag is missing. If `title` is missing, the original filename stem is used.
- `--albumartist` keeps compilations and guest-featured tracks filed under one folder instead of scattering them across per-track artists. Suggest it when the dry run shows an album split across several artist folders.
- Track numbers are zero-padded to 2 or 3 digits depending on the highest track in each album.
- Disc numbers > 1 produce a `Disc-Track` prefix (e.g. `2-01 Track Title.flac`).
- Characters that are illegal in a path component are rewritten: `/`, `\` and `|` become `-`, and `:`, `?`, `"`, `*`, `<`, `>` are dropped (`AC/DC` → `AC-DC`, `Kind of Blue: Legacy` → `Kind of Blue Legacy`).
- Nothing is overwritten. Two files that resolve to the same destination are reported before anything moves, and the larger one wins.
- Case-only renames work correctly on case-insensitive filesystems, and moves use `shutil.move` so a library spanning multiple mounts works.
- Hidden directories and macOS `._*` sidecar files are ignored.
