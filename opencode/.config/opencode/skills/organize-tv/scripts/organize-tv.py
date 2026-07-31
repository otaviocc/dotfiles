#!/usr/bin/env python3
"""
organize-tv.py

Generic organizer for TV show files in a Jellyfin TV library.  Parses scene-style
names algorithmically (no hardcoded titles) into the Jellyfin TV series convention:
    /TV Shows/Show Name (year)/Season NN/Show Name (year) - sNNeNN - Optional Title.ext
Reference: https://jellyfin.org/docs/general/server/media/show-naming/

USAGE
    1. Copy this script to the root of your TV library.
    2. Dry run (default, changes nothing):   python3 organize-tv.py
    3. Inspect the planned moves.
    4. Apply for real:                       python3 organize-tv.py --apply

OPTIONS
    --apply             Execute the moves (default is dry run).
    --root PATH         Library root (default: current directory).
    --minimal           Drop episode titles; name files "Show (year) - sNNeNN.ext".
    --sub-lang CODE     Language code inserted into subtitle filenames (extension is
                        kept as-is), e.g. "en" -> "...s01e01.en.srt" / "...en.ass".
                        Default is "en".

WHAT IT DOES
    - Handles both layouts a download produces: a show FOLDER (with or without
      Season subfolders) and LOOSE episode files in the library root.
    - Extracts the show name and premiere year algorithmically from scene-style
      names (no hardcoded titles).
    - Detects editions (e.g. Director's Cut, Extended) and emits {edition-...} tags.
    - Strips release junk (resolution, codec, audio, group tags, REMASTERED, etc.).
    - Light title-casing for all-lowercase scene names.
    - Already-correct "Show (year)" files/folders are detected and left untouched.
    - Multi-episode files (sNNeNN-eNN) are detected and named correctly.
    - Files without sNNeNN but with bare numbers are handled as season 1 episodes.
    - Never overwrites: existing targets and no-op renames are skipped.
    - Empty leftover folders are removed after a successful --apply.
"""

import argparse
import os
import re

VIDEO_EXTS = {".mkv", ".mp4", ".m4v", ".avi", ".mov", ".ts"}
SUB_EXTS = {".srt", ".ass", ".ssa", ".sub", ".vtt"}

SE_RE = re.compile(r"[Ss](\d{1,2})[Ee](\d{1,2})")
MULTI_EPRE = re.compile(r"[\s._-]*-?\s*[eE](\d{1,2})\b")
MULTI_PAREN_RE = re.compile(r"\((\d+)\)[\s._]*and[\s._]*\((\d+)\)")
BARE_RE = re.compile(r"(?:^|[\s._-])(\d{1,2})\s*$")
SEASON_DIR_RE = re.compile(r"[Ss]eason\s*(\d{1,2})")

ALREADY_RE = re.compile(
    r"^(?P<title>.+?) \((?P<year>\d{4})\)(?: \{edition-(?P<ed>[^}]+)\})?$"
)

QUALITY_RE = re.compile(
    r"\b(?:\d{3,4}p|4k|2160p|1080i|bluray|blu-ray|brrip|bdrip|bdremux|remux|"
    r"web[- ]?dl|webrip|hdtv|hdrip|dvdrip|dvdscr|hdts|telesync|hdcam|"
    r"x264|x265|h\s?264|h\s?265|hevc|avc|xvid|divx|"
    r"aac|ac3|dd5|ddp5|ddp|dts|truehd|atmos|flac|mp3|opus|"
    r"10bit|8bit|hdr10|hdr|sdr|yify|yts|vostfr)\b",
    re.IGNORECASE,
)

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
    __slots__ = ("title", "year", "edition", "already")

    def __init__(self, title, year, edition=None, already=False):
        self.title = title
        self.year = year
        self.edition = edition
        self.already = already


def parse_show_identity(name):
    """Parse a show name into (title, year, edition). Returns None if no year."""
    m = ALREADY_RE.match(name)
    if m:
        return ShowIdentity(m.group("title"), int(m.group("year")),
                            m.group("ed"), already=True)

    norm = re.sub(r"[._]+", " ", name)
    norm = re.sub(r"\s+", " ", norm).strip()

    q = QUALITY_RE.search(norm)
    head = norm[:q.start()] if q else norm

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

    title = head[:ym.start()].strip()
    if not title:
        title = head[ym.end():].strip()

    title = NOISE_RE.sub(" ", title)
    title = re.sub(r"\s+", " ", title).strip(" -._(")
    if not title:
        return None
    return ShowIdentity(smart_title(title), year,
                        " ".join(editions) if editions else None)


def parse_episode(stem):
    """Return (season, episode, episode2, title) or None."""
    m = SE_RE.search(stem)
    if m:
        ss, ee = int(m.group(1)), int(m.group(2))
        after = stem[m.end():]
        ee2 = None
        m2 = MULTI_EPRE.search(after)
        if m2:
            ee2 = int(m2.group(1))
            after = after[:m2.start()]
        else:
            m3 = MULTI_PAREN_RE.search(after)
            if m3:
                ee2 = ee + 1
                after = after[:m3.start()]
        title = clean_episode_title(after)
        return ss, ee, ee2, title
    m2 = BARE_RE.search(stem)
    if m2:
        return 1, int(m2.group(1)), None, ""
    return None


