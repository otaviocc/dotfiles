---
name: flac-to-alac
description: Convert FLAC audio files to ALAC (.m4a) using ffmpeg, preserving metadata and embedded artwork. Use when asked to convert, transcode, or migrate a FLAC music library.
---

# FLAC to ALAC

Converts every FLAC file under a directory to ALAC (.m4a) using ffmpeg. Metadata and embedded album art are preserved via `-c:v copy -map 0`.

By default each conversion is verified lossless: source and destination are decoded to raw PCM and their digests compared. **The FLAC is deleted only after that check passes.**

## Prerequisites

- Python 3 (stdlib only, no pip dependencies)
- `ffmpeg` installed and on `$PATH` (macOS: `brew install ffmpeg`, Linux: `apt install ffmpeg` or your package manager)

## Usage

Paths below are relative to this skill's directory.

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
| `--keep-original` | Keep the FLAC after conversion (default: delete once verified) |
| `--no-verify` | Skip the lossless verification step. Implies the FLAC is kept |
| `--force-delete` | Delete the FLAC even though verification was skipped |
| `--jobs N` | Convert N files in parallel (default: 4, capped at CPU count) |

## Workflow

1. Ask the user for the music library path
2. Check that `ffmpeg` is available (`which ffmpeg`)
3. Run without `--apply` first (dry-run)
4. Present the planned conversions to the user
5. Only run with `--apply` after explicit confirmation

## Safety

- **A source FLAC is only ever deleted after its conversion verified as lossless.** If verification fails the FLAC is kept, the file is listed as `VERIFY FAILED`, and the script exits non-zero.
- `--no-verify` alone will not delete anything; deleting unverified conversions requires the explicit `--no-verify --force-delete` combination.
- Output is written to a temp file and atomically renamed into place, so an interrupted run cannot leave a truncated `.m4a` that a later run would mistake for a finished conversion. Stale temp files from a previous interrupted run are swept at the start of an `--apply`.

## Notes

- If the `.m4a` destination already exists, the file is skipped.
- Verification decodes both files to `pcm_s32le` and compares a streaming digest, so memory use stays flat regardless of track length.
- If a cover image cannot be copied into the MP4 container, the conversion is retried without the artwork rather than failing, and the file is reported as `artwork dropped`.
- Hidden directories and macOS `._*` sidecar files are ignored.
