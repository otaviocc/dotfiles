#!/usr/bin/env python3
"""
organize-music.py

Organize music files into Artist/Album/Track Title structure based on audio tags.

Reads artist, album, title, track number, and disc number from audio file metadata
(via mutagen) and moves files into a clean hierarchy:

    root/
      Artist Name/
        Album Name/
          01 Track Title.flac
          02 Another Track.flac

Files with missing tags are skipped. Empty directories left behind after moves
are cleaned up automatically.

USAGE
    python3 organize-music.py --root /path/to/music              # dry run
    python3 organize-music.py --root /path/to/music --apply      # move files

OPTIONS
    --root PATH         Directory to scan (default: current directory).
    --apply             Execute the moves (default is dry run).
"""

import argparse
import os
import re
import shutil
import sys

import mutagen

AUDIO_EXTENSIONS = {".mp3", ".flac", ".m4a", ".ogg", ".aac", ".wma"}

UNSAFE_CHARS = re.compile(r'[\\/:*?"<>|]')


def sanitize(name):
    """Remove filesystem-unsafe characters from a string."""
    return UNSAFE_CHARS.sub("_", name).strip(". ")


def _first(tags, key, default=None):
    """Safely get the first value of a tag, tolerating missing or empty lists."""
    values = tags.get(key) or []
    return values[0] if values else default


def _parse_int_prefix(value, default):
    """Parse the leading integer of a "N" or "N/M" tag value, tolerating junk."""
    if not value:
        return default
    try:
        return int(value.split("/")[0].strip())
    except (ValueError, AttributeError):
        return default


def read_tags(filepath):
    """Read audio tags from a file. Returns None if required tags are missing
    or unusable (missing artist/album, or malformed tag data)."""
    try:
        audio = mutagen.File(filepath, easy=True)
    except Exception:
        return None

    if audio is None:
        return None

    tags = audio.tags
    if tags is None:
        return None

    try:
        artist = _first(tags, "artist")
        album = _first(tags, "album")
        title = _first(tags, "title")

        if not artist or not album:
            return None

        if not title:
            title = os.path.splitext(os.path.basename(filepath))[0]

        track_num = _parse_int_prefix(_first(tags, "tracknumber", "0"), 0)
        disc_num = _parse_int_prefix(_first(tags, "discnumber", "1"), 1)

        return {
            "artist": sanitize(artist),
            "album": sanitize(album),
            "title": sanitize(title),
            "track_num": track_num,
            "disc_num": disc_num,
        }
    except Exception:
        return None


def build_target_dir(root, tags):
    """Build the target directory path: root/Artist/Album."""
    return os.path.join(root, tags["artist"], tags["album"])


def build_target_filename(tags, ext, max_track):
    """Build the target filename with track number prefix."""
    width = 3 if max_track > 99 else 2
    prefix = f"{tags['track_num']:0{width}d}"

    if tags["disc_num"] > 1:
        prefix = f"{tags['disc_num']}-{prefix}"

    return f"{prefix} {tags['title']}{ext}"


def scan_files(root):
    """Recursively scan for audio files."""
    files = []
    for dirpath, _dirs, filenames in os.walk(root):
        for fn in filenames:
            if os.path.splitext(fn)[1].lower() in AUDIO_EXTENSIONS:
                files.append(os.path.join(dirpath, fn))
    return sorted(files)


def collect_moves(root, files):
    """Plan moves for all files. Returns (moves, warnings)."""
    album_tracks = {}
    file_tags = {}

    moves = []
    warnings = []
    claimed = {}  # abspath(target) -> source filepath that already claimed it

    for filepath in files:
        tags = read_tags(filepath)
        if tags is None:
            warnings.append(f"missing or unreadable tags: {os.path.relpath(filepath, root)}")
            continue

        file_tags[filepath] = tags
        key = (tags["artist"], tags["album"])
        album_tracks.setdefault(key, []).append(tags["track_num"])

    for filepath, tags in file_tags.items():
        key = (tags["artist"], tags["album"])
        max_track = max(album_tracks[key])

        target_dir = build_target_dir(root, tags)
        filename = build_target_filename(tags, os.path.splitext(filepath)[1].lower(),
                                         max_track)
        target_path = os.path.join(target_dir, filename)
        target_abs = os.path.abspath(target_path)

        if os.path.exists(target_path) and target_abs != os.path.abspath(filepath):
            warnings.append(f"target exists, skipping: {os.path.relpath(target_path, root)}")
            continue

        if os.path.abspath(filepath) == target_abs:
            continue

        if target_abs in claimed:
            warnings.append(
                f"duplicate target, skipping: {os.path.relpath(filepath, root)} "
                f"and {os.path.relpath(claimed[target_abs], root)} both map to "
                f"{os.path.relpath(target_path, root)}"
            )
            continue

        claimed[target_abs] = filepath
        moves.append((filepath, target_path))

    return moves, warnings


def remove_empty_dirs(root):
    """Remove empty directories recursively under root. Returns count removed."""
    count = 0
    for dirpath in sorted(
        (os.path.join(dp, d) for dp, dirs, files in os.walk(root, topdown=False)
         for d in dirs),
        reverse=True,
    ):
        try:
            if not os.listdir(dirpath):
                os.rmdir(dirpath)
                count += 1
        except OSError:
            pass
    return count


def main():
    ap = argparse.ArgumentParser(description="Organize music files by audio tags.")
    ap.add_argument("--root", default=".", help="Directory to scan (default: .)")
    ap.add_argument("--apply", action="store_true",
                    help="Execute the moves (default is dry run)")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    apply = args.apply

    if not os.path.isdir(root):
        print(f"Error: '{root}' is not a directory", file=sys.stderr)
        sys.exit(1)

    print(f"root={root}  mode={'APPLY' if apply else 'DRY RUN'}")
    print("-" * 70)

    files = scan_files(root)
    if not files:
        print("No audio files found.")
        sys.exit(0)

    moves, warnings = collect_moves(root, files)

    for src, dst in moves:
        print(f"{os.path.relpath(src, root)}\n   -> {os.path.relpath(dst, root)}")

    print("-" * 70)
    for w in warnings:
        print(f"  ?? {w}")
    print(f"{'moved' if apply else 'planned'}: {len(moves)}   "
          f"warnings: {len(warnings)}   "
          f"({'APPLY' if apply else 'DRY RUN — re-run with --apply to execute'})")

    if not moves:
        sys.exit(0)

    if apply:
        moved = 0
        for src, dst in moves:
            try:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.move(src, dst)
                moved += 1
            except Exception as e:
                print(f"  Error moving {os.path.relpath(src, root)}: {e}",
                      file=sys.stderr)

        removed = remove_empty_dirs(root)
        print(f"Moved {moved} files. Removed {removed} empty directories.")


if __name__ == "__main__":
    main()
