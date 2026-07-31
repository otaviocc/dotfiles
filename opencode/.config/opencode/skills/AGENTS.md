# AGENTS.md

Personal OpenCode skills. Each skill is a folder here bundling a `SKILL.md`
(instructions) with a self-contained Python script. Most scripts use
**only the stdlib** — no pip install needed. Exceptions are noted below.

## Skills

| Skill | Script | Purpose |
|-------|--------|---------|
| `organize-movies` | `organize-movies/scripts/organize-movies.py` | Organize movie files into Jellyfin `Movies/Title (year)/` layout |
| `organize-tv` | `organize-tv/scripts/organize-tv.py` | Organize TV episodes into Jellyfin `TV Shows/Title (year)/Season NN/` layout |
| `organize-kids-shows` | `organize-kids-shows/scripts/organize-kids-shows.py` | Same as organize-tv but tailored for kids shows (bare-number episodes, no editions) |
| `flac-to-alac` | `flac-to-alac/scripts/flac-to-alac.py` | Convert FLAC files to ALAC (.m4a) via ffmpeg (preserves artwork) |
| `organize-music` | `organize-music/scripts/organize-music.py` | Organize music files into Artist/Album/Track structure via audio tags |
| `add-episode-titles` | `add-episode-titles/scripts/add-episode-titles.py` | Backfill episode titles into organized TV filenames via TVMaze |
| `brrr` | see `brrr/SKILL.md` | |
| `stash-cli` | see `stash-cli/SKILL.md` | |

These are symlinked into `~/.config/opencode/skills/` by `install.sh`
(part of the `opencode` package) — nothing to set up by hand.

## Conventions

- All rename/organize scripts default to **dry-run**. Pass `--apply` to actually move files.
- They accept `--root PATH` (default: current directory).
- `organize-tv.py` uses module-level globals `MINIMAL` and `SUB_LANG` set from argparse — an oddity if you're reading the code.
- The rename scripts share near-identical parsing logic (`smart_title`, `QUALITY_RE`, `EDITION_PATTERNS`, `NOISE_RE`) that is duplicated, not factored into a common module.

## Commit messages

Follow the seven rules (cbea.ms/git-commit); nothing enforces this, it's discipline:

- Subject: imperative mood ("Add", "Fix", not "Added"/"Adds"), capitalized, ≤50 chars, no trailing period. Verified by `git log`.
- Blank line between subject and body; wrap the body at 72 chars.
- Body explains what and why, not how. A single cohesive change gets prose; a commit grouping several distinct changes gets - bullets.

## Running directly

```bash
# Rename scripts — always dry-run first
python3 organize-movies/scripts/organize-movies.py --root /path/to/movies
python3 organize-movies/scripts/organize-movies.py --root /path/to/movies --apply

python3 organize-tv/scripts/organize-tv.py --root /path/to/tv
python3 organize-tv/scripts/organize-tv.py --root /path/to/tv --apply

python3 organize-kids-shows/scripts/organize-kids-shows.py --root /path/to/kids
python3 organize-kids-shows/scripts/organize-kids-shows.py --root /path/to/kids --apply

# FLAC to ALAC (requires ffmpeg)
python3 flac-to-alac/scripts/flac-to-alac.py --root /path/to/music
python3 flac-to-alac/scripts/flac-to-alac.py --root /path/to/music --apply
python3 flac-to-alac/scripts/flac-to-alac.py --root /path/to/music --apply --keep-original

# Organize music (requires pip install mutagen)
python3 organize-music/scripts/organize-music.py --root /path/to/music
python3 organize-music/scripts/organize-music.py --root /path/to/music --apply

# Add episode titles (requires network access to api.tvmaze.com)
python3 add-episode-titles/scripts/add-episode-titles.py --root /path/to/tv
python3 add-episode-titles/scripts/add-episode-titles.py --root /path/to/tv --apply
```

## Notes

- `organize-movies` and `organize-kids-shows` support `--sub-lang CODE` for subtitle file renaming.
- `organize-tv` has `--minimal` to drop episode titles from filenames.
- `organize-kids-shows` has `--bare-number-episodes` for files named `Show 1`, `Show 2`, etc. (off by default to avoid treating movies as episodes).
- `add-episode-titles` queries `api.tvmaze.com` (no API key); requires network access. Runs after `organize-tv` to fill in episode titles.
- `flac-to-alac` requires `ffmpeg`. Uses `-c:v copy -map 0` to preserve embedded artwork.
- `organize-music` requires `mutagen` (`pip install mutagen`) for reading audio metadata tags.
