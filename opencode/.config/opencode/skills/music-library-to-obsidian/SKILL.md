---
name: music-library-to-obsidian
description: Scan a ripped CD music library and create one Obsidian note per album, with YAML frontmatter (album, artist, year, tracks, discs), the embedded cover art, and a numbered track list. Also writes Albums.base and Artists.base for browsing the collection. Use when asked to catalogue, index, or document a music collection in Obsidian.
---

# Music Library to Obsidian

Recursively scans a music library, reads audio metadata via `ffprobe`, and
creates one Obsidian note per album. Notes are organised by artist folder
inside a configurable vault subfolder.

```
Music/
  Miles Davis/
    Kind of Blue (1959).md
    Bitches Brew (1970).md
    Artworks/
      Kind of Blue (1959).jpg
      Bitches Brew (1970).jpg
  Radiohead/
    OK Computer (1997).md
    ...
  Albums.base
  Artists.base
```

Each album note looks like:

```markdown
---
album: "Kind of Blue"
album_artist: "Miles Davis"
year: 1959
tracks: 5
discs: 1
tags:
  - music/collection
  - music/album
---

![[Music/Miles Davis/Artworks/Kind of Blue (1959).jpg]]

01. So What
02. Freddie Freeloader
03. Blue in Green
04. All Blues
05. Flamenco Sketches
```

Running the script again after ripping new albums rewrites existing notes so
the artwork path stays correct and track lists stay accurate.

Two Obsidian Bases are written to the vault subfolder root:

- **Albums.base** — table view (all albums, by-artist grouping) + gallery cards view
- **Artists.base** — albums grouped by artist with list and table views

## Prerequisites

- Python 3
- `mutagen` (`pip install mutagen`) — reads tag headers without spawning a subprocess per file, which matters on network-mounted libraries
- Obsidian open with the target vault (the `obsidian` CLI requires a running instance)

## Usage

Paths below are relative to this skill's directory.

```bash
python3 scripts/music-library-to-obsidian.py \
    --root /path/to/music \
    --vault /path/to/vault
```

The script defaults to **dry-run** — it shows what would be created without
touching the vault. Review the output, then confirm with the user before applying.

```bash
python3 scripts/music-library-to-obsidian.py \
    --root /path/to/music \
    --vault /path/to/vault \
    --apply
```

## Flags

| Flag | Description |
|------|-------------|
| `--root DIR` | Music library root to scan (required) |
| `--vault DIR` | Obsidian vault root directory (required) |
| `--folder NAME` | Subfolder inside the vault (default: `Music`) |
| `--tag TAG` | Tag applied to every album note (default: `music/collection`) |
| `--apply` | Write files (default: dry-run) |

## Workflow

1. Ask the user for the music library path and vault path
2. Run without `--apply` first to show the planned notes
3. Present the output — artists, albums, year, track counts, cover availability
4. Only run with `--apply` after explicit confirmation

## How notes are built

For each album the script:

1. Reads tags from every audio file via `ffprobe` (no pip install)
2. Picks the best cover: `folder.jpg` / `folder.jpeg` preferred, then the
   largest JPEG/PNG/WebP in the album directory
3. Copies the cover to `<Artist>/Artworks/<Album> (<Year>).ext`
4. Writes the album note with full YAML frontmatter and an embedded-artwork
   wikilink (`![[vault/relative/path.jpg]]`) above the numbered track list

## Notes

- **Artist field**: uses `albumartist` tag, falling back to `artist`. This
  keeps compilations filed under one artist rather than scattered.
- **Year**: read from the `date` tag (first 4 characters), falling back to
  `year`, `originaldate`, `originalyear`. Albums with no year sort last and
  note filename omits the year parenthetical.
- **Multi-disc albums**: when more than one disc number is found, tracks are
  prefixed `2-01`, `2-02`, etc. and grouped under **Disc N** headings.
- **Disc/track counts in frontmatter**: taken from the `N/M` denominator in
  the `tracknumber`/`discnumber` tags when available; otherwise derived from
  the actual tracks/discs found.
- **Idempotent**: re-running with `--apply` overwrites existing notes so
  newly ripped discs appear correctly. Artwork is **not** re-copied if the
  destination file already exists — delete the file from the vault and re-run
  to replace it.
- **Skipped files**: audio files missing both `artist`/`albumartist` and
  `album` tags are skipped with a warning shown at the end of the run.
- **Hidden files**: macOS `._*` sidecar files and directories starting with
  `.` are ignored.
- **Base files**: `Albums.base` and `Artists.base` are always overwritten on
  `--apply`. They filter on the `music/album` tag so they pick up all album
  notes regardless of subfolder.
