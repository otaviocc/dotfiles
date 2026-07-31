#!/usr/bin/env python3
"""
organize-movies.py

Generic organizer for NEW movie files dropped into a Jellyfin movie library. Parses
scene-style names algorithmically (no hardcoded titles) into the Jellyfin convention:
    /Movies/Movie Name (year)/Movie Name (year).ext
Reference: https://jellyfin.org/docs/general/server/media/movie-naming/

USAGE
    1. Copy this script to the root of your Movies library.
    2. Dry run (default, changes nothing):   python3 organize-movies.py
    3. Inspect the planned moves.
    4. Apply for real:                       python3 organize-movies.py --apply

OPTIONS
    --apply             Execute the moves (default is dry run).
    --root PATH         Library root (default: current directory).
    --no-editions       Do not emit {edition-...} tags (otherwise detected from the
                        filename: Director's Cut, Final Cut, Extended, Unrated,
                        Theatrical, IMAX).
    --sub-lang CODE     Language code inserted into subtitle filenames (extension is
                        kept as-is), e.g. "en" -> "Movie (year).en.srt" / ".en.ass".
                        Default is empty -> "Movie (year).srt" (matches a plain library).

WHAT IT DOES
    - Handles both layouts a download produces: a release FOLDER containing the video,
      and a LOOSE video file sitting in the library root. Subtitles travelling with the
      video are renamed to match (and grouped into the same folder).
    - Extracts the release year as the LAST year-like token before the quality tail, so
      titles that contain a number are safe (e.g. "Blade Runner 2049 2017" -> year 2017).
    - Strips release junk (resolution, source, codec, audio, group tags, REMASTERED, etc.).
    - Lifts edition tags out of the name and into {edition-...}.
    - Light title-casing for all-lowercase scene names ("john.wick" -> "John Wick").
    - Already-correct "Title (year)" files/folders are detected and left untouched.
    - Never overwrites: existing targets and no-op renames are skipped. Files it cannot
      parse (no detectable year) are reported and left alone.
"""

import argparse
import os
import re

VIDEO_EXTS = {".mkv", ".mp4", ".m4v", ".avi", ".mov", ".wmv", ".ts"}
SUB_EXTS = {".srt", ".ass", ".ssa", ".sub", ".vtt"}

ALREADY_RE = re.compile(
    r"^(?P<title>.+?) \((?P<year>\d{4})\)(?: \{edition-(?P<ed>[^}]+)\})?$"
)

# First token of the "release tail"; everything from here on is not part of the title.
QUALITY_RE = re.compile(
    r"\b(?:\d{3,4}p|4k|2160p|1080i|bluray|blu-ray|brrip|bdrip|bdremux|remux|"
    r"web[- ]?dl|webrip|hdtv|hdrip|dvdrip|dvdscr|hdts|telesync|hdcam|"
    r"x264|x265|h\s?264|h\s?265|hevc|avc|xvid|divx|"
    r"aac|ac3|dd5|ddp5|ddp|dts|truehd|atmos|flac|mp3|opus|"
    r"10bit|8bit|hdr10|hdr|sdr|yify|yts|vostfr)\b",
    re.IGNORECASE,
)

# Edition keywords. label=None means "noise": strip from title but don't tag.
EDITION_PATTERNS = [
    (re.compile(r"director'?s[ .]?cut", re.I), "Director's Cut"),
    (re.compile(r"\bfinal[ .]?cut\b", re.I), "Final Cut"),
    (re.compile(r"\bextended(?:[ .]?(?:cut|edition))?\b", re.I), "Extended"),
    (re.compile(r"\bunrated\b", re.I), "Unrated"),
    (re.compile(r"\btheatrical(?:[ .]?cut)?\b", re.I), "Theatrical"),
    (re.compile(r"\bimax\b", re.I), "IMAX"),
    (re.compile(r"\bremastered\b", re.I), None),
    (re.compile(r"\brestored\b", re.I), None),
]

