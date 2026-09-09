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
    --albumartist       Prefer the albumartist tag over artist for the top-level
                        folder, so compilations and featured tracks stay together.
"""

import argparse
import os
import re
import shutil
import sys

try:
    import mutagen
except ImportError:
    print("Error: mutagen is required. Install with: pip install mutagen",
          file=sys.stderr)
    sys.exit(1)

AUDIO_EXTENSIONS = {".mp3", ".flac", ".m4a", ".ogg", ".aac", ".wma", ".opus", ".wav"}

# Characters that are illegal or troublesome in a path component on the
# filesystems a media library is typically served from (APFS, ext4, SMB/NTFS).
UNSAFE_DASH_RE = re.compile(r"[/\\|]")
UNSAFE_DROP_RE = re.compile(r'[:?"*<>\x00-\x1f]')


def safe_component(name):
    """Make a string safe to use as a single path component."""
    name = UNSAFE_DASH_RE.sub("-", name)
    name = UNSAFE_DROP_RE.sub("", name)
    name = re.sub(r"\s+", " ", name).strip(" .")
    return name or "_"


def _first(tags, key, default=None):
    """Safely get the first value of a tag, tolerating missing or empty lists."""
    values = tags.get(key) or []
    return values[0] if values else default


def _parse_int_prefix(value, default):
    """Parse the leading integer of a "N" or "N/M" tag value, tolerating junk."""
    if not value:
        return default
    try:
        return int(str(value).split("/")[0].strip())
    except (ValueError, AttributeError):
        return default


def read_tags(filepath, prefer_albumartist):
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
        album_artist = _first(tags, "albumartist")
        if prefer_albumartist:
            artist = album_artist or artist
        album = _first(tags, "album")
        title = _first(tags, "title")

        if not artist or not album:
            return None

        if not title:
            title = os.path.splitext(os.path.basename(filepath))[0]

        track_num = _parse_int_prefix(_first(tags, "tracknumber", "0"), 0)
        disc_num = _parse_int_prefix(_first(tags, "discnumber", "1"), 1)

        return {
            "artist": safe_component(artist),
            "album": safe_component(album),
            "title": safe_component(title),
            "track_num": track_num,
            "disc_num": disc_num,
        }
    except Exception:
        return None


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
    for dirpath, dirs, filenames in os.walk(root):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fn in filenames:
            if fn.startswith("._"):      # macOS AppleDouble sidecar
                continue
            if os.path.splitext(fn)[1].lower() in AUDIO_EXTENSIONS:
                files.append(os.path.join(dirpath, fn))
    return sorted(files)


def collect_moves(root, files, prefer_albumartist):
    """Plan moves for all files. Returns (moves, warnings)."""
    album_tracks = {}
    file_tags = {}
    moves = []
    warnings = []

    for filepath in files:
        tags = read_tags(filepath, prefer_albumartist)
        if tags is None:
            warnings.append(
                f"missing or unreadable tags: {os.path.relpath(filepath, root)}"
            )
            continue
        file_tags[filepath] = tags
        key = (tags["artist"], tags["album"])
        album_tracks.setdefault(key, []).append(tags["track_num"])

    for filepath, tags in file_tags.items():
        key = (tags["artist"], tags["album"])
        max_track = max(album_tracks[key])
        target_dir = os.path.join(root, tags["artist"], tags["album"])
        filename = build_target_filename(
            tags, os.path.splitext(filepath)[1].lower(), max_track
        )
        moves.append((filepath, os.path.join(target_dir, filename)))

    return moves, warnings


def execute_moves(moves, root, apply):
    """Print, validate and optionally perform a list of (src, dst) moves.

    Resolves destinations claimed by several sources in favour of the largest
    file, refuses to overwrite anything already on disk, and defers a move whose
    destination is still held by a file that is itself scheduled to move away.
    Returns (done, skipped, errors).
    """
    def rel(path):
        return os.path.relpath(path, root)

    def rank(item):
        """Best candidate first: largest file, then longest name."""
        try:
            size = os.path.getsize(item[0])
        except OSError:
            size = 0
        return (-size, -len(os.path.basename(item[0])), item[0])

    problems = []
    skipped = 0

    order, by_dst = [], {}
    for src, dst in moves:
        if os.path.abspath(src) == os.path.abspath(dst):
            continue
        key = os.path.abspath(dst)
        if key not in by_dst:
            by_dst[key] = []
            order.append(key)
        by_dst[key].append((src, dst))

    winners = []
    for key in order:
        items = by_dst[key]
        if len(items) > 1:
            items = sorted(items, key=rank)
            for src, dst in items[1:]:
                problems.append(
                    f"duplicate target: keeping {rel(items[0][0])}, skipping "
                    f"{rel(src)} (both map to {rel(dst)})"
                )
                skipped += 1
        winners.append(items[0])

    sources = {os.path.abspath(src) for src, _ in winners}
    queue = []
    for src, dst in winners:
        in_place = False
        if os.path.exists(dst):
            try:
                in_place = os.path.samefile(src, dst)
            except OSError:
                in_place = False
            if not in_place and os.path.abspath(dst) not in sources:
                problems.append(f"target exists, skipping: {rel(dst)}")
                skipped += 1
                continue
        queue.append((src, dst, in_place))

    for src, dst, _ in queue:
        print(f"{rel(src)}\n   -> {rel(dst)}")
    for problem in problems:
        print(f"  !! {problem}")

    if not apply:
        return len(queue), skipped, 0

    done = errors = 0
    remaining = queue
    while remaining:
        ready = [m for m in remaining if m[2] or not os.path.exists(m[1])]
        blocked = [m for m in remaining if not (m[2] or not os.path.exists(m[1]))]
        if not ready:
            for _src, dst, _flag in blocked:
                print(f"  !! blocked, target still occupied: {rel(dst)}",
                      file=sys.stderr)
                skipped += 1
            break
        for src, dst, _flag in ready:
            try:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.move(src, dst)
                done += 1
            except OSError as exc:
                print(f"  !! error moving {rel(src)}: {exc}", file=sys.stderr)
                errors += 1
        remaining = blocked
    return done, skipped, errors


def prune_empty_dirs(root):
    """Remove empty directories under root. Returns count removed."""
    removed = 0
    root_abs = os.path.abspath(root)
    for dirpath, _dirs, _files in os.walk(root, topdown=False):
        if os.path.abspath(dirpath) == root_abs:
            continue
        try:
            if not os.listdir(dirpath):
                os.rmdir(dirpath)
                removed += 1
        except OSError:
            pass
    return removed


def main():
    ap = argparse.ArgumentParser(description="Organize music files by audio tags.")
    ap.add_argument("--root", default=".", help="Directory to scan (default: .)")
    ap.add_argument("--apply", action="store_true",
                    help="Execute the moves (default is dry run)")
    ap.add_argument("--albumartist", action="store_true",
                    help="Prefer the albumartist tag for the top-level folder")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    apply = args.apply

    if not os.path.isdir(root):
        print(f"Error: '{root}' is not a directory", file=sys.stderr)
        sys.exit(1)

    print(f"root={root}  mode={'APPLY' if apply else 'DRY RUN'}  "
          f"artist-tag={'albumartist' if args.albumartist else 'artist'}")
    print("-" * 70)

    files = scan_files(root)
    if not files:
        print("No audio files found.")
        return

    moves, warnings = collect_moves(root, files, args.albumartist)
    done, skipped, errors = execute_moves(moves, root, apply)

    removed = prune_empty_dirs(root) if apply else 0

    print("-" * 70)
    for w in warnings:
        print(f"  ?? {w}")
    summary = (f"{'moved' if apply else 'planned'}: {done}   skipped: {skipped}   "
               f"warnings: {len(warnings)}")
    if errors:
        summary += f"   errors: {errors}"
    if apply and removed:
        summary += f"   empty folders removed: {removed}"
    if not apply:
        summary += "   (DRY RUN — re-run with --apply to execute)"
    print(summary)
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
