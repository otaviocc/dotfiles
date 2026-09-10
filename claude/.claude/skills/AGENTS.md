# AGENTS.md

Personal agent skills, shared between Claude Code and opencode. Each skill is a
folder here bundling a `SKILL.md` (instructions) with a self-contained Python
script. Most scripts use **only the stdlib** — no pip install needed. Exceptions
are noted below.

## Skills in this repo

| Skill | Script | Purpose |
|-------|--------|---------|
| `organize-movies` | `organize-movies/scripts/organize-movies.py` | Organize movie files into Jellyfin `Movies/Title (year)/` layout |
| `organize-tv` | `organize-tv/scripts/organize-tv.py` | Organize TV episodes into Jellyfin `TV Shows/Title (year)/Season NN/` layout |
| `organize-kids-shows` | `organize-kids-shows/scripts/organize-kids-shows.py` | Same as organize-tv but tailored for kids shows (bare-number episodes, no editions) |
| `flac-to-alac` | `flac-to-alac/scripts/flac-to-alac.py` | Convert FLAC files to ALAC (.m4a) via ffmpeg (preserves artwork, verifies lossless) |
| `add-episode-titles` | `add-episode-titles/scripts/add-episode-titles.py` | Backfill episode titles into organized TV filenames via TVMaze |
| `brrr` | none (curl only) | Send a push notification to the user's devices via the Brrr API |
| `hunk` | none (shells out to the `hunk` binary) | Load Hunk's own review skill (`hunk skill path`) and use it for a code review |
| `code-snippet-image` | `code-snippet-image/scripts/generate_code_image.py` | Generate macOS-style code snippet images from Swift code (dark theme, warm palette, retina-ready PNG); requires Pillow + Pygments |
| `jellyfin-library-cards` | `jellyfin-library-cards/scripts/generate_card.py` | Generate Jellyfin library card artwork (Fredoka, purple-to-cyan gradient, transparent PNG); font bundled in `assets/`; requires Pillow |

These live in the `claude` package at `claude/.claude/skills/`, stowed to
`~/.claude/skills/`. Claude Code reads that directory natively. opencode does
**not**, despite its own bundled docs listing `~/.claude/skills` under "External
skills (auto-loaded)" — as of 1.18.29 nothing there is picked up, symlinked or
not. The `opencode` package registers the directory explicitly instead:

```jsonc
"skills": { "paths": ["~/.claude/skills"] }
```

A leading `~` is expanded; `$HOME` is not. Verify with `opencode debug skill`,
which prints every skill it can see and where each was loaded from.

## Skills NOT in this repo

Other skill directories on the macOS machine hold skills this repo does **not**
track, so they will not survive a bootstrap onto a new machine:

| Skill | Where it actually lives |
|-------|-------------------------|
| `stash-cli` | the Stash project itself (`CLI`'s own skill); deliberately untracked here so the docs never drift from the binary |
| `supacode-cli`, `supacode-deeplinks` | real directories, installed by Supacode itself |
| `swift-concurrency`, `swift-testing-expert`, `swiftui-expert-skill`, `xcode-disk-cleanup` | symlinks into `~/.agents/skills/`, installed as Claude Code plugins |

Everything tool-installed lands in `~/.claude/skills/` as a real directory
alongside this package's symlinks, which is why `~/.claude/skills/` is left as a
real directory rather than folded into a single stow symlink.

## Conventions

- All rename/organize scripts default to **dry-run**. Pass `--apply` to actually move files.
- They accept `--root PATH` (default: current directory).
- Every script is **self-contained**: no shared module, so a single skill folder
  can be copied to a media library and run on its own. The price is that
  `safe_component`, `execute_moves`, `prune_empty_dirs`, `smart_title`,
  `QUALITY_RE`, `NOISE_RE` (and, in the two Jellyfin video organizers,
  `EDITION_PATTERNS`) are duplicated across scripts.
  **When you fix one, check whether the same fix belongs in the siblings.**
- `execute_moves` is byte-identical across `organize-tv`, `organize-kids-shows`
  and `organize-movies` — keep it that way. `add-episode-titles` carries a
  superset: the same body plus a `dir_renames` parameter and a trailing
  directory-rename pass. `safe_component`'s body is identical across all four;
  only its docstring is tailored per skill.

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

# Add episode titles (requires network access to api.tvmaze.com)
python3 add-episode-titles/scripts/add-episode-titles.py --root /path/to/tv
python3 add-episode-titles/scripts/add-episode-titles.py --root /path/to/tv --apply
```

## Notes

- All three video organizers support `--sub-lang CODE`; all default to **no**
  language code, and all recognise a code the subtitle already carries (across
  the full `LANG_CODES` list) so it stays paired with its episode.
  `organize-movies` additionally carries that code into the new name when
  `--sub-lang` is not given; `organize-tv` and `organize-kids-shows` drop it.
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