NOISE_RE = re.compile(
    r"\b(?:proper|repack|internal|retail|limited|multi|complete|hybrid|"
    r"open\s?matte|uncut|dubbed|subbed)\b",
    re.IGNORECASE,
)

PART_RE = re.compile(r"\b(?:cd|dvd|disc|disk|part|pt)\s*0*([1-8])\b", re.IGNORECASE)

SMALL_WORDS = {"a", "an", "the", "of", "and", "or", "in", "on", "to", "for",
               "vs", "at", "by", "with", "from", "as", "but", "nor"}


def smart_title(text):
    # A fully shouty release name ("THE.DARK.KNIGHT") has no way to distinguish
    # real acronyms from all-caps noise, so title-case every word in that case.
    # Otherwise, a word that already carries mixed case is left alone (acronyms,
    # already-proper-cased names, etc.).
    all_caps = text.isupper()
    words = text.split()
    out = []
    for i, w in enumerate(words):
        if not all_caps and any(c.isupper() for c in w):
            out.append(w)
        elif i != 0 and w.lower() in SMALL_WORDS:
            out.append(w.lower())
        else:
            rest = w[1:].lower() if all_caps else w[1:]
            out.append(w[:1].upper() + rest)
    return " ".join(out)


class Parsed:
    __slots__ = ("title", "year", "edition", "already")

    def __init__(self, title, year, edition, already=False):
        self.title = title
        self.year = year
        self.edition = edition
        self.already = already


def parse_identity(stem):
    """Parse a movie stem into (title, year, edition). Returns None if no year."""
    # drop a trailing organized split marker ("Title (2010) - pt1") before matching
    stem = re.sub(r"\s*-\s*(?:cd|dvd|disc|disk|part|pt)\s*0*[1-8]\s*$", "", stem,
                  flags=re.IGNORECASE)
    m = ALREADY_RE.match(stem)
    if m:
        return Parsed(m.group("title"), int(m.group("year")), m.group("ed"), already=True)

    norm = re.sub(r"[._]+", " ", stem)
    norm = re.sub(r"\s+", " ", norm).strip()

    q = QUALITY_RE.search(norm)
    head = norm[: q.start()] if q else norm

    editions = []
    for rgx, label in EDITION_PATTERNS:
        if rgx.search(norm):
            if label and label not in editions:
                editions.append(label)
            head = rgx.sub(" ", head)

    years = list(re.finditer(r"\b(?:19|20)\d{2}\b", head))
    if not years:
        return None
    ym = years[-1]
    year = int(ym.group(0))

    title = head[: ym.start()].strip()
    if not title:                              # leading-year style: "2024 War Machine"
        title = head[ym.end():].strip()

    title = NOISE_RE.sub(" ", title)
    title = re.sub(r"\s+", " ", title).strip(" -._(")
    if not title:
        return None
    return Parsed(smart_title(title), year, " ".join(editions) if editions else None)


def detect_part(stem, title=""):
    """Detect a multi-disc/multi-part split marker (e.g. "CD1", "Part 2").

    Skips titles where the parsed movie title already spells out that same
    part number (e.g. "Mockingjay Part 1"), so it isn't tagged a second time
    as "... - pt1".
    """
    m = PART_RE.search(re.sub(r"[._]+", " ", stem))
    if not m:
        return None
    part = int(m.group(1))
    if re.search(rf"\b(?:part|pt)\s*0*{part}\b", title, re.IGNORECASE):
        return None
    return part


def folder_name(p, editions_on):
    name = f"{p.title} ({p.year})"
    if p.edition and editions_on:
        name += f" {{edition-{p.edition}}}"
    return name


def file_base(p, editions_on, part):
    base = folder_name(p, editions_on)
    if part:
        base += f" - pt{part}"
    return base


def sub_stem(stem):
    """Strip a trailing language code from a subtitle stem for parsing."""
    return re.sub(r"[ ._-](?:eng|english|en|por|pt|spa|es|fre|fr|ger|de)$", "", stem,
                  flags=re.IGNORECASE)


