# AGENTS.md

Personal OpenCode skills. Each skill is a folder here bundling a `SKILL.md`
(instructions) with a self-contained Python script. Most scripts use
**only the stdlib** — no pip install needed. Exceptions are noted below.

## Skills in this repo

| Skill | Script | Purpose |
|-------|--------|---------|
| `organize-movies` | `organize-movies/scripts/organize-movies.py` | Organize movie files into Jellyfin `Movies/Title (year)/` layout |
| `organize-tv` | `organize-tv/scripts/organize-tv.py` | Organize TV episodes into Jellyfin `TV Shows/Title (year)/Season NN/` layout |
| `organize-kids-shows` | `organize-kids-shows/scripts/organize-kids-shows.py` | Same as organize-tv but tailored for kids shows (bare-number episodes, no editions) |
| `flac-to-alac` | `flac-to-alac/scripts/flac-to-alac.py` | Convert FLAC files to ALAC (.m4a) via ffmpeg (preserves artwork, verifies lossless) |
| `organize-music` | `organize-music/scripts/organize-music.py` | Organize music files into Artist/Album/Track structure via audio tags |
| `add-episode-titles` | `add-episode-titles/scripts/add-episode-titles.py` | Backfill episode titles into organized TV filenames via TVMaze |
| `brrr` | none (curl only) | Send a push notification to the user's devices via the Brrr API |
| `stash-cli` | none (drives the `stash` binary) | Save, search, tag, import/export bookmarks in the self-hosted Stash manager |
| `music-library-to-bear` | `music-library-to-bear/scripts/music-library-to-bear.py` | Scan a ripped CD library and create one Bear note per artist via bearcli |
| `music-library-to-obsidian` | `music-library-to-obsidian/scripts/music-library-to-obsidian.py` | Scan a ripped CD library and create one Obsidian note per album with frontmatter, embedded cover, and track list; writes Albums.base and Artists.base |
| `code-snippet-image` | `code-snippet-image/scripts/generate_code_image.py` | Generate macOS-style code snippet images from Swift code (dark theme, warm palette, retina-ready PNG); requires Pillow + Pygments |
| `jellyfin-library-cards` | `jellyfin-library-cards/scripts/generate_card.py` | Generate Jellyfin library card artwork (Fredoka, purple-to-cyan gradient, transparent PNG); font bundled in `assets/`; requires Pillow |

These are symlinked into `~/.config/opencode/skills/` by `install.sh`
(part of the `opencode` package) — nothing to set up by hand.

## Skills NOT in this repo

`~/.config/opencode/skills/` also contains skills that this repo does **not**
track, so they will not survive a bootstrap onto a new machine:

| Skill | Where it actually lives |
|-------|-------------------------|
| `supacode-cli`, `supacode-deeplinks` | real directories, installed by Supacode itself |
| `swift-concurrency`, `swift-testing-expert`, `swiftui-expert-skill`, `xcode-disk-cleanup` | symlinks into `~/.agents/skills/` |

If any of those should be version-controlled, move them into this directory and
let stow link them like the rest.

## Conventions

- All rename/organize scripts default to **dry-run**. Pass `--apply` to actually move files.
- They accept `--root PATH` (default: current directory).
- Every script is **self-contained**: no shared module, so a single skill folder
  can be copied to a media library and run on its own. The price is that
  `safe_component`, `execute_moves`, `prune_empty_dirs`, `smart_title`,
  `QUALITY_RE`, `EDITION_PATTERNS` and `NOISE_RE` are duplicated across scripts.
  **When you fix one, check whether the same fix belongs in the siblings.**
- `safe_component` and `execute_moves` are intentionally byte-identical across
  `organize-tv`, `organize-kids-shows`, `organize-movies`, `organize-music` and
  `add-episode-titles`. Keep them that way.

### Shared move semantics

`execute_moves` is the single place where anything touches the filesystem. It:

- filters no-op moves (source already at its destination);
- resolves a destination claimed by several sources in favour of the **largest
  file**, reporting the losers rather than silently picking by iteration order;
- refuses to overwrite an existing file, unless that file is itself scheduled to
  move away — in which case the move is deferred until the destination is free;
- allows case-only renames on case-insensitive filesystems (`os.path.samefile`);
- uses `shutil.move`, so a library spanning several mounts does not blow up with
  `EXDEV`;
- reports every problem **during the dry run**, before anything is moved.

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
python3 organize-music/scripts/organize-music.py --root /path/to/music --apply --albumartist

# Add episode titles (requires network access to api.tvmaze.com)
python3 add-episode-titles/scripts/add-episode-titles.py --root /path/to/tv
python3 add-episode-titles/scripts/add-episode-titles.py --root /path/to/tv --apply
```

## Notes

- All three video organizers support `--sub-lang CODE`; all default to **no**
  language code. `organize-movies` additionally preserves a language code the
  subtitle already carries when `--sub-lang` is not given.
- `organize-tv` has `--minimal` to drop episode titles from filenames.
- `organize-tv` and `organize-kids-shows` both have `--bare-number-episodes`,
  off by default so movies are not mistaken for episodes. Both resolve the
  season from a `Season NN` parent folder when the filename lacks `sNNeNN`.
- Video files with no detectable episode number become numbered Season 00
  specials keeping their original name, rather than all colliding on `s00e01`.
- `add-episode-titles` queries `api.tvmaze.com` (no API key); requires network
  access. Runs after `organize-tv` to fill in episode titles. Titles are
  sanitised before use — TVMaze returns things like `Part 1/2`.
- `flac-to-alac` requires `ffmpeg`. Uses `-c:v copy -map 0` to preserve embedded
  artwork, writes atomically via a temp file, and **only deletes a source FLAC
  after verifying the conversion is lossless**. `--no-verify` will not delete
  anything unless paired with `--force-delete`.
- `organize-music` requires `mutagen` (`pip install mutagen`) for reading audio
  metadata tags, and exits with an install hint rather than a traceback if it is
  missing.
