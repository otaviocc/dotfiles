---
name: music-library-to-bear
description: Scan a ripped CD music library and create one Bear note per artist, listing all albums sorted by year with cover art and track lists. Use when asked to catalogue, index, or document a music collection in Bear, or when the user wants to check which CDs they own while browsing a store.
---

# Music Library to Bear

Recursively scans a music library, reads audio metadata via `mutagen`, and
creates (or updates) one Bear note per artist. Each note lists every album in
chronological order with the album cover embedded above the track list.

```
# Miles Davis

## Kind of Blue (1959)

[cover image]

01. So What
02. Freddie Freeloader
...

## Bitches Brew (1970)

[cover image]

01. Pharaoh's Dance
...
```

Running the script again after ripping new CDs always rewrites the note so
the year-sorted order stays correct.

## Prerequisites

- Python 3 (stdlib only — no pip dependencies)
- `ffprobe` — part of ffmpeg (`brew install ffmpeg`)
- Bear 2.8 or later installed at `/Applications/Bear.app`

## Usage

Paths below are relative to this skill's directory.

```bash
python3 scripts/music-library-to-bear.py --root /path/to/music
```

The script defaults to **dry-run** — it shows what would be created without
touching Bear. Review the output, then confirm with the user before applying.

```bash
python3 scripts/music-library-to-bear.py --root /path/to/music --apply
```

## Flags

| Flag | Description |
|------|-------------|
| `--root DIR` | Music library root to scan (required) |
| `--tag TAG` | Bear tag applied to all notes (default: `music/collection`) |
| `--apply` | Write notes to Bear (default: dry-run) |

## Workflow

1. Ask the user for the music library root path
2. Run without `--apply` first (dry-run) to show the planned notes
3. Present the output to the user — artists, albums, year, track counts, cover availability
4. Only run with `--apply` after explicit confirmation

## How notes are built

For each artist the script performs four steps:

1. **Create** the note with track lists only (no images yet), using
   `bearcli create --if-not-exists` to get the note ID, then immediately
   overwrites it so the year-sorted order is always up to date.
2. **Attach** each album cover via `bearcli attachments add`, naming the
   file `YEAR - Album Name.jpg` to keep attachments identifiable.
3. **Re-read** the note with `bearcli cat --format json` to collect the
   actual markdown links Bear generated (Bear renames on collision, e.g.
   `cover 2.jpg`).
4. **Overwrite** the note a final time with covers placed inline under
   each album heading.

## Notes

- **Artist field**: uses `albumartist` tag, falling back to `artist`. This
  keeps compilation albums and guest-featured tracks filed under one artist
  folder instead of being scattered.
- **Year**: read from the `date` tag (first 4 characters), falling back to
  `year`, `originaldate`, `originalyear`. Albums with no year sort last and
  display as `Unknown Year`.
- **Cover detection**: `folder.jpg` or `folder.jpeg` (case-insensitive) wins.
  If neither exists, the largest JPEG in the album directory is used.
- **Multi-disc albums**: tracks are prefixed `2-01`, `2-02`, etc. when the
  disc number is greater than 1.
- **Always overwrites**: the note is rewritten on every run so newly ripped
  albums appear in the correct chronological position.
- **Skipped files**: audio files missing both `artist`/`albumartist` or
  `album` tags are skipped with a warning. All warnings are shown at the end
  of the run.
- **Hidden files**: macOS `._*` sidecar files and directories starting with
  `.` are ignored.
- **bearcli path**: `/Applications/Bear.app/Contents/MacOS/bearcli`. If Bear
  is installed elsewhere, edit the `BEARCLI` constant at the top of the script.
