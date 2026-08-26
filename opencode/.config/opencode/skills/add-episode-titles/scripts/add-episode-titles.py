#!/usr/bin/env python3
"""
add-episode-titles.py

Backfills missing episode titles into TV filenames using the TVMaze API
(no API key required, network access needed).

Supports two filename formats:
    /TV Shows/Show Name (year)/Season 01/
        Show Name (year) - s01e01.mkv
            -> Show Name (year) - s01e01 - Episode Title.mkv

    /TV Shows/Show Name/Season 01/
        Show Name - s01e01.mkv
            -> Show Name (year) - s01e01 - Episode Title.mkv  (+ dir rename)

Files without a year are resolved against TVMaze to determine the premiere
year, which is then added to both the filename and the parent directory name.

Episode titles come from a remote API, so characters that are not legal in a
path component (a slash in "Part 1/2", a colon, ...) are rewritten before the
name is used.

USAGE
    1. Dry run (default, changes nothing):  python3 add-episode-titles.py --root /path/to/tv
    2. Inspect the planned renames.
    3. Apply for real:                      python3 add-episode-titles.py --root /path/to/tv --apply

OPTIONS
    --root PATH           TV library root (default: current directory).
    --apply               Execute the renames (default is dry run).
    --multi-ep-first      Use the first episode's title for multi-episode files
                          (s01e01-e02). Default is to skip them.
    --threshold FLOAT     Minimum similarity (0..1) required to accept a TVMaze
                          show match (default 0.75).
    --timeout SECONDS     HTTP timeout for TVMaze requests (default 15).
"""

import argparse
import difflib
import json
import os
import re
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.tvmaze.com"
USER_AGENT = "add-episode-titles/1.1 (personal Jellyfin library)"
VIDEO_EXTS = {".mkv", ".mp4", ".m4v", ".avi", ".mov", ".ts"}
SUB_EXTS = {".srt", ".ass", ".ssa", ".sub", ".vtt"}
REQUEST_GAP = 0.35
MAX_RETRIES = 3

SUB_LANG_RE = re.compile(
    r"\.(?:eng|english|en|por|pt|spa|es|fre|fr|ger|de|ita|it|jpn|ja|kor|ko|"
    r"chi|zh|nld|nl|swe|sv|nor|no|dan|da|fin|fi|pol|pl|rus|ru|tur|tr|ara|"
    r"heb|he)$",
    re.IGNORECASE,
)

FILENAME_RE = re.compile(
    r"^(?P<show>.+?) \((?P<year>\d{4})\)"
    r"(?P<edition> \{edition-[^}]+\})? - "
    r"[sS](?P<season>\d{1,2})[eE](?P<ep>\d{1,2})"
    r"(?:-e(?P<ep2>\d{1,2}))?"
    r"(?: - (?P<title>.+))?$"
)

FILENAME_NO_YEAR_RE = re.compile(
    r"^(?P<show>.+?) - "
    r"[sS](?P<season>\d{1,2})[eE](?P<ep>\d{1,2})"
    r"(?:-e(?P<ep2>\d{1,2}))?"
    r"(?: - (?P<title>.+))?$"
)

# Characters that are illegal or troublesome in a path component on the
# filesystems a media library is typically served from (APFS, ext4, SMB/NTFS).
UNSAFE_DASH_RE = re.compile(r"[/\\|]")
UNSAFE_DROP_RE = re.compile(r'[:?"*<>\x00-\x1f]')


def safe_component(name):
    """Make a string safe to use as a single path component.

    Episode titles arrive from TVMaze and routinely contain characters that are
    illegal, or actively dangerous, inside a filename ("Part 1/2", "Chapter 4:
    The Trial"). Rewrite rather than trust them.
    """
    name = UNSAFE_DASH_RE.sub("-", name)
    name = UNSAFE_DROP_RE.sub("", name)
    name = re.sub(r"\s+", " ", name).strip(" .")
    return name or "_"


def normalize(text):
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def title_sim(a, b):
    return difflib.SequenceMatcher(None, normalize(a), normalize(b)).ratio()


_last_request = [0.0]
TIMEOUT = 15


def http_get(url):
    for attempt in range(MAX_RETRIES):
        gap = _last_request[0] + REQUEST_GAP - time.monotonic()
        if gap > 0:
            time.sleep(gap)
        _last_request[0] = time.monotonic()
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < MAX_RETRIES - 1:
                retry = float(e.headers.get("Retry-After", 10) or 10)
                time.sleep(min(retry, 30))
                continue
            if e.code == 404:
                return None
            raise
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 * (attempt + 1))
                continue
            print(f"  !! network error contacting TVMaze: {e}", file=sys.stderr)
            return None
    return None