def media_kind(fn):
    ext = os.path.splitext(fn)[1].lower()
    if ext in VIDEO_EXTS:
        return "video", ext
    if ext in SUB_EXTS:
        return "sub", ext
    return None, ext


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--no-editions", action="store_true")
    ap.add_argument("--sub-lang", default="")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    apply = args.apply
    editions_on = not args.no_editions
    sub_lang = args.sub_lang.strip(".")

    print(f"root={root}  mode={'APPLY' if apply else 'DRY RUN'}  "
          f"editions={'on' if editions_on else 'off'}  "
          f"sub-lang={sub_lang or '<none>'}")
    print("-" * 70)

    moves = []          # (src, dst)
    warnings = []

    def plan_file(src_path, ident, target_dir):
        fn = os.path.basename(src_path)
        kind, ext = media_kind(fn)
        if kind is None:
            return
        stem = os.path.splitext(fn)[0]
        part = detect_part(stem, ident.title)
        base = file_base(ident, editions_on, part)
        if kind == "sub":
            lang = sub_lang
            dst_name = f"{base}.{lang}{ext}" if lang else f"{base}{ext}"
        else:
            dst_name = f"{base}{ext}"
        moves.append((src_path, os.path.join(target_dir, dst_name)))

    entries = sorted(os.listdir(root))
    loose = []

    for entry in entries:
        full = os.path.join(root, entry)
        if os.path.isdir(full):
            # identify the movie from the primary video, else the folder name
            files = [f for f in os.listdir(full) if os.path.isfile(os.path.join(full, f))]
            videos = [f for f in files if media_kind(f)[0] == "video"]
            ident = None
            for v in sorted(videos, key=len, reverse=True):
                ident = parse_identity(os.path.splitext(v)[0])
                if ident:
                    break
            if ident is None:
                ident = parse_identity(entry)
            if ident is None:
                warnings.append(f"could not parse (folder left as-is): {entry}")
                continue
            new_dir = os.path.join(root, folder_name(ident, editions_on))
            for f in files:
                plan_file(os.path.join(full, f), ident, new_dir)
        elif os.path.isfile(full):
            kind, _ = media_kind(entry)
            if kind:
                loose.append(entry)

    # group loose root-level files by movie identity
    groups = {}
    for fn in loose:
        kind, _ = media_kind(fn)
        stem = os.path.splitext(fn)[0]
        ident = parse_identity(sub_stem(stem) if kind == "sub" else stem)
        if ident is None:
            warnings.append(f"could not parse (file left as-is): {fn}")
            continue
        key = folder_name(ident, editions_on)
        groups.setdefault(key, ident)
        new_dir = os.path.join(root, key)
        plan_file(os.path.join(root, fn), ident, new_dir)

    done = skipped = 0
    for src, dst in moves:
        if os.path.abspath(src) == os.path.abspath(dst):
            continue
        rel_src = os.path.relpath(src, root)
        rel_dst = os.path.relpath(dst, root)
        if os.path.exists(dst):
            print(f"  !! target exists, skipping: {rel_dst}")
            skipped += 1
            continue
        print(f"{rel_src}\n   -> {rel_dst}")
        if apply:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            os.rename(src, dst)
        done += 1

    # remove now-empty source folders
    if apply:
        for entry in entries:
            full = os.path.join(root, entry)
            if os.path.isdir(full):
                try:
                    if not os.listdir(full):
                        os.rmdir(full)
                except OSError:
                    pass

    print("-" * 70)
    for w in warnings:
        print(f"  ?? {w}")
    print(f"{'moved' if apply else 'planned'}: {done}   skipped: {skipped}   "
          f"warnings: {len(warnings)}   "
          f"({'APPLY' if apply else 'DRY RUN — re-run with --apply to execute'})")


if __name__ == "__main__":
    main()
