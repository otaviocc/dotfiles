#!/usr/bin/env python3
"""
add-episode-titles.py

Backfills missing episode titles into Jellyfin-organized TV filenames using the
TVMaze API (no API key required, network access needed):

    /TV Shows/Show Name (year)/Season 01/
        Show Name (year) - s01e01.mkv
            -> Show Name (year) - s01e01 - Episode Title.mkv

Only files already matching the Jellyfin show-naming convention are touched
(Show Name (year) - sNNeNN.ext). Files that already carry an episode title are
left alone. Matching subtitle files are renamed to stay paired with their video.

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
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.tvmaze.com"
USER_AGENT = "add-episode-titles/1.0 (personal Jellyfin library)"
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
    return None


def resolve_show(title, year, threshold):
    results = http_get(f"{API}/search/shows?q=" + urllib.parse.quote(title))
    if not results:
        return None
    best, best_score = None, -1.0
    for item in results:
        show = item["show"]
        sim = title_sim(title, show.get("name") or "")
        sy = None
        if show.get("premiered"):
            m = re.match(r"(\d{4})", show["premiered"])
            if m:
                sy = int(m.group(1))
        year_ok = year == 0 or sy == year
        score = sim + (0.25 if year_ok else 0.0)
        if score > best_score:
            best, best_score = show, score
    if best is None or title_sim(title, best.get("name") or "") < threshold:
        return None
    return best


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


def new_stem(m, name):
    tag = f"s{int(m.group('season')):02d}e{int(m.group('ep')):02d}"
    if m.group("ep2"):
        tag += f"-e{int(m.group('ep2')):02d}"
    edition = m.group("edition") or ""
    return f"{m.group('show')} ({m.group('year')}){edition} - {tag} - {name}"


def sub_sibling_names(dirpath, old_stem, new_base):
    out = []
    try:
        entries = os.listdir(dirpath)
    except OSError:
        return out
    for fn in entries:
        stem, ext = os.path.splitext(fn)
        if ext.lower() not in SUB_EXTS:
            continue
        lang = ""
        m = SUB_LANG_RE.search(stem)
        if m:
            lang = m.group(0)
            stem = stem[:m.start()]
        if stem == old_stem:
            out.append((os.path.join(dirpath, fn), os.path.join(dirpath, new_base + lang + ext)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--multi-ep-first", action="store_true")
    ap.add_argument("--threshold", type=float, default=0.75)
    ap.add_argument("--timeout", type=int, default=15)
    args = ap.parse_args()

    global TIMEOUT
    TIMEOUT = args.timeout
    root = os.path.abspath(args.root)

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
            if not m:
                continue
            if m.group("title"):
                already_titled += 1
                continue
            key = (m.group("show"), int(m.group("year")), m.group("edition") or "")
            jobs.setdefault(key, []).append((os.path.join(dp, fn), m))

    if not jobs:
        print("no Jellyfin-formatted files missing episode titles found")
        return

    plans = []
    stats = {"no_show": 0, "no_episode": 0, "multi_skip": 0, "conflict": 0}
    seen_shows = {}

    for (show, year, edition), items in sorted(jobs.items()):
        cache_key = (show.lower(), year)
        if cache_key not in seen_shows:
            print(f"\nresolving: {show} ({year})")
            tv = resolve_show(show, year, args.threshold)
            eps = {}
            if tv is None:
                print(f"  ?? no reliable TVMaze match — {len(items)} file(s) skipped")
            else:
                eps = fetch_episodes(tv)
                print(f"  matched -> {tv['name']} ({str(tv.get('premiered'))[:4]})")
            seen_shows[cache_key] = (tv, eps)
        tv, eps = seen_shows[cache_key]

        if tv is None:
            stats["no_show"] += len(items)
            continue

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
            base = new_stem(m, name)
            dst = os.path.join(os.path.dirname(path), base + os.path.splitext(path)[1])
            plans.append((path, dst))
            for ssub, dsub in sub_sibling_names(os.path.dirname(path),
                                                os.path.basename(os.path.splitext(path)[0]), base):
                plans.append((ssub, dsub))

    print("-" * 70)
    done = skipped = 0
    for src, dst in plans:
        if os.path.abspath(src) == os.path.abspath(dst):
            continue
        if os.path.exists(dst):
            stats["conflict"] += 1
            print(f"  !! target exists, skipping: {os.path.relpath(dst, root)}")
            continue
        print(f"{os.path.relpath(src, root)}\n   -> {os.path.relpath(dst, root)}")
        if args.apply:
            os.rename(src, dst)
        done += 1
        skipped += 0
    skipped += stats["multi_skip"]

    print("-" * 70)
    print(f"{'renamed' if args.apply else 'planned'}: {done}   already titled: "
          f"{already_titled}   skipped: {skipped}   "
          f"no show match: {stats['no_show']}   no episode: {stats['no_episode']}   "
          f"conflicts: {stats['conflict']}")
    if not args.apply:
        print("DRY RUN — re-run with --apply to execute")


if __name__ == "__main__":
    main()
