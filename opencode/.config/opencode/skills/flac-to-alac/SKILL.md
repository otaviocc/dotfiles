---
name: flac-to-alac
description: Convert a folder tree of FLAC music files to Apple Lossless (ALAC .m4a) while fully preserving every tag (title, artist, album, ReplayGain, AccurateRip, CTDB, Label, CatalogNumber, etc.) and embedded cover art, and verify afterwards that no file failed or got truncated mid-conversion. Use when asked to convert FLAC to ALAC/Apple Lossless/m4a, batch-convert an album/music library, or to check/verify a previous FLAC→ALAC conversion for missing or corrupt files.
---

# FLAC to ALAC conversion

Converts nested folders of `.flac` albums into ALAC (`.m4a`) losslessly,
while preserving **all** tags — not just the common ones. Plain `ffmpeg -c:a
alac` silently drops any non-standard Vorbis comment (ReplayGain,
AccurateRip*, CTDB*, Label, LabelNo, CatalogNumber, dynamic range, etc.),
which is why this skill uses `ffmpeg` for lossless audio transcoding plus
`mutagen` (Python) for a manual, complete tag copy.

## What the scripts do

- `scripts/convert_to_alac.py SOURCE_ROOT [OUTPUT_ROOT]`
  - Recursively finds all `*.flac` under `SOURCE_ROOT`.
  - For each file: encodes audio-only to ALAC via `ffmpeg` (bit-depth /
    sample rate unchanged — bit-exact/lossless, no resampling).
  - Copies every tag from the source FLAC into the new file with `mutagen`:
    - Well-known fields → proper MP4 atoms: title, artist, album, album
      artist, date, genre, comment, track/tracktotal (`trkn`), disc/disctotal
      (`disk`).
    - Every other tag → `----:com.apple.iTunes:<NAME>` freeform atom, so
      nothing is silently dropped.
    - Embedded cover art → `covr` atom (copied byte-for-byte).
  - Mirrors `SOURCE_ROOT`'s directory structure under `OUTPUT_ROOT` (default:
    `SOURCE_ROOT/ALAC`). Original FLAC files are never modified or deleted.
  - Skips files whose `.m4a` output already exists, so it is safe to re-run
    (e.g. after an interrupted batch, or when new albums are added later).

- `scripts/verify_conversion.py SOURCE_ROOT [OUTPUT_ROOT]`
  - For every source `.flac`, confirms the corresponding `.m4a` exists, is
    readable (not corrupt/truncated), has a matching sample rate, and has an
    **exact matching sample count** (catches truncation that a rounded
    duration display could hide — important after an interrupted run).
  - Prints a summary and exits non-zero if any problems are found.

Both scripts default `SOURCE_ROOT` to the current working directory and
`OUTPUT_ROOT` to `SOURCE_ROOT/ALAC` if not given.

## Usage

This skill directory bundles its own venv with `mutagen` pre-installed —
no per-run setup needed. Always invoke the venv's Python explicitly (do not
rely on system `python3`, which won't have `mutagen`).

```bash
SKILL_DIR=~/.config/opencode/skills/flac-to-alac

# Convert (run from, or point at, the music library root)
"$SKILL_DIR/.venv/bin/python" "$SKILL_DIR/scripts/convert_to_alac.py" /path/to/music/library

# Verify afterwards (especially if the convert run was interrupted, e.g. a
# shell timeout) — re-run convert first to fill in any gaps, then verify.
"$SKILL_DIR/.venv/bin/python" "$SKILL_DIR/scripts/verify_conversion.py" /path/to/music/library
```

Output goes to `/path/to/music/library/ALAC/...` by default, mirroring the
original folder structure, with the FLACs left untouched.

## Notes / gotchas

- Conversions of large libraries can take a while; run in the background
  (`nohup ... &` + poll the log) rather than a single foreground call, to
  avoid the shell tool's own command timeout killing the process mid-batch.
  If that does happen, it's safe: the script writes to a `.m4a.tmp` file and
  only renames it to `.m4a` after tags are fully copied, so a kill mid-file
  leaves an orphaned `.tmp`, never a corrupt `.m4a`. Just re-run
  `convert_to_alac.py` (it resumes) and then `verify_conversion.py` to
  confirm everything is intact.
- If the venv is ever missing or broken, recreate it with:
  ```bash
  cd ~/.config/opencode/skills/flac-to-alac
  python3 -m venv .venv
  ./.venv/bin/pip install --upgrade pip
  ./.venv/bin/pip install mutagen
  ```
- Requires `ffmpeg` on `PATH` (with ALAC encoder support, true of any modern
  build, e.g. via `brew install ffmpeg`).
