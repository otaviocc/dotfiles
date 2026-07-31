#!/usr/bin/env python3
"""
organize-kids-shows.py

Generic organizer for kids-show files (e.g. ripped DVDs, downloaded episodes) into
the Jellyfin naming convention:
    /Kids Shows/Show Name (year)/Season NN/Show Name (year) - sNNeNN - Optional Title.ext

Parses show names and episode numbers algorithmically (no hardcoded titles).
Handles both folder-based shows and loose episode files in the library root.

USAGE
    python3 organize-kids-shows.py                          # dry run
    python3 organize-kids-shows.py --apply                  # perform the renames
    python3 organize-kids-shows.py --bare-number-episodes   # also handle "Name 1..N"

OPTIONS
    --apply                 Perform the moves (default is dry run).
    --root PATH             Library root (default: current directory).
    --sub-lang CODE         Language code inserted into subtitle filenames (extension is
                            kept as-is), e.g. "en" -> "Show.s01e01.en.srt" / ".en.ass".
                            Default is empty -> "Show.s01e01.srt".
    --bare-number-episodes  Treat files with a trailing bare number and no sNNeNN
                            (e.g. "PAW Patrol Jet to the Rescue 1") as s01eNN. Off by
                            default so real movie folders are not mistaken for shows.

WHAT IT DOES
    - Extracts the show name and premiere year from folder names and filenames.
    - Strips release junk (resolution, source, codec, audio, group tags, etc.).
    - Detects sNNeNN episode markers and rebuilds "Season NN" folders.
    - Falls back to bare numbers (1, 2, 3...) as season 1 episodes when
      --bare-number-episodes is set.
    - Rebuilds "Season NN" subfolders from the episode numbers.
    - Light title-casing for all-lowercase scene names.
    - Already-correct "Show Name (year)/Season NN/..." layouts are detected
      and left untouched.
    - Never overwrites: existing targets and no-op renames are skipped.
    - Empty leftover folders are removed after a successful --apply.
"""

import argparse
import os
import re

VIDEO_EXTS = {".mkv", ".mp4", ".m4v", ".avi", ".mov"}
SUB_EXTS = {".srt", ".ass", ".ssa", ".sub", ".vtt"}

SE_RE = re.compile(r"[Ss](\d{1,2})[Ee](\d{1,2})")
BARE_RE = re.compile(r"(?:^|[\s._-])(\d{1,2})\s*$")
SEASON_DIR_RE = re.compile(r"[Ss]eason\s*(\d{1,2})")

ALREADY_RE = re.compile(
    r"^(?P<title>.+?) \((?P<year>\d{4})\)$"
)

QUALITY_RE = re.compile(
    r"\b(?:\d{3,4}p|4k|2160p|1080i|bluray|blu-ray|brrip|bdrip|bdremux|remux|"
    r"web[- ]?dl|webrip|hdtv|hdrip|dvdrip|dvdscr|hdts|telesync|hdcam|"
    r"x264|x265|h\s?264|h\s?265|hevc|avc|xvid|divx|"
    r"aac|ac3|dd5|ddp5|ddp|dts|truehd|atmos|flac|mp3|opus|"
    r"10bit|8bit|hdr10|hdr|sdr|yify|yts|vostfr)\b",
    re.IGNORECASE,
)

NOISE_RE = re.compile(
    r"\b(?:proper|repack|internal|retail|limited|multi|complete|hybrid|"
    r"open\s?matte|uncut|dubbed|subbed)\b",
    re.IGNORECASE,
)

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


class ShowIdentity:
    __slots__ = ("title", "year", "already")

    def __init__(self, title, year, already=False):
        self.title = title
        self.year = year
        self.already = already


def parse_show_identity(name):
    """Parse a show name into (title, year). Returns None if no year."""
    m = ALREADY_RE.match(name)
    if m:
        return ShowIdentity(m.group("title"), int(m.group("year")), already=True)

    norm = re.sub(r"[._]+", " ", name)
    norm = re.sub(r"\s+", " ", norm).strip()

    q = QUALITY_RE.search(norm)
    head = norm[:q.start()] if q else norm

    years = list(re.finditer(r"\b(?:19|20)\d{2}\b", head))
    if not years:
        return None
    ym = years[-1]
    year = int(ym.group(0))

    title = head[:ym.start()].strip()
    if not title:
        title = head[ym.end():].strip()

    title = NOISE_RE.sub(" ", title)
    title = re.sub(r"\s+", " ", title).strip(" -._(")
    if not title:
        return None
    return ShowIdentity(smart_title(title), year)


def parse_episode(stem):
    """Return (season, episode, title) or None."""
    m = SE_RE.search(stem)
    if m:
        ss, ee = int(m.group(1)), int(m.group(2))
        rest = stem[m.end():]
        title = rest.replace("_", " ").replace(".", " ")
        title = re.sub(r"\s+", " ", title).strip(" -")
        tokens = [t for t in title.split() if not QUALITY_RE.match(t)]
        title = " ".join(tokens).strip(" -")
        return ss, ee, title
    m2 = BARE_RE.search(stem)
    if m2:
        return 1, int(m2.group(1)), ""
    return None


