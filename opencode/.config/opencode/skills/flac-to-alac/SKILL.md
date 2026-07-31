---
name: flac-to-alac
description: Convert FLAC audio files to ALAC (.m4a) using ffmpeg, preserving metadata and embedded artwork. Use when asked to convert, transcode, or migrate a FLAC music library.
---

# FLAC to ALAC

Converts every FLAC file under a directory to ALAC (.m4a) using ffmpeg. Metadata and embedded album art are preserved via `-c:v copy -map 0`.

Optionally verifies lossless conversion by decoding both source and destination to raw PCM and comparing byte-for-byte.

## Prerequisites

- Python 3 (stdlib only, no pip dependencies)
- `ffmpeg` installed and on `$PATH` (macOS: `brew install ffmpeg`, Linux: `apt install ffmpeg` or your package manager)

## Usage

```bash
python3 scripts/flac-to-alac.py --root /path/to/music
```

The script defaults to **dry-run** — it shows what would be converted without changing anything. Review the output, then confirm with the user before applying.

```bash
python3 scripts/flac-to-alac.py --root /path/to/music --apply
```

## Flags

| Flag | Description |
|------|-------------|
| `--root DIR` | Directory to scan (default: current directory) |
| `--apply` | Execute conversions (default: dry-run) |
| `--keep-original` | Keep the FLAC file after conversion (default: delete on success) |
| `--no-verify` | Skip the lossless verification step |

## Workflow

1. Ask the user for the music library path
2. Check that `ffmpeg` is available (`which ffmpeg`)
3. Run without `--apply` first (dry-run)
4. Present the planned conversions to the user
5. Only run with `--apply` after explicit confirmation

## Notes

- If the `.m4a` destination already exists, the file is skipped.
- If the FLAC is deleted but the `.m4a` is 0 bytes, the FLAC is kept as a safety measure.
- Verification decodes both files to `pcm_s32le` and compares byte-for-byte.