def resolve_show(title, year, threshold):
    """Return (show, candidates). show is None when nothing clears threshold."""
    results = http_get(f"{API}/search/shows?q=" + urllib.parse.quote(title))
    if not results:
        return None, []
    scored = []
    for item in results:
        show = item["show"]
        sim = title_sim(title, show.get("name") or "")
        sy = None
        if show.get("premiered"):
            m = re.match(r"(\d{4})", show["premiered"])
            if m:
                sy = int(m.group(1))
        year_ok = year == 0 or sy == year
        scored.append((sim + (0.25 if year_ok else 0.0), sim, show))
    scored.sort(key=lambda t: t[0], reverse=True)
    candidates = [(s[2].get("name") or "?", str(s[2].get("premiered"))[:4], s[1])
                  for s in scored[:3]]
    best = scored[0]
    if best[1] < threshold:
        return None, candidates
    return best[2], candidates


def fetch_episodes(show):
    data = http_get(f"{API}/shows/{show['id']}/episodes")
    if not data:
        return {}
    out = {}
    for ep in data:
        season, number = ep.get("season"), ep.get("number")
        name = (ep.get("name") or "").strip()
        if season is not None and number is not None and name:
            out[(season, number)] = name
    return out


def new_stem(m, name, resolved_year=None):
    tag = f"s{int(m.group('season')):02d}e{int(m.group('ep')):02d}"
    if m.group("ep2"):
        tag += f"-e{int(m.group('ep2')):02d}"
    try:
        edition = m.group("edition") or ""
    except IndexError:
        edition = ""
    try:
        year = m.group("year")
    except IndexError:
        year = None
    if not year:
        year = str(resolved_year)
    return (f"{m.group('show')} ({year}){edition} - {tag} - "
            f"{safe_component(name)}")


def sub_sibling_names(dirpath, old_stem, new_base):
    out = []
    try:
        entries = os.listdir(dirpath)
    except OSError:
        return out
    for fn in sorted(entries):
        stem, ext = os.path.splitext(fn)
        if ext.lower() not in SUB_EXTS:
            continue
        lang = ""
        m = SUB_LANG_RE.search(stem)
        if m:
            lang = m.group(0)
            stem = stem[:m.start()]
        if stem == old_stem:
            out.append((os.path.join(dirpath, fn),
                        os.path.join(dirpath, new_base + lang + ext)))
    return out


def execute_moves(moves, root, apply, dir_renames=None):
    """Print, validate and optionally perform a list of (src, dst) moves.

    Resolves destinations claimed by several sources in favour of the largest
    file, refuses to overwrite anything already on disk, and defers a move whose
    destination is still held by a file that is itself scheduled to move away.
    Optionally renames directories after file moves are complete.
    Returns (done, skipped, errors).
    """
    if dir_renames is None:
        dir_renames = []

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
    for old_d, new_d in dir_renames:
        print(f"{rel(old_d)}\n   -> {rel(new_d)}")
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

    for old_d, new_d in dir_renames:
        if not os.path.isdir(old_d):
            continue
        if os.path.exists(new_d):
            print(f"  !! directory already exists, skipping: {rel(new_d)}",
                  file=sys.stderr)
            skipped += 1
            continue
        try:
            os.rename(old_d, new_d)
            done += 1
        except OSError as exc:
            print(f"  !! error renaming {rel(old_d)}: {exc}", file=sys.stderr)
            errors += 1

    return done, skipped, errors


