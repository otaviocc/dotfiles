#!/usr/bin/env python3
"""
music-library-to-obsidian.py

Scans a music library recursively and creates one Obsidian note per album,
organised under an artist folder inside a target vault folder.

Output structure inside the vault:

    Music/
      Miles Davis/
        Kind of Blue (1959).md
        Bitches Brew (1970).md
        Artworks/
          Kind of Blue (1959).jpg
          Bitches Brew (1970).jpg
      ...

Each album note has full YAML frontmatter (album, album_artist, tracks,
discs, year, tags) and a body with the embedded cover and numbered track list.

Two Obsidian Bases are also written:

    Music/Albums.base  — table + cards views of all album notes
    Music/Artists.base — one row per unique artist with album count

USAGE
    python3 music-library-to-obsidian.py \\
        --root  /path/to/music \\
        --vault /path/to/vault \\
        --folder Music                     # subfolder inside the vault (default)

    # dry run (default) — shows what would be created
    python3 music-library-to-obsidian.py --root ... --vault ...

    # apply — write files and use the obsidian CLI to open/refresh
    python3 music-library-to-obsidian.py --root ... --vault ... --apply

OPTIONS
    --root PATH     Music library root to scan (required).
    --vault PATH    Obsidian vault root (required).
    --folder NAME   Subfolder inside the vault (default: Music).
    --tag TAG       Tag added to every album note (default: music/collection).
    --apply         Write files and call the Obsidian CLI (default: dry run).

REQUIREMENTS
    mutagen — pip install mutagen
    obsidian CLI must be on PATH (comes with Obsidian on macOS/Linux).
"""

import argparse
import os
import re
import shutil
import subprocess
import sys

try:
    import mutagen
except ImportError:
    print("Error: mutagen is required. Install with: pip install mutagen",
          file=sys.stderr)
    sys.exit(1)

OBSIDIAN_CLI = "obsidian"