def season_from_folder(path):
    """Try to detect a season number from the folder containing a file."""
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


RES_RE = re.compile(r"^\d{3,4}p$", re.IGNORECASE)
LEADING_JUNK = {"repack", "proper", "internal", "real"}


def clean_episode_title(text):
    s = text.replace("_", " ").replace(".", " ")
    s = re.sub(r"\s+", " ", s).strip()
    if not s:
        return ""
    tokens = []
    for tok in s.split(" "):
        if RES_RE.match(tok):
            break
        tokens.append(tok)
    while tokens and tokens[0].lower() in LEADING_JUNK:
        tokens.pop(0)
    title = " ".join(tokens).strip(" -")
    title = re.sub(r"\s*\[[^\]]*$", "", title).strip(" -")
    return title


def show_folder_name(ident, editions_on):
    name = f"{ident.title} ({ident.year})"
    if ident.edition and editions_on:
        name += f" {{edition-{ident.edition}}}"
    return name


def ep_tag(ss, ee, ee2):
    tag = f"s{ss:02d}e{ee:02d}"
    if ee2 is not None:
        tag += f"-e{ee2:02d}"
    return tag


def file_base(ident, editions_on, ss, ee, ee2, title, part=None, minimal=False):
    base = f"{show_folder_name(ident, editions_on)} - {ep_tag(ss, ee, ee2)}"
    if title and not minimal:
        base += f" - {title}"
    if part is not None:
        base += f" - pt{part}"
    return base


def season_dir(ss):
    return "Season 00" if ss == 0 else f"Season {ss:02d}"


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
    ap.add_argument("--minimal", action="store_true")
    ap.add_argument("--sub-lang", default="en")
    args = ap.parse_args()

    global MINIMAL, SUB_LANG
    MINIMAL = args.minimal
    SUB_LANG = args.sub_lang.strip(".")
    root = os.path.abspath(args.root)
    apply = args.apply

    print(f"root={root}  mode={'APPLY' if apply else 'DRY RUN'}  "
          f"titles={'minimal' if MINIMAL else 'keep'}  sub-lang={SUB_LANG}")
    print("-" * 70)

    moves = []
    warnings = []
    old_dirs = []

    def plan_episode(src_path, ident, title, ss, ee, ee2, kind, ext):
        if MINIMAL:
            title = ""
        base = file_base(ident, editions_on=True, ss=ss, ee=ee, ee2=ee2,
                         title=title, minimal=MINIMAL)
        if kind == "sub" and SUB_LANG:
            fname = f"{base}.{SUB_LANG}{ext}"
        else:
            fname = f"{base}{ext}"
        target_dir = os.path.join(root, show_folder_name(ident, True), season_dir(ss))
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
            videos = []
            for dp, _d, files in os.walk(full):
                for fn in files:
                    k, _ = media_kind(fn)
                    if k == "video":
                        videos.append(fn)
            for v in sorted(videos, key=len, reverse=True):
                ident = parse_show_identity(os.path.splitext(v)[0])
                if ident:
                    break
        if ident is None:
            warnings.append(f"could not parse show folder (left as-is): {entry}")
            continue

        new_show_dir = os.path.join(root, show_folder_name(ident, True))
        old_dirs.append(full)

        episodes = []
        unmatched = []
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
                    ss, ee, ee2, title = ep
                    if ss is None:
                        fs = season_from_folder(fpath)
                        ss = fs if fs is not None else 1
                    episodes.append((fpath, title, ss, ee, ee2, kind, ext))
                else:
                    unmatched.append((fpath, fn, kind, ext))

        ep_best = {}
        for path, title, ss, ee, ee2, kind, ext in episodes:
            if ee2 is None and title:
                key = (ss, ee)
                if len(title) > len(ep_best.get(key, "")):
                    ep_best[key] = title

        for path, title, ss, ee, ee2, kind, ext in episodes:
            if ee2 is None:
                title = ep_best.get((ss, ee), title)
            plan_episode(path, ident, title, ss, ee, ee2, kind, ext)

        for fpath, fn, kind, ext in unmatched:
            stem = os.path.splitext(fn)[0]
            sub = sub_stem(stem) if kind == "sub" else stem
            ident2 = parse_show_identity(sub)
            if ident2 is None:
                ident2 = ident
            plan_episode(fpath, ident2, "", 0, 1, None, kind, ext)

    for fn in loose:
        kind, ext = media_kind(fn)
        stem = os.path.splitext(fn)[0]
        sub = sub_stem(stem) if kind == "sub" else stem
        ep = parse_episode(sub)
        if not ep:
            ident2 = parse_show_identity(sub)
            if ident2 is None:
                warnings.append(f"could not parse (file left as-is): {fn}")
                continue
            plan_episode(os.path.join(root, fn), ident2, "", 0, 1, None, kind, ext)
        else:
            ss, ee, ee2, title = ep
            ident2 = parse_show_identity(sub)
            if ident2 is None:
                ident2 = ShowIdentity(fn.split(".")[0].replace(".", " ").replace("_", " ").strip(), 0)
            plan_episode(os.path.join(root, fn), ident2, title, ss, ee, ee2, kind, ext)

    done = skipped = 0
    for src, dst in moves:
        dst = dst.replace(":", "")
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
    MINIMAL = False
    SUB_LANG = "en"
    main()
