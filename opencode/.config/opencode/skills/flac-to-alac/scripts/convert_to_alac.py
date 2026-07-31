#!/usr/bin/env python3
"""
Convert FLAC files to ALAC (.m4a) while fully preserving tags and artwork.

- Audio is transcoded losslessly with ffmpeg (same bit depth / sample rate).
- ALL tags from the source FLAC (Vorbis comments) are copied into the
  destination file: well-known fields become proper MP4 atoms, and every
  other (non-standard) tag is preserved as an iTunes-style freeform atom
  (----:com.apple.iTunes:<NAME>) so nothing is lost (ReplayGain, AccurateRip,
  CTDB, Label, CatalogNumber, etc.)
- Embedded cover art is copied into the MP4 `covr` atom.
- Output mirrors the source directory structure under ./ALAC/, leaving the
  original FLAC files untouched. Already-converted files are skipped so the
  script is safely resumable.

Usage:
    <skill_dir>/.venv/bin/python convert_to_alac.py [SOURCE_ROOT] [OUTPUT_ROOT]

Defaults: SOURCE_ROOT = current working directory, OUTPUT_ROOT = SOURCE_ROOT/ALAC
"""

import subprocess
import sys
from pathlib import Path

from mutagen.flac import FLAC
from mutagen.mp4 import MP4, MP4Cover, MP4FreeForm

FREEFORM_MEAN = "com.apple.iTunes"

# Aliases (normalized: upper-case, spaces/underscores collapsed to single space)
# mapping to the canonical field they represent.
ALIASES = {
    "TITLE": "title",
    "ARTIST": "artist",
    "ALBUM": "album",
    "ALBUM ARTIST": "album_artist",
    "ALBUMARTIST": "album_artist",
    "DATE": "date",
    "YEAR": "date",
    "GENRE": "genre",
    "COMMENT": "comment",
    "TRACK": "track",
    "TRACKNUMBER": "track",
    "TRACKTOTAL": "tracktotal",
    "TOTALTRACKS": "tracktotal",
    "DISC": "disc",
    "DISCNUMBER": "disc",
    "DISCTOTAL": "disctotal",
    "TOTALDISCS": "disctotal",
}


def normalize_key(key: str) -> str:
    return " ".join(key.strip().upper().replace("_", " ").split())


def first(tags, *names):
    for n in names:
        vals = tags.get(n)
        if vals:
            return str(vals[0])
    return None


def to_int(value):
    if value is None:
        return None
    try:
        return int(str(value).strip())
    except ValueError:
        return None


def jpeg_or_png(data: bytes) -> int:
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return MP4Cover.FORMAT_PNG
    return MP4Cover.FORMAT_JPEG


def copy_tags(flac_path: Path, mp4_path: Path) -> None:
    src = FLAC(str(flac_path))
    dst = MP4(str(mp4_path))
    dst.clear()

    vc = src.tags or {}

    title = first(vc, "TITLE")
    artist = first(vc, "ARTIST")
    album = first(vc, "ALBUM")
    album_artist = first(vc, "ALBUM ARTIST", "ALBUMARTIST", "album_artist")
    date = first(vc, "DATE", "YEAR")
    genre = first(vc, "GENRE")
    comment = first(vc, "COMMENT")
    track = to_int(first(vc, "TRACKNUMBER", "TRACK", "track"))
    tracktotal = to_int(first(vc, "TRACKTOTAL", "TOTALTRACKS"))
    disc = to_int(first(vc, "DISCNUMBER", "DISC", "disc"))
    disctotal = to_int(first(vc, "DISCTOTAL", "TOTALDISCS"))

    if title:
        dst["\xa9nam"] = [title]
    if artist:
        dst["\xa9ART"] = [artist]
    if album:
        dst["\xa9alb"] = [album]
    if album_artist:
        dst["aART"] = [album_artist]
    if date:
        dst["\xa9day"] = [date]
    if genre:
        dst["\xa9gen"] = [genre]
    if comment:
        dst["\xa9cmt"] = [comment]
    if track is not None:
        dst["trkn"] = [(track, tracktotal or 0)]
    if disc is not None:
        dst["disk"] = [(disc, disctotal or 0)]

    # Every remaining tag -> freeform atom, so nothing is silently dropped.
    consumed_canonical = {
        "title", "artist", "album", "album_artist", "date", "genre",
        "comment", "track", "tracktotal", "disc", "disctotal",
    }
    seen_freeform_keys = set()
    for raw_key, values in vc.items():
        norm = normalize_key(raw_key)
        canonical = ALIASES.get(norm)
        if canonical in consumed_canonical:
            continue
        freeform_name = raw_key.strip()
        if freeform_name in seen_freeform_keys:
            continue
        seen_freeform_keys.add(freeform_name)
        joined = "; ".join(str(v) for v in values)
        key = f"----:{FREEFORM_MEAN}:{freeform_name}"
        dst[key] = [MP4FreeForm(joined.encode("utf-8"))]

    # Cover art
    covers = []
    for pic in src.pictures:
        covers.append(MP4Cover(pic.data, imageformat=jpeg_or_png(pic.data)))
    if covers:
        dst["covr"] = covers

    dst.save()


def convert_one(flac_path: Path, mp4_path: Path) -> None:
    mp4_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = mp4_path.with_suffix(".m4a.tmp")

    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-i", str(flac_path),
        "-map", "0:a",
        "-map_metadata", "-1",
        "-vn",
        "-c:a", "alac",
        "-f", "ipod",
        str(tmp_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr.strip()}")

    copy_tags(flac_path, tmp_path)
    tmp_path.rename(mp4_path)


def main():
    source_root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    output_root = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else source_root / "ALAC"

    flac_files = sorted(source_root.rglob("*.flac"))
    # Don't recurse into our own output tree if it happens to be under source_root.
    flac_files = [f for f in flac_files if output_root not in f.parents]

    total = len(flac_files)
    converted = 0
    skipped = 0
    failed = []

    print(f"Source: {source_root}")
    print(f"Output: {output_root}")
    print(f"Found {total} FLAC file(s).\n")

    for i, flac_path in enumerate(flac_files, 1):
        rel = flac_path.relative_to(source_root)
        mp4_path = output_root / rel.with_suffix(".m4a")

        if mp4_path.exists():
            skipped += 1
            print(f"[{i}/{total}] SKIP (exists): {rel}")
            continue

        print(f"[{i}/{total}] Converting: {rel}")
        try:
            convert_one(flac_path, mp4_path)
            converted += 1
        except Exception as e:
            failed.append((rel, str(e)))
            print(f"    FAILED: {e}")

    print("\n--- Summary ---")
    print(f"Converted: {converted}")
    print(f"Skipped (already existed): {skipped}")
    print(f"Failed: {len(failed)}")
    for rel, err in failed:
        print(f"  - {rel}: {err}")


if __name__ == "__main__":
    main()
