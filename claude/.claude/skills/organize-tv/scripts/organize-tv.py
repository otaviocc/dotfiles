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
    --apply                 Execute the moves (default is dry run).
    --root PATH             Library root (default: current directory).
    --minimal               Drop episode titles; name files "Show (year) - sNNeNN.ext".
    --sub-lang CODE         Language code inserted into subtitle filenames (extension
                            is kept as-is), e.g. "en" -> "...s01e01.en.srt".
                            Default is empty -> "...s01e01.srt".
    --bare-number-episodes  Treat a trailing bare number with no sNNeNN (e.g.
                            "Show Name 3") as an episode number. Off by default so
                            movies and specials are not mistaken for episodes.

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
    - Season numbers come from a "Season NN" parent folder when the filename does
      not carry one.
    - Files with no detectable episode number are filed as Season 00 specials,
      numbered in filename order and keeping their original name as the title.
    - Never overwrites: destinations claimed twice, or already occupied, are
      reported and skipped before anything moves.
    - Empty leftover folders are removed after a successful --apply.
"""

import argparse
import os
import re
import shutil
import sys

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

# Characters that are illegal or troublesome in a path component on the
# filesystems a media library is typically served from (APFS, ext4, SMB/NTFS).
UNSAFE_DASH_RE = re.compile(r"[/\\|]")
UNSAFE_DROP_RE = re.compile(r'[:?"*<>\x00-\x1f]')


def safe_component(name):
    """Make a string safe to use as a single path component.

    Titles are derived from untrusted source filenames, so separators and
    reserved characters are rewritten rather than passed through into a path.
    """
    name = UNSAFE_DASH_RE.sub("-", name)
    name = UNSAFE_DROP_RE.sub("", name)
    name = re.sub(r"\s+", " ", name).strip(" .")
    return name or "_"


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


SEASON_TOKEN_RE = re.compile(r"\b[Ss]\d{1,2}(?:[Ee]\d{1,2})?\b")


def fallback_show_title(name):
    """Derive a show title from a release name that carries no year.

    Most scene TV releases omit the year ("Severance.S01.1080p.ATVP.WEB-DL"),
    so cut the release tail, any sNN/sNNeNN marker and a trailing "Season N"
    and keep what is left. Returns None if nothing usable remains.
    """
    norm = re.sub(r"[._]+", " ", name)
    norm = re.sub(r"\s+", " ", norm).strip()
    q = QUALITY_RE.search(norm)
    if q:
        norm = norm[:q.start()]
    s = SEASON_TOKEN_RE.search(norm)
    if s:
        norm = norm[:s.start()]
    norm = re.sub(r"\b[Ss]eason\s*\d{1,2}\b.*$", "", norm)
    for rgx, _label in EDITION_PATTERNS:
        norm = rgx.sub(" ", norm)
    norm = NOISE_RE.sub(" ", norm)
    norm = re.sub(r"\s+", " ", norm).strip(" -._([")
    if not norm:
        return None
    return smart_title(norm)


def parse_episode(stem, allow_bare):
    """Return (season, episode, episode2, title) or None.

    season is None when the number came from a trailing bare number, in which
    case the caller resolves the season from the containing folder.
    """
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
    if allow_bare:
        m2 = BARE_RE.search(stem)
        if m2:
            return None, int(m2.group(1)), None, ""
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
    name = f"{ident.title} ({ident.year})" if ident.year else ident.title
    if ident.edition and editions_on:
        name += f" {{edition-{ident.edition}}}"
    return safe_component(name)


def ep_tag(ss, ee, ee2):
    tag = f"s{ss:02d}e{ee:02d}"
    if ee2 is not None:
        tag += f"-e{ee2:02d}"
    return tag


def file_base(ident, editions_on, ss, ee, ee2, title, part=None, minimal=False):
    base = f"{show_folder_name(ident, editions_on)} - {ep_tag(ss, ee, ee2)}"
    if title and not minimal:
        base += f" - {safe_component(title)}"
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
            for _src, dst, _ in blocked:
                print(f"  !! blocked, target still occupied: {rel(dst)}",
                      file=sys.stderr)
                skipped += 1
            break
        for src, dst, _ in ready:
            try:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.move(src, dst)
                done += 1
            except OSError as exc:
                print(f"  !! error moving {rel(src)}: {exc}", file=sys.stderr)
                errors += 1
        remaining = blocked
    return done, skipped, errors


def prune_empty_dirs(root, candidates):
    removed = 0
    root_abs = os.path.abspath(root)
    for base in candidates:
        if not os.path.isdir(base):
            continue
        for dirpath, _dirs, _files in os.walk(base, topdown=False):
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
    ap = argparse.ArgumentParser(
        description="Organize TV files into the Jellyfin show-naming convention.",
    )
    ap.add_argument("--root", default=".", help="Library root (default: .)")
    ap.add_argument("--apply", action="store_true",
                    help="Execute the moves (default is dry run)")
    ap.add_argument("--minimal", action="store_true",
                    help="Drop episode titles from filenames")
    ap.add_argument("--sub-lang", default="",
                    help="Language code for subtitle filenames (default: none)")
    ap.add_argument("--bare-number-episodes", action="store_true",
                    help="Treat a trailing bare number as an episode number")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    apply = args.apply
    minimal = args.minimal
    sub_lang = args.sub_lang.strip(".")
    bare = args.bare_number_episodes

    if not os.path.isdir(root):
        print(f"Error: '{root}' is not a directory", file=sys.stderr)
        sys.exit(1)

    print(f"root={root}  mode={'APPLY' if apply else 'DRY RUN'}  "
          f"titles={'minimal' if minimal else 'keep'}  "
          f"sub-lang={sub_lang or '<none>'}  "
          f"bare-numbers={'on' if bare else 'off'}")
    print("-" * 70)

    moves = []
    warnings = []
    old_dirs = []
    canonical = {}          # case-insensitive show folder -> canonical title
    warned_no_year = set()  # shows already reported as missing a year

    def plan_episode(src_path, ident, title, ss, ee, ee2, kind, ext):
        base = file_base(ident, True, ss, ee, ee2,
                         "" if minimal else title, minimal=minimal)
        if kind == "sub" and sub_lang:
            fname = f"{base}.{sub_lang}{ext}"
        else:
            fname = f"{base}{ext}"
        target_dir = os.path.join(root, show_folder_name(ident, True), season_dir(ss))
        moves.append((src_path, os.path.join(target_dir, fname)))

    def canonicalize(ident):
        key = show_folder_name(ident, True).lower()
        if key in canonical:
            ident.title = canonical[key]
        else:
            canonical[key] = ident.title
        return ident

    def plan_specials(items, ident, label):
        """File items with no episode number as numbered Season 00 specials.

        Videos and their subtitles are grouped by stem so a pair keeps one
        number, and the original name becomes the episode title so the files
        stay identifiable.
        """
        groups = {}
        for fpath, fn, kind, ext in items:
            stem = os.path.splitext(fn)[0]
            key = sub_stem(stem) if kind == "sub" else stem
            groups.setdefault(key, []).append((fpath, kind, ext))
        for index, key in enumerate(sorted(groups), start=1):
            title = clean_episode_title(key) or key
            for fpath, kind, ext in groups[key]:
                plan_episode(fpath, ident, title, 0, index, None, kind, ext)
        if groups:
            warnings.append(
                f"{len(groups)} item(s) in '{label}' had no episode number — "
                f"filed as Season 00 specials"
                + ("" if bare else
                   "  [if they are episodes named 'Name 1..N', "
                   "add --bare-number-episodes]")
            )

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
        videos = []
        if ident is None:
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
            # No year anywhere: fall back to a year-less show folder, which
            # Jellyfin still matches (less reliably than "Show (year)").
            title = fallback_show_title(entry)
            if title is None:
                for v in sorted(videos, key=len, reverse=True):
                    title = fallback_show_title(os.path.splitext(v)[0])
                    if title:
                        break
            if title is None:
                warnings.append(f"could not parse show folder (left as-is): {entry}")
                continue
            ident = ShowIdentity(title, 0)
            # Only worth saying while the folder is still being reshaped; an
            # already-settled year-less library should not re-warn every run.
            if entry != show_folder_name(ident, True):
                warnings.append(
                    f"no year detected in '{entry}' — filing under '{title}'; "
                    f"rename to '{title} (year)' for a reliable Jellyfin match"
                )

        ident = canonicalize(ident)
        old_dirs.append(full)

        episodes = []
        unmatched = []
        for dp, _d, files in os.walk(full):
            for fn in sorted(files):
                kind, ext = media_kind(fn)
                if kind is None:
                    continue
                fpath = os.path.join(dp, fn)
                stem = os.path.splitext(fn)[0]
                if kind == "sub":
                    stem = sub_stem(stem)
                ep = parse_episode(stem, bare)
                if ep:
                    ss, ee, ee2, title = ep
                    if ss is None:
                        folder_season = season_from_folder(fpath)
                        ss = folder_season if folder_season is not None else 1
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

        plan_specials(unmatched, ident, entry)

    loose_specials = {}
    for fn in loose:
        kind, ext = media_kind(fn)
        stem = os.path.splitext(fn)[0]
        sub = sub_stem(stem) if kind == "sub" else stem
        ident = parse_show_identity(sub)
        ep = parse_episode(sub, bare)
        if ident is None:
            # Only fall back for files that clearly are episodes; a loose file
            # with neither a year nor an episode marker is most likely a movie.
            title = fallback_show_title(sub) if ep is not None else None
            if title is None:
                warnings.append(f"could not parse (file left as-is): {fn}")
                continue
            ident = ShowIdentity(title, 0)
            if title not in warned_no_year:
                warned_no_year.add(title)
                warnings.append(
                    f"no year detected for '{title}' — filing under '{title}'; "
                    f"add the year for a reliable Jellyfin match"
                )
        ident = canonicalize(ident)
        if ep is None:
            loose_specials.setdefault(show_folder_name(ident, True), (ident, []))
            loose_specials[show_folder_name(ident, True)][1].append(
                (os.path.join(root, fn), fn, kind, ext)
            )
            continue
        ss, ee, ee2, title = ep
        if ss is None:
            ss = 1
        plan_episode(os.path.join(root, fn), ident, title, ss, ee, ee2, kind, ext)

    for label, (ident, items) in sorted(loose_specials.items()):
        plan_specials(items, ident, label)

    done, skipped, errors = execute_moves(moves, root, apply)

    removed = prune_empty_dirs(root, old_dirs) if apply else 0

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