AUDIO_EXTENSIONS = {".mp3", ".flac", ".m4a", ".ogg", ".aac", ".opus", ".wav", ".wma"}
COVER_PREFERRED  = {"folder.jpg", "folder.jpeg"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

UNSAFE_PATH_RE   = re.compile(r'[\\/:*?"<>|]')


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def safe_filename(name):
    """Strip characters that are unsafe in filenames."""
    cleaned = UNSAFE_PATH_RE.sub("-", name)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    return cleaned or "_"


def _first(tags, key, default=None):
    """Return the first value of a mutagen tag list, or default."""
    values = tags.get(key) or []
    return values[0] if values else default


def _parse_int_prefix(value, default):
    """Parse the leading integer of a 'N' or 'N/M' tag value."""
    if not value:
        return default
    try:
        return int(str(value).split("/")[0].strip())
    except (ValueError, AttributeError):
        return default


def _parse_int_denom(value, default):
    """Parse the denominator of a 'N/M' tag value (the total), or default."""
    if not value:
        return default
    parts = str(value).split("/")
    if len(parts) < 2:
        return default
    try:
        return int(parts[1].strip())
    except (ValueError, AttributeError):
        return default


def _parse_year(tags):
    """Return a 4-digit year string from a mutagen easy-tag dict, or None."""
    for key in ("date", "year", "originaldate", "originalyear"):
        raw = _first(tags, key) or ""
        if raw:
            m = re.match(r"(\d{4})", raw)
            if m:
                return m.group(1)
    return None


# ---------------------------------------------------------------------------
# Tag reading (mutagen)
# ---------------------------------------------------------------------------

def read_tags(filepath):
    """
    Read audio tags from a file using mutagen (easy=True interface).
    Returns a dict with: artist, album_artist, album, year,
                         track_num, disc_num, total_tracks, total_discs, title.
    Returns None if the file can't be read or is missing required tags.
    """
    try:
        audio = mutagen.File(filepath, easy=True)
    except Exception:
        return None
    if audio is None or audio.tags is None:
        return None

    tags = audio.tags

    album_artist     = (_first(tags, "albumartist") or "").strip()
    artist           = (_first(tags, "artist") or "").strip()
    effective_artist = album_artist or artist

    album = (_first(tags, "album") or "").strip()
    if not effective_artist or not album:
        return None

    title     = (_first(tags, "title") or "").strip() or os.path.splitext(
        os.path.basename(filepath))[0]
    year      = _parse_year(tags)
    tracktag  = _first(tags, "tracknumber")
    disctag   = _first(tags, "discnumber")
    track_num = _parse_int_prefix(tracktag, 0)
    disc_num  = _parse_int_prefix(disctag, 1)
    total_tracks = _parse_int_denom(tracktag, None)
    total_discs  = _parse_int_denom(disctag, None)

    return {
        "artist":       effective_artist,
        "album_artist": album_artist or artist,
        "album":        album,
        "year":         year,           # "YYYY" str or None
        "title":        title,
        "track_num":    track_num,
        "disc_num":     disc_num,
        "total_tracks": total_tracks,   # int or None
        "total_discs":  total_discs,    # int or None
    }


# ---------------------------------------------------------------------------
# Cover detection
# ---------------------------------------------------------------------------

def find_cover(directory):
    """
    Return the path of the best cover image in `directory`, or None.
    Preference: folder.jpg / folder.jpeg first, then largest image file.
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
                return full
            candidates.append(full)

    if not candidates:
        return None

    candidates.sort(key=lambda p: os.path.getsize(p), reverse=True)
    return candidates[0]


# ---------------------------------------------------------------------------
# Library scan
# ---------------------------------------------------------------------------

def scan_library(root):
    """
    Walk `root` recursively and return:

        library = {
            artist_name: {
                album_sort_key: {
                    "album":        str,
                    "album_artist": str,
                    "year":         "YYYY" or None,
                    "cover":        "/path/to/image" or None,
                    "tracks":       [(disc, track_num, title), ...],
                    "total_tracks": int or None,
                    "total_discs":  int or None,
                    "dir":          "/path/to/album/dir",
                }
            }
        }

        album_sort_key = (year_sort_tuple, year_str, album_name)
        year_sort_tuple = (0, year_str) for known, (1, "") for unknown (sorts last)
    """
    library  = {}
    warnings = []

    for dirpath, dirs, filenames in os.walk(root):
        dirs[:] = sorted(d for d in dirs if not d.startswith("."))

        audio_files = [
            os.path.join(dirpath, f)
            for f in sorted(filenames)
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
            year      = info["year"]
            sort_tup  = (0, year) if year else (1, "")
            album_key = (sort_tup, year or "Unknown Year", album)

            if artist not in library:
                library[artist] = {}

            if album_key not in library[artist]:
                library[artist][album_key] = {
                    "album":        album,
                    "album_artist": info["album_artist"],
                    "year":         year,
                    "cover":        cover,
                    "tracks":       [],
                    "total_tracks": info["total_tracks"],
                    "total_discs":  info["total_discs"],
                    "dir":          dirpath,
                }
            elif info["total_tracks"] and not library[artist][album_key]["total_tracks"]:
                library[artist][album_key]["total_tracks"] = info["total_tracks"]
            elif info["total_discs"] and not library[artist][album_key]["total_discs"]:
                library[artist][album_key]["total_discs"] = info["total_discs"]

            library[artist][album_key]["tracks"].append(
                (info["disc_num"], info["track_num"], info["title"])
            )

    # Sort tracks within each album by (disc, track)
    for artist_data in library.values():
        for album_data in artist_data.values():
            album_data["tracks"].sort(key=lambda t: (t[0], t[1]))

    return library, warnings


# ---------------------------------------------------------------------------
# Note generation
# ---------------------------------------------------------------------------

def album_note_filename(year, album_name):
    """e.g. 'Kind of Blue (1959).md'"""
    safe = safe_filename(album_name)
    if year:
        return f"{safe} ({year}).md"
    return f"{safe}.md"


def artwork_filename(year, album_name, ext=".jpg"):
    """e.g. 'Kind of Blue (1959).jpg'"""
    safe = safe_filename(album_name)
    if year:
        return f"{safe} ({year}){ext}"
    return f"{safe}{ext}"


def count_discs(tracks):
    """Return the number of distinct disc numbers in a track list."""
    return len({t[0] for t in tracks})


def build_track_line(track_num, title, max_track):
    width = 3 if max_track > 99 else 2
    return f"{track_num:0{width}d}. {title}"


def build_album_note(album_data, tag, artwork_vault_path):
    """
    Build the full markdown text for one album note.

    `artwork_vault_path` is the vault-relative path to the artwork file
    (e.g. 'Music/Miles Davis/Artworks/Kind of Blue (1959).jpg'), or None.
    """
    album        = album_data["album"]
    album_artist = album_data["album_artist"]
    year         = album_data["year"] or ""
    tracks       = album_data["tracks"]
    n_tracks     = album_data["total_tracks"] or len(tracks)
    n_discs_tag  = album_data["total_discs"] or count_discs(tracks)

    # ----- frontmatter -----
    fm_lines = ["---"]
    fm_lines.append(f"album: \"{album.replace(chr(34), chr(39))}\"")
    fm_lines.append(f"album_artist: \"{album_artist.replace(chr(34), chr(39))}\"")
    if year:
        fm_lines.append(f"year: {year}")
    else:
        fm_lines.append("year:")
    fm_lines.append(f"tracks: {n_tracks}")
    fm_lines.append(f"discs: {n_discs_tag}")
    if artwork_vault_path:
        fm_lines.append(f"cover: \"[[{artwork_vault_path}]]\"")
    else:
        fm_lines.append("cover:")
    fm_lines.append("tags:")
    fm_lines.append(f"  - {tag}")
    fm_lines.append("  - music/album")
    fm_lines.append("---")

    # ----- body -----
    body_lines = []

    # Embedded cover (no leading blank line — a blank line after --- renders visibly)
    if artwork_vault_path:
        body_lines.append(f"![[{artwork_vault_path}]]")
        body_lines.append("")

    # Track list
    body_lines.append("## Tracks")
    body_lines.append("")

    is_multi  = count_discs(tracks) > 1
    max_track = max((t[1] for t in tracks), default=1)

    current_disc = None
    for disc, track_num, title in tracks:
        if is_multi and disc != current_disc:
            current_disc = disc
            if body_lines[-1] != "":
                body_lines.append("")
            body_lines.append(f"**Disc {disc}**")
            body_lines.append("")
        body_lines.append(build_track_line(track_num, title, max_track))

    body_lines.append("")

    return "\n".join(fm_lines + body_lines)


# ---------------------------------------------------------------------------
# Base file generation
# ---------------------------------------------------------------------------

ALBUMS_BASE = """\
# Albums base — auto-generated by music-library-to-obsidian
filters:
  and:
    - file.hasTag("music/album")

properties:
  album:
    displayName: Album
  album_artist:
    displayName: Artist
  year:
    displayName: Year
  tracks:
    displayName: Tracks
  discs:
    displayName: Discs
  cover:
    displayName: Cover

views:
  - type: cards
    name: Covers
    image: cover
    imageFit: cover
    order:
      - year
      - album
    groupBy:
      property: album_artist
      direction: ASC

  - type: table
    name: All Albums
    order:
      - album_artist
      - year
      - album
      - tracks
      - discs

  - type: table
    name: By Artist
    order:
      - album_artist
      - year
      - album
      - tracks
    groupBy:
      property: album_artist
      direction: ASC
"""

ARTISTS_BASE = """\
# Artists base — auto-generated by music-library-to-obsidian
#
# This base surfaces one row per distinct album_artist value.
# Because Bases operate on notes, we use a formula to count albums per artist.
filters:
  and:
    - file.hasTag("music/album")

formulas:
  year_range: 'if(year, year.toString(), "—")'

properties:
  album_artist:
    displayName: Artist
  formula.year_range:
    displayName: Year

views:
  - type: table
    name: Albums by Artist
    order:
      - album_artist
      - album
      - formula.year_range
      - tracks
    groupBy:
      property: album_artist
      direction: ASC

  - type: list
    name: Artist List
    order:
      - album_artist
      - album
    groupBy:
      property: album_artist
      direction: ASC
"""


# ---------------------------------------------------------------------------
# Dry-run report
# ---------------------------------------------------------------------------

def print_dry_run(library, warnings, root, vault_root, vault_folder, tag):
    width = 72
    print(f"[DRY RUN]  root={root}  vault-folder={vault_folder}  tag={tag}")
    print("─" * width)

    base_dir      = os.path.join(vault_root, vault_folder)
    total_albums  = 0
    art_new       = 0
    art_existing  = 0

    for artist in sorted(library.keys()):
        print(f"\n{artist}/")
        artist_dir   = os.path.join(base_dir, safe_filename(artist))
        artworks_dir = os.path.join(artist_dir, "Artworks")
        albums_sorted = sorted(library[artist].keys())
        for album_key in albums_sorted:
            total_albums += 1
            _, year_str, album_name = album_key
            data       = library[artist][album_key]
            n_tracks   = len(data["tracks"])
            n_discs    = count_discs(data["tracks"])
            note_fn    = album_note_filename(data["year"], album_name)
            note_path  = os.path.join(artist_dir, note_fn)
            note_state = "update" if os.path.isfile(note_path) else "create"

            if data["cover"]:
                src_ext  = os.path.splitext(data["cover"])[1].lower() or ".jpg"
                art_fn   = artwork_filename(data["year"], album_name, src_ext)
                art_dest = os.path.join(artworks_dir, art_fn)
                if os.path.isfile(art_dest):
                    cover_flag = "art: exists"
                    art_existing += 1
                else:
                    cover_flag = "art: copy"
                    art_new += 1
            else:
                cover_flag = "no cover"

            label = f"  [{note_state}] {note_fn:<50}"
            print(f"{label} {n_tracks:>3} tracks  {n_discs} disc(s)  {cover_flag}")

    print("\n" + "─" * width)
    if warnings:
        print(f"\nWarnings ({len(warnings)}):")
        for w in warnings:
            print(f"  ?? {w}")
        print()

    print(f"{len(library)} artist folder(s), {total_albums} album note(s) would be "
          f"created/updated.")
    print(f"Artworks: {art_new} to copy, {art_existing} already present (skipped).")
    print(f"Albums.base and Artists.base would be written to {vault_folder}/.")
    print("Re-run with --apply to execute.")


# ---------------------------------------------------------------------------
# Apply
# ---------------------------------------------------------------------------

def _obsidian_open(vault, path):
    """Ask Obsidian to open a file so the vault index picks it up."""
    try:
        subprocess.run(
            [OBSIDIAN_CLI, f'vault="{vault}"', f'open file="{path}"', "silent"],
            capture_output=True,
            timeout=5,
        )
    except Exception:
        pass  # non-fatal; the file exists regardless


def apply_library(library, warnings, root, vault_root, vault_folder, tag):
    """
    Write album notes, copy artwork, and create base files.
    """
    base_dir = os.path.join(vault_root, vault_folder)
    os.makedirs(base_dir, exist_ok=True)

    created        = 0
    updated        = 0
    skipped        = 0
    errors         = 0
    artworks_new   = 0
    artworks_skip  = 0

    for artist in sorted(library.keys()):
        artist_dir   = os.path.join(base_dir, safe_filename(artist))
        artworks_dir = os.path.join(artist_dir, "Artworks")
        os.makedirs(artworks_dir, exist_ok=True)

        albums_sorted = sorted(library[artist].keys())
        print(f"\n{artist}/ ({len(albums_sorted)} album(s))")

        for album_key in albums_sorted:
            _, year_str, album_name = album_key
            data = library[artist][album_key]

            note_fn      = album_note_filename(data["year"], album_name)
            note_path    = os.path.join(artist_dir, note_fn)
            note_existed = os.path.isfile(note_path)

            # ---- copy artwork ----
            artwork_vault_path = None
            if data["cover"]:
                src_ext  = os.path.splitext(data["cover"])[1].lower() or ".jpg"
                art_fn   = artwork_filename(data["year"], album_name, src_ext)
                art_dest = os.path.join(artworks_dir, art_fn)
                try:
                    # vault-relative path uses forward slashes
                    artwork_vault_path = "/".join([
                        vault_folder,
                        safe_filename(artist),
                        "Artworks",
                        art_fn,
                    ])
                    if os.path.isfile(art_dest):
                        artworks_skip += 1   # already present — leave it alone
                    else:
                        shutil.copy2(data["cover"], art_dest)
                        artworks_new += 1
                except Exception as exc:
                    print(f"    artwork copy failed for {album_name}: {exc}",
                          file=sys.stderr)

            # ---- write note ----
            try:
                content = build_album_note(data, tag, artwork_vault_path)
                with open(note_path, "w", encoding="utf-8") as fh:
                    fh.write(content)

                status = "updated" if note_existed else "created"
                if note_existed:
                    updated += 1
                else:
                    created += 1
                art_flag = f"  [art: {os.path.basename(artwork_vault_path)}]" \
                           if artwork_vault_path else "  [no cover]"
                print(f"  {status}: {note_fn}{art_flag}")
            except Exception as exc:
                print(f"  ERROR writing {note_fn}: {exc}", file=sys.stderr)
                errors += 1

    # ---- write base files ----
    for base_name, base_content in [
        ("Albums.base", ALBUMS_BASE),
        ("Artists.base", ARTISTS_BASE),
    ]:
        base_path = os.path.join(base_dir, base_name)
        try:
            with open(base_path, "w", encoding="utf-8") as fh:
                fh.write(base_content)
            print(f"\nWrote {vault_folder}/{base_name}")
        except Exception as exc:
            print(f"\nERROR writing {base_name}: {exc}", file=sys.stderr)
            errors += 1

    # ---- summary ----
    width = 72
    print("\n" + "─" * width)
    if warnings:
        print(f"\nWarnings ({len(warnings)}):")
        for w in warnings:
            print(f"  ?? {w}")

    print(
        f"\ncreated: {created}   updated: {updated}   "
        f"artworks copied: {artworks_new}   artworks skipped: {artworks_skip}   "
        f"errors: {errors}"
    )
    if errors:
        sys.exit(1)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="Create Obsidian album notes from a music library."
    )
    ap.add_argument("--root",   required=True,
                    help="Music library root directory")
    ap.add_argument("--vault",  required=True,
                    help="Obsidian vault root directory")
    ap.add_argument("--folder", default="Music",
                    help="Subfolder inside the vault (default: Music)")
    ap.add_argument("--tag",    default="music/collection",
                    help="Tag applied to every album note (default: music/collection)")
    ap.add_argument("--apply",  action="store_true",
                    help="Write files (default is dry run)")
    args = ap.parse_args()

    root       = os.path.abspath(args.root)
    vault_root = os.path.abspath(args.vault)

    if not os.path.isdir(root):
        print(f"Error: music root '{root}' is not a directory", file=sys.stderr)
        sys.exit(1)
    if not os.path.isdir(vault_root):
        print(f"Error: vault '{vault_root}' is not a directory", file=sys.stderr)
        sys.exit(1)

    print(f"Scanning {root} …")
    library, warnings = scan_library(root)

    if not library:
        print("No artists found. Check that the folder contains audio files with tags.")
        return

    if args.apply:
        apply_library(library, warnings, root, vault_root, args.folder, args.tag)
    else:
        print_dry_run(library, warnings, root, vault_root, args.folder, args.tag)


if __name__ == "__main__":
    main()
