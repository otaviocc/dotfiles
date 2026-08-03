#!/usr/bin/env python3
"""
music-library-to-bear.py

Scans a music library recursively and creates/updates one Bear note per artist,
listing all albums sorted by year (oldest first), with the album cover and
track list under each album heading.

USAGE
    python3 music-library-to-bear.py --root /path/to/music              # dry run
    python3 music-library-to-bear.py --root /path/to/music --apply      # write to Bear

OPTIONS
    --root PATH     Music library root to scan (required).
    --tag TAG       Bear tag applied to every note (default: music/collection).
    --apply         Write notes to Bear (default is dry run).

REQUIREMENTS
    ffprobe (part of ffmpeg) must be on PATH.
    Install with: brew install ffmpeg
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from urllib.parse import unquote

BEARCLI  = "/Applications/Bear.app/Contents/MacOS/bearcli"
FFPROBE  = "ffprobe"

AUDIO_EXTENSIONS = {".mp3", ".flac", ".m4a", ".ogg", ".aac", ".opus", ".wav", ".wma"}
COVER_PREFERRED  = {"folder.jpg", "folder.jpeg"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg"}

# ---------------------------------------------------------------------------
# Tag helpers (ffprobe-based, no pip dependencies)
# ---------------------------------------------------------------------------

def _check_ffprobe():
    """Exit early with a clear message if ffprobe is not available."""
    try:
        subprocess.run(
            [FFPROBE, "-version"],
            capture_output=True,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("Error: ffprobe not found. Install with: brew install ffmpeg", file=sys.stderr)
        sys.exit(1)


def _parse_int_prefix(value, default):
    """Parse the leading integer of a 'N' or 'N/M' tag value."""
    if not value:
        return default
    try:
        return int(str(value).split("/")[0].strip())
    except (ValueError, AttributeError):
        return default


def _parse_year(tags):
    """Return a 4-digit year string from ffprobe tags, or None."""
    for key in ("date", "year", "originaldate", "originalyear",
                "TDRC", "TYER", "TDOR"):
        raw = tags.get(key, "")
        if raw:
            m = re.match(r"(\d{4})", raw)
            if m:
                return m.group(1)
    return None


def read_tags(filepath):
    """
    Read audio tags from a file using ffprobe.
    Returns a dict with keys: artist, album, year, track_num, disc_num, title.
    Returns None if the file can't be read or is missing required tags.
    """
    try:
        result = subprocess.run(
            [
                FFPROBE,
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                filepath,
            ],
            capture_output=True,
            check=True,
        )
        data = json.loads(result.stdout)
    except Exception:
        return None

    tags = data.get("format", {}).get("tags", {})
    if not tags:
        return None

    # ffprobe tag keys are case-sensitive and vary by format/tagger.
    # Build a case-insensitive lookup covering common variants.
    ci = {k.lower(): v for k, v in tags.items()}

    album_artist = ci.get("album_artist") or ci.get("albumartist") or ""
    artist       = ci.get("artist") or ""
    effective_artist = (album_artist or artist).strip()

    album = (ci.get("album") or "").strip()

    if not effective_artist or not album:
        return None

    title     = (ci.get("title") or "").strip() or os.path.splitext(os.path.basename(filepath))[0]
    year      = _parse_year(ci)
    track_num = _parse_int_prefix(ci.get("track") or ci.get("tracknumber"), 0)
    disc_num  = _parse_int_prefix(ci.get("disc") or ci.get("discnumber"), 1)

    return {
        "artist":    effective_artist,
        "album":     album,
        "year":      year,      # str "YYYY" or None
        "track_num": track_num,
        "disc_num":  disc_num,
        "title":     title,
    }


# ---------------------------------------------------------------------------
# Cover detection
# ---------------------------------------------------------------------------

def find_cover(directory):
    """
    Return the path of the best cover image in `directory`, or None.
    Preference order:
      1. folder.jpg / folder.jpeg (case-insensitive)
      2. Largest JPEG in the directory
    """
    candidates = []
    try:
        entries = os.listdir(directory)
    except OSError:
        return None

    for name in entries:
        if name.startswith("._"):
            continue
        if os.path.splitext(name)[1].lower() in IMAGE_EXTENSIONS:
            full = os.path.join(directory, name)
            if name.lower() in COVER_PREFERRED:
                return full          # immediate winner
            candidates.append(full)

    if not candidates:
        return None

    # Fall back to the largest JPEG
    candidates.sort(key=lambda p: os.path.getsize(p), reverse=True)
    return candidates[0]


# ---------------------------------------------------------------------------
# Library scan
# ---------------------------------------------------------------------------

def scan_library(root):
    """
    Walk `root` recursively and build:

        library = {
            artist_name: {
                (year_sort_key, year_str, album_name): {
                    "cover":   "/path/to/folder.jpg" or None,
                    "tracks":  [(disc, track_num, title), ...],
                    "dir":     "/path/to/album/dir",
                }
            }
        }

    year_sort_key is (0, year_str) for known years, (1, "") to sort last.
    """
    library  = {}   # artist -> {album_key -> album_data}
    warnings = []

    for dirpath, dirs, filenames in os.walk(root):
        # Skip hidden directories in-place
        dirs[:] = sorted(d for d in dirs if not d.startswith("."))

        audio_files = [
            os.path.join(dirpath, f)
            for f in filenames
            if not f.startswith("._")
            and os.path.splitext(f)[1].lower() in AUDIO_EXTENSIONS
        ]

        if not audio_files:
            continue

        cover = find_cover(dirpath)

        for filepath in audio_files:
            info = read_tags(filepath)
            if info is None:
                rel = os.path.relpath(filepath, root)
                warnings.append(f"skipped (missing/unreadable tags): {rel}")
                continue

            artist    = info["artist"]
            album     = info["album"]
            year      = info["year"]          # str or None
            sort_key  = (0, year) if year else (1, "")
            album_key = (sort_key, year or "Unknown Year", album)

            if artist not in library:
                library[artist] = {}

            if album_key not in library[artist]:
                library[artist][album_key] = {
                    "cover":  cover,
                    "tracks": [],
                    "dir":    dirpath,
                }

            library[artist][album_key]["tracks"].append(
                (info["disc_num"], info["track_num"], info["title"])
            )

    # Sort tracks within each album
    for artist_data in library.values():
        for album_data in artist_data.values():
            album_data["tracks"].sort(key=lambda t: (t[0], t[1]))

    return library, warnings


# ---------------------------------------------------------------------------
# Dry-run report
# ---------------------------------------------------------------------------

def print_dry_run(library, warnings, root, tag):
    width = 70
    print(f"[DRY RUN]  root={root}  tag={tag}")
    print("─" * width)

    for artist in sorted(library.keys()):
        print(f"\nArtist: {artist}")
        albums = sorted(library[artist].keys())   # already (sort_key, year, name)
        for album_key in albums:
            _, year_str, album_name = album_key
            data        = library[artist][album_key]
            track_count = len(data["tracks"])
            cover_flag  = "✓" if data["cover"] else "✗"
            label       = f"{year_str} · {album_name}"
            print(f"  {label:<50}  {track_count:>3} tracks   cover: {cover_flag}")

    print("\n" + "─" * width)
    if warnings:
        print(f"\nWarnings ({len(warnings)}):")
        for w in warnings:
            print(f"  ?? {w}")
        print()

    total_notes = len(library)
    print(f"{total_notes} note(s) would be created/updated in Bear.")
    print("Re-run with --apply to execute.")


# ---------------------------------------------------------------------------
# Bear interaction
# ---------------------------------------------------------------------------

def bearcli(*args, stdin_bytes=None):
    """
    Run bearcli with the given args.
    Returns (stdout_str, returncode).
    Raises RuntimeError on non-zero exit with a useful message.
    """
    cmd = [BEARCLI] + list(args)
    result = subprocess.run(
        cmd,
        input=stdin_bytes,
        capture_output=True,
    )
    stdout = result.stdout.decode("utf-8", errors="replace")
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"bearcli {' '.join(args[:2])} failed: {stderr or stdout.strip()}")
    return stdout


def build_track_line(disc, track_num, title, max_track, is_multidisc):
    """Format a single track line."""
    width  = 3 if max_track > 99 else 2
    prefix = f"{track_num:0{width}d}"
    if is_multidisc and disc > 1:
        prefix = f"{disc}-{prefix}"
    return f"{prefix}. {title}"


def build_note_content_no_images(artist, albums_sorted, library, tag):
    """
    Build markdown note content without any image links.
    `albums_sorted` is a list of album_keys in display order.
    Returns the full markdown string.
    """
    lines = [f"# {artist}", ""]

    for album_key in albums_sorted:
        _, year_str, album_name = album_key
        data   = library[artist][album_key]
        tracks = data["tracks"]

        heading = f"## {album_name} ({year_str})"
        lines.append(heading)
        lines.append("")

        # Tracks
        discs     = {t[0] for t in tracks}
        is_multi  = len(discs) > 1
        max_track = max(t[1] for t in tracks) if tracks else 1

        for disc, track_num, title in tracks:
            lines.append(build_track_line(disc, track_num, title, max_track, is_multi))

        lines.append("")

    # Embed tag inline so overwrite preserves it
    lines.append(f"#{tag}")
    lines.append("")

    return "\n".join(lines)


def build_note_content_with_images(artist, albums_sorted, library, cover_links, tag):
    """
    Build the final markdown with cover image links inserted after each album heading.
    `cover_links` maps album_key -> markdown image syntax string (or None).
    """
    lines = [f"# {artist}", ""]

    for album_key in albums_sorted:
        _, year_str, album_name = album_key
        data   = library[artist][album_key]
        tracks = data["tracks"]

        heading = f"## {album_name} ({year_str})"
        lines.append(heading)
        lines.append("")

        # Cover image
        link = cover_links.get(album_key)
        if link:
            lines.append(link)
            lines.append("")

        # Tracks
        discs     = {t[0] for t in tracks}
        is_multi  = len(discs) > 1
        max_track = max(t[1] for t in tracks) if tracks else 1

        for disc, track_num, title in tracks:
            lines.append(build_track_line(disc, track_num, title, max_track, is_multi))

        lines.append("")

    # Embed tag inline so overwrite preserves it
    lines.append(f"#{tag}")
    lines.append("")

    return "\n".join(lines)


def attachment_filename(year_str, album_name):
    """
    Build a safe filename for an album cover attachment.
    Bear uses the filename to avoid collisions (e.g. renames to 'name 2.jpg').
    """
    safe = re.sub(r'[\\/:*?"<>|]', "-", album_name).strip()
    return f"{year_str} - {safe}.jpg"



def apply_library(library, warnings, root, tag):
    """Create or overwrite one Bear note per artist."""
    if not os.path.isfile(BEARCLI):
        print(f"Error: bearcli not found at {BEARCLI}", file=sys.stderr)
        sys.exit(1)

    created = updated = skipped = errors = 0

    for artist in sorted(library.keys()):
        albums_sorted = sorted(library[artist].keys())

        print(f"\nProcessing: {artist} ({len(albums_sorted)} album(s))")

        try:
            # ----------------------------------------------------------------
            # Step 1: create the note (or retrieve existing) with tracks only
            # ----------------------------------------------------------------
            initial_content = build_note_content_no_images(artist, albums_sorted, library, tag)

            raw = bearcli(
                "create", artist,
                "--content", initial_content,
                "--tags", tag,
                "--if-not-exists",
                "--format", "json",
            )

            note_json    = json.loads(raw)
            note_id      = note_json["id"]
            note_existed = bool(note_json.get("title"))  # always has title; use modified heuristic

            was_new = not note_existed
            if was_new:
                created += 1
                print(f"  created note {note_id[:8]}")
            else:
                updated += 1
                print(f"  updated note {note_id[:8]}")

            # ----------------------------------------------------------------
            # Step 2: attach covers one by one, collect Bear's link text
            # ----------------------------------------------------------------
            cover_links = {}   # album_key -> markdown link string

            for album_key in albums_sorted:
                _, year_str, album_name = album_key
                cover_path = library[artist][album_key]["cover"]

                if not cover_path:
                    print(f"    {year_str} · {album_name}: no cover")
                    cover_links[album_key] = None
                    continue

                filename = attachment_filename(year_str, album_name)

                try:
                    with open(cover_path, "rb") as f:
                        cover_bytes = f.read()

                    bearcli(
                        "attachments", "add", note_id,
                        "--filename", filename,
                        stdin_bytes=cover_bytes,
                    )
                    time.sleep(0.3)   # give Bear time to process the attachment
                    print(f"    {year_str} · {album_name}: cover attached")

                    # Bear appended a link — we'll collect them all at the end
                    cover_links[album_key] = filename   # placeholder; resolved below

                except Exception as exc:
                    print(f"    {year_str} · {album_name}: cover failed — {exc}")
                    cover_links[album_key] = None

            # ----------------------------------------------------------------
            # Step 3: re-read the note to get Bear's actual attachment links
            # ----------------------------------------------------------------
            note_raw     = bearcli("cat", note_id, "--format", "json")
            note_parsed  = json.loads(note_raw)
            note_content = note_parsed.get("content", "")

            # Bear appended image links as ![](filename.jpg) at the bottom.
            # Filenames are URL-encoded (spaces become %20, etc.).
            # Build a map: decoded filename (lowercased) -> full markdown image syntax.
            bear_link_map = {}
            for m in re.finditer(r'(!\[\]\(([^)]+)\))', note_content):
                full_link, encoded_fname = m.group(1), m.group(2)
                decoded = unquote(encoded_fname).lower()
                bear_link_map[decoded] = full_link

            # Resolve placeholders to actual bear image links.
            # Bear may rename on collision (e.g. "foo.jpg" -> "foo 2.jpg"),
            # so we match on stem prefix.
            for album_key, val in cover_links.items():
                if val is None:
                    continue
                _, year_str, album_name = album_key
                requested = attachment_filename(year_str, album_name)
                requested_stem = os.path.splitext(requested)[0].lower()

                matched_link = None
                for decoded_fname, full_link in bear_link_map.items():
                    stem = os.path.splitext(decoded_fname)[0]
                    if stem == requested_stem or stem.startswith(requested_stem):
                        matched_link = full_link
                        break

                cover_links[album_key] = matched_link   # may still be None if not found

            # ----------------------------------------------------------------
            # Step 4: overwrite with covers in the correct positions
            # ----------------------------------------------------------------
            final_content = build_note_content_with_images(
                artist, albums_sorted, library, cover_links, tag
            )

            bearcli(
                "overwrite", note_id,
                "--content", final_content,
                "--force",
            )
            print(f"  note finalised with inline covers")

        except Exception as exc:
            print(f"  ERROR: {exc}", file=sys.stderr)
            errors += 1

    # Summary
    width = 70
    print("\n" + "─" * width)
    if warnings:
        print(f"\nWarnings ({len(warnings)}):")
        for w in warnings:
            print(f"  ?? {w}")

    print(
        f"\ncreated: {created}   updated: {updated}   "
        f"skipped: {skipped}   errors: {errors}"
    )
    if errors:
        sys.exit(1)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="Create Bear notes from a music library, one note per artist."
    )
    ap.add_argument("--root", required=True, help="Music library root directory")
    ap.add_argument("--tag",  default="music/collection",
                    help="Bear tag for all notes (default: music/collection)")
    ap.add_argument("--apply", action="store_true",
                    help="Write to Bear (default is dry run)")
    args = ap.parse_args()

    _check_ffprobe()

    root = os.path.abspath(args.root)

    if not os.path.isdir(root):
        print(f"Error: '{root}' is not a directory", file=sys.stderr)
        sys.exit(1)

    print(f"Scanning {root} …")
    library, warnings = scan_library(root)

    if not library:
        print("No artists found. Check that the folder contains audio files with tags.")
        return

    if args.apply:
        apply_library(library, warnings, root, args.tag)
    else:
        print_dry_run(library, warnings, root, args.tag)


if __name__ == "__main__":
    main()