def main():
    ap = argparse.ArgumentParser(
        description="Backfill episode titles into Jellyfin TV filenames via TVMaze.",
    )
    ap.add_argument("--root", default=".", help="TV library root (default: .)")
    ap.add_argument("--apply", action="store_true",
                    help="Execute the renames (default is dry run)")
    ap.add_argument("--multi-ep-first", action="store_true",
                    help="Use the first episode's title for multi-episode files")
    ap.add_argument("--threshold", type=float, default=0.75,
                    help="Minimum TVMaze title similarity to accept (default 0.75)")
    ap.add_argument("--timeout", type=int, default=15,
                    help="HTTP timeout in seconds (default 15)")
    args = ap.parse_args()

    global TIMEOUT
    TIMEOUT = args.timeout
    root = os.path.abspath(args.root)

    if not os.path.isdir(root):
        print(f"Error: '{root}' is not a directory", file=sys.stderr)
        sys.exit(1)

    print(f"root={root}  mode={'APPLY' if args.apply else 'DRY RUN'}  "
          f"threshold={args.threshold}")
    print("-" * 70)

    jobs = {}
    already_titled = 0
    for dp, _dirs, files in os.walk(root):
        for fn in sorted(files):
            stem, ext = os.path.splitext(fn)
            if ext.lower() not in VIDEO_EXTS:
                continue
            m = FILENAME_RE.match(stem)
            if m:
                if m.group("title"):
                    already_titled += 1
                    continue
                key = (m.group("show"), int(m.group("year")),
                       m.group("edition") or "", False)
                jobs.setdefault(key, []).append((os.path.join(dp, fn), m))
                continue
            m = FILENAME_NO_YEAR_RE.match(stem)
            if m:
                if m.group("title"):
                    already_titled += 1
                    continue
                key = (m.group("show"), 0, "", True)
                jobs.setdefault(key, []).append((os.path.join(dp, fn), m))

    if not jobs:
        print(f"no Jellyfin-formatted files missing episode titles found "
              f"(already titled: {already_titled})")
        return

    plans = []
    dir_renames = []
    stats = {"no_show": 0, "no_episode": 0, "multi_skip": 0}
    seen_shows = {}

    for (show, year, _edition, needs_year), items in sorted(jobs.items()):
        cache_key = (show.lower(), year)
        if cache_key not in seen_shows:
            print(f"\nresolving: {show} ({year})" if year else
                  f"\nresolving: {show} (no year)")
            tv, candidates = resolve_show(show, year, args.threshold)
            eps = {}
            if tv is None:
                print(f"  ?? no reliable TVMaze match — {len(items)} file(s) skipped")
                for name, premiered, sim in candidates:
                    print(f"     closest: {name} ({premiered})  similarity {sim:.2f}")
                if candidates:
                    print(f"     (lower --threshold below {args.threshold} to accept one)")
            else:
                eps = fetch_episodes(tv)
                print(f"  matched -> {tv['name']} ({str(tv.get('premiered'))[:4]})"
                      f"  {len(eps)} episode titles")
            seen_shows[cache_key] = (tv, eps)
        tv, eps = seen_shows[cache_key]

        if tv is None:
            stats["no_show"] += len(items)
            continue

        resolved_year = None
        if needs_year and tv.get("premiered"):
            m_year = re.match(r"(\d{4})", tv["premiered"])
            if m_year:
                resolved_year = int(m_year.group(1))

        for path, m in items:
            rel = os.path.relpath(path, root)
            ss, ee = int(m.group("season")), int(m.group("ep"))
            ep2 = int(m.group("ep2")) if m.group("ep2") else None
            if ep2 is not None and not args.multi_ep_first:
                stats["multi_skip"] += 1
                print(f"  -- multi-episode, skipping: {rel}")
                continue
            name = eps.get((ss, ee))
            if not name:
                stats["no_episode"] += 1
                print(f"  ?? s{ss:02d}e{ee:02d} not found in TVMaze: {rel}")
                continue
            base = new_stem(m, name, resolved_year)
            dst = os.path.join(os.path.dirname(path),
                               base + os.path.splitext(path)[1])
            plans.append((path, dst))
            old_stem = os.path.basename(os.path.splitext(path)[0])
            plans.extend(sub_sibling_names(os.path.dirname(path), old_stem, base))

            if needs_year and resolved_year:
                show_dir = os.path.dirname(os.path.dirname(path))
                dir_name = os.path.basename(show_dir)
                new_dir_name = f"{show} ({resolved_year})"
                if dir_name != new_dir_name:
                    new_show_dir = os.path.join(os.path.dirname(show_dir),
                                                new_dir_name)
                    pair = (show_dir, new_show_dir)
                    if pair not in dir_renames:
                        dir_renames.append(pair)

    print("-" * 70)
    done, skipped, errors = execute_moves(plans, root, args.apply,
                                         dir_renames)
    skipped += stats["multi_skip"]

    print("-" * 70)
    summary = (f"{'renamed' if args.apply else 'planned'}: {done}   "
               f"already titled: {already_titled}   skipped: {skipped}   "
               f"no show match: {stats['no_show']}   "
               f"no episode: {stats['no_episode']}")
    if errors:
        summary += f"   errors: {errors}"
    print(summary)
    if not args.apply:
        print("DRY RUN — re-run with --apply to execute")
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