def season_from_folder(path):
    """Try to detect a season number from the parent folder name."""
    parent = os.path.basename(os.path.dirname(path))
    m = SEASON_DIR_RE.search(parent)
    if m:
        return int(m.group(1))
    years = list(re.finditer(r"\b(?:19|20)\d{2}\b", parent))
    if years:
        return None
    m2 = BARE_RE.search(parent)
    if m2:
        return 1
    return None


def show_folder_name(ident):
    title = clean_show_name(ident.title)
    if ident.year:
        return f"{title} ({ident.year})"
    return title


def clean_show_name(name):
    name = re.sub(r"[._]+", " ", name)
    name = name.replace(":", "")
    return re.sub(r"\s+", " ", name).strip()


def sub_stem(stem):
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
    ap.add_argument("--sub-lang", default="")
    ap.add_argument("--bare-number-episodes", action="store_true")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    apply = args.apply
    sub_lang = args.sub_lang.strip(".")
    bare = args.bare_number_episodes

    print(f"root={root}  mode={'APPLY' if apply else 'DRY RUN'}  "
          f"sub-lang={sub_lang or '<none>'}  "
          f"bare-numbers={'on' if bare else 'off'}")
    print("-" * 70)

    moves = []
    warnings = []
    old_dirs = []

    def plan_episode(src_path, ident, ss, ee, title, kind, ext):
        base = f"{show_folder_name(ident)} - s{ss:02d}e{ee:02d}"
        if title:
            base += f" - {title}"
        if kind == "sub" and sub_lang:
            fname = f"{base}.{sub_lang}{ext}"
        else:
            fname = f"{base}{ext}"
        target_dir = os.path.join(root, show_folder_name(ident), f"Season {ss:02d}")
        moves.append((src_path, os.path.join(target_dir, fname)))

    entries = sorted(os.listdir(root))
    loose = []

    for entry in entries:
        full = os.path.join(root, entry)
        if not os.path.isdir(full):
            kind, _ = media_kind(entry)
            if kind:
                loose.append(entry)
            continue

        ident = parse_show_identity(entry)
        if ident is None:
            show_name = clean_show_name(entry)
            ident = ShowIdentity(show_name, 0)
        else:
            show_name = ident.title

        new_show_dir = os.path.join(root, show_folder_name(ident))
        old_dirs.append(full)

        episodes = []
        for dp, _d, files in os.walk(full):
            for fn in files:
                kind, ext = media_kind(fn)
                if kind is None:
                    continue
                fpath = os.path.join(dp, fn)
                stem = os.path.splitext(fn)[0]
                if kind == "sub":
                    stem = sub_stem(stem)
                ep = parse_episode(stem)
                if ep:
                    ss, ee, title = ep
                    episodes.append((fpath, ss, ee, title, kind, ext))
                elif bare:
                    bare_m = BARE_RE.search(stem)
                    if bare_m:
                        episodes.append((fpath, 1, int(bare_m.group(1)), "", kind, ext))

        if not episodes:
            hint = (f"no episode numbers in '{entry}' — looks like a movie/special; "
                    f"move it to a Movies library (left untouched)")
            if not bare:
                hint += "  [if these are episodes named 'Name 1..N', add --bare-number-episodes]"
            warnings.append(hint)
            continue

        ep_best = {}
        for fpath, ss, ee, title, kind, ext in episodes:
            if title:
                key = (ss, ee)
                if len(title) > len(ep_best.get(key, "")):
                    ep_best[key] = title

        for fpath, ss, ee, title, kind, ext in episodes:
            title = ep_best.get((ss, ee), title)
            plan_episode(fpath, ident, ss, ee, title, kind, ext)

    for fn in loose:
        kind, ext = media_kind(fn)
        stem = os.path.splitext(fn)[0]
        if kind == "sub":
            stem = sub_stem(stem)
        ep = parse_episode(stem)
        if not ep:
            if bare:
                bare_m = BARE_RE.search(stem)
                if bare_m:
                    ep = (1, int(bare_m.group(1)), "")
        if not ep:
            warnings.append(f"could not parse episode (file left as-is): {fn}")
            continue
        ss, ee, title = ep
        ident = parse_show_identity(stem)
        if ident is None:
            ident = ShowIdentity(fn.split(".")[0].replace(".", " ").replace("_", " ").strip(), 0)
        plan_episode(os.path.join(root, fn), ident, ss, ee, title, kind, ext)

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

    if apply:
        for base in old_dirs:
            for dp, dirs, files in os.walk(base, topdown=False):
                try:
                    if not os.listdir(dp):
                        os.rmdir(dp)
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
