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
                            (e.g. "PAW Patrol Jet to the Rescue 1") as episodes. Off by
                            default so real movie folders are not mistaken for shows.

WHAT IT DOES
    - Extracts the show name and premiere year from folder names and filenames.
    - Strips release junk (resolution, source, codec, audio, group tags, etc.).
    - Detects sNNeNN episode markers and rebuilds "Season NN" folders.
    - Falls back to bare numbers (1, 2, 3...) as episodes only when
      --bare-number-episodes is set.
    - Season numbers come from a "Season NN" parent folder when the filename does
      not carry one.
    - Light title-casing for all-lowercase scene names.
    - Already-correct "Show Name (year)/Season NN/..." layouts are detected
      and left untouched.
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


SEASON_TOKEN_RE = re.compile(r"\b[Ss]\d{1,2}(?:[Ee]\d{1,2})?\b")


def fallback_show_title(name):
    """Derive a show title from a release name that carries no year.

    Kids-show rips frequently have no year at all, so cut the release tail,
    any sNN/sNNeNN marker and a trailing "Season N" and keep what is left.
    Returns None if nothing usable remains.
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
    norm = NOISE_RE.sub(" ", norm)
    norm = re.sub(r"\s+", " ", norm).strip(" -._([")
    if not norm:
        return None
    return smart_title(norm)


def parse_episode(stem, allow_bare):
    """Return (season, episode, title) or None.

    season is None when the number came from a trailing bare number, in which
    case the caller resolves the season from the containing folder.
    """
    m = SE_RE.search(stem)
    if m:
        ss, ee = int(m.group(1)), int(m.group(2))
        rest = stem[m.end():]
        title = rest.replace("_", " ").replace(".", " ")
        title = re.sub(r"\s+", " ", title).strip(" -")
        tokens = [t for t in title.split() if not QUALITY_RE.match(t)]
        title = " ".join(tokens).strip(" -")
        return ss, ee, title
    if allow_bare:
        m2 = BARE_RE.search(stem)
        if m2:
            return None, int(m2.group(1)), ""
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


def clean_show_name(name):
    name = re.sub(r"[._]+", " ", name)
    return safe_component(name)


def show_folder_name(ident):
    title = clean_show_name(ident.title)
    if ident.year:
        return f"{title} ({ident.year})"
    return title


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
        description="Organize kids show files into the Jellyfin naming convention.",
    )
    ap.add_argument("--root", default=".", help="Library root (default: .)")
    ap.add_argument("--apply", action="store_true",
                    help="Execute the moves (default is dry run)")
    ap.add_argument("--sub-lang", default="",
                    help="Language code for subtitle filenames (default: none)")
    ap.add_argument("--bare-number-episodes", action="store_true",
                    help="Treat a trailing bare number as an episode number")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    apply = args.apply
    sub_lang = args.sub_lang.strip(".")
    bare = args.bare_number_episodes

    if not os.path.isdir(root):
        print(f"Error: '{root}' is not a directory", file=sys.stderr)
        sys.exit(1)

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
            base += f" - {safe_component(title)}"
        if kind == "sub" and sub_lang:
            fname = f"{base}.{sub_lang}{ext}"
        else:
            fname = f"{base}{ext}"
        target_dir = os.path.join(root, show_folder_name(ident), f"Season {ss:02d}")
        moves.append((src_path, os.path.join(target_dir, fname)))

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
            for fpath, kind, ext in groups[key]:
                plan_episode(fpath, ident, 0, index, key, kind, ext)
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
        if ident is None:
            ident = ShowIdentity(
                fallback_show_title(entry) or clean_show_name(entry), 0
            )

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
                    ss, ee, title = ep
                    if ss is None:
                        folder_season = season_from_folder(fpath)
                        ss = folder_season if folder_season is not None else 1
                    episodes.append((fpath, ss, ee, title, kind, ext))
                else:
                    unmatched.append((fpath, fn, kind, ext))

        if not episodes and unmatched:
            hint = (f"no episode numbers in '{entry}' — looks like a movie/special; "
                    f"left untouched")
            if not bare:
                hint += ("  [if these are episodes named 'Name 1..N', "
                         "add --bare-number-episodes]")
            warnings.append(hint)
            old_dirs.pop()
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

        plan_specials(unmatched, ident, entry)

    for fn in loose:
        kind, ext = media_kind(fn)
        stem = os.path.splitext(fn)[0]
        if kind == "sub":
            stem = sub_stem(stem)
        ep = parse_episode(stem, bare)
        if not ep:
            warnings.append(f"could not parse episode (file left as-is): {fn}")
            continue
        ss, ee, title = ep
        if ss is None:
            ss = 1
        ident = parse_show_identity(stem)
        if ident is None:
            ident = ShowIdentity(
                fallback_show_title(stem)
                or clean_show_name(fn.split(".")[0].replace("_", " ").strip()), 0
            )
        plan_episode(os.path.join(root, fn), ident, ss, ee, title, kind, ext)

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
