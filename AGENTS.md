# AGENTS.md

Personal dotfiles managed with **GNU Stow**, shared between a Fedora Linux box
and macOS machines. There is no build, no test suite, no linter, and no CI —
"verification" means re-stowing and reloading the affected tool.

Read `README.md` for the full rationale. This file only covers what an agent
would get wrong.

## Layout

One directory per tool = one Stow package. The path *inside* the package mirrors
where the file lands under `$HOME` (`zsh/.zshrc` → `~/.zshrc`,
`nvim/.config/nvim/init.lua` → `~/.config/nvim/init.lua`).

Packages: `zsh git nvim tmux ghostty lazygit tig herdr opencode hunk vigia bat`,
plus the
OS-overlay packages `git-macos`/`git-linux` and `ghostty-macos`/`ghostty-linux`.

## Commands

```bash
./install.sh                # stow every package in ALL_PACKAGES
./install.sh zsh git nvim   # stow a subset
```

- Editing a file that is **already** stowed takes effect immediately (it's a
  symlink into this repo). No re-stow needed.
- **Adding a new file** to an existing package requires `./install.sh <pkg>` to
  create the new symlink.
- A new package must be appended to `ALL_PACKAGES` in `install.sh:34`, or
  a bare `./install.sh` will silently skip it. Overlay packages are the
  exception: they are derived as `${package}-${OS_SUFFIX}` (`install.sh:95`) and
  must **not** be listed.
- Never create symlinks with `ln`. Stow owns every symlink in `$HOME`, including
  the `*.local` OS-selection ones.
- `install.sh` **moves** any real (non-symlink) file that collides into
  `~/.dotfiles-backup-<timestamp>`. It does this before stowing, so running it
  on a machine with hand-written configs relocates them out of `$HOME`.

## The two OS-difference mechanisms

Pick the right one; they are not interchangeable.

1. **Runtime branching** (`zsh`, `tmux`) — the shared file inspects `uname` and
   sources a tracked sibling: `zsh/.zshrc` → `~/.zshrc.{macos,linux}`
   (`zsh/.zshrc:257`); `tmux.conf` → `tmux.{macos,linux}.conf` via `if-shell`.
   Nothing extra to install.
2. **Overlay symlink packages** (`git`, `ghostty`) — these formats can't branch
   on `uname`, so the main config unconditionally includes a `*.local` file, and
   a tiny overlay package ships a **pre-committed relative symlink** pointing at
   the right OS variant (e.g. `git-macos/.gitconfig.local -> ../git/.gitconfig.macos`).

If you add a third overlay, note that `.gitignore` ignores `*.local` globally —
you must add an explicit `!` negation for the new symlink or git will not track
it. See the four existing exceptions in `.gitignore`.

## Local machine overrides (untracked, never commit)

| File | Sourced by |
|---|---|
| `~/.zshrc.local` | `zsh/.zshrc`, always last |
| `~/.gitconfig.local.machine` | `git/.gitconfig.{macos,linux}` |

Do not confuse `~/.gitconfig.local.machine` (hand-made, untracked) with
`~/.gitconfig.local` (the stow-managed OS-selection symlink).

## Per-tool gotchas

- **ghostty** — the shared config is `config.ghostty`, *not* `config`. This is
  deliberate for the Ghostty version in use; see the header comment in
  `ghostty/.config/ghostty/config.ghostty`. Do not "fix" the filename. It ends
  with `config-file = ?config.local`; the `?` keeps Ghostty from erroring before
  `install.sh` has run.
- **nvim** — the stock [LazyVim](https://www.lazyvim.org) starter template,
  kept verbatim so upgrades are a re-diff against
  <https://github.com/LazyVim/starter>. The only intentional deviation is
  `lua/plugins/colorscheme.lua`, which declares `rebelot/kanagawa.nvim` and
  points LazyVim's `colorscheme` option at `kanagawa-dragon`. LazyVim does not
  bundle kanagawa (it does bundle tokyonight and catppuccin), so the plugin
  spec is required; there is no vendored `colors/` directory. Personal settings go in
  `lua/config/{options,keymaps,autocmds}.lua`; extra plugins in `lua/plugins/`.
  `lazy-lock.json` is tracked; commit it after plugin updates.
- **bat** — Kanagawa is not built into bat, so the theme is vendored as
  `themes/kanagawa-dragon.tmTheme` and bat only picks it up from a compiled
  cache: run `bat cache --build` after stowing or after editing it. See the
  theme trap in the Kanagawa Dragon section about the `--theme` value.
- **herdr** — only `config.toml` is tracked. Logs, `session.json`,
  `release-notes.json` and `.plugins.lock` are runtime state; leave them out.
- **holodeck** — only `config.json` is tracked. `url-history.json` next to it
  is runtime state; leave it out. The file is strict JSON (serde_json), so it
  takes no comments — document choices here or in the README, not inline.
- **opencode** — `~/.config/opencode/skills/` contains skills this repo does not
  track (Supacode's own, and symlinks into `~/.agents/skills/`). Don't assume
  everything there is version-controlled. Skill-specific rules live in
  `opencode/.config/opencode/skills/AGENTS.md` — read it before touching any
  skill script.

## Kanagawa Dragon theme

**`docs/palette.md` is the source of truth for every color in this repo.**
Variant is **Dragon**, accent is **yellow** `#c4b28a`.

Almost nothing here is invented: diff row backgrounds come from Kanagawa's own
`diff` table, muted diff signs from its `vcs` table, and every syntax slot from
its `syn` table (keyword=violet, operator/preproc=red, type=aqua, fun=blue,
identifier=yellow, constant=orange, number=pink, string=green). Dragon sets
`syn.variable = "none"`, so variables inherit the plain foreground. Only the
word-level and gutter diff steps are extrapolated, by mixing the matching `vcs`
colour into `bg`.

Traps worth knowing:

- **herdr is not truly on Dragon.** Its built-in `kanagawa` is the **Wave**
  variant (purple `#1F1F28` background). Don't "fix" the other tools to match
  it — it is the one that is off. Everything else is on real Dragon.
- **opencode uses a vendored theme, not its built-in.** opencode's own
  `kanagawa` is Wave (its bundled defs are `sumiInk*`/`fujiWhite`), so a Dragon
  theme is vendored at `opencode/.config/opencode/themes/kanagawa-dragon.json`.
  opencode loads global themes from `<config>/themes/<name>.json`; the file's
  50 theme keys mirror its built-in kanagawa exactly, and every value is a
  reference into `defs`.
- **nvim needs a plugin spec.** LazyVim bundles tokyonight and catppuccin but
  not kanagawa, so `lua/plugins/colorscheme.lua` declares
  `rebelot/kanagawa.nvim` with `lazy = false` and `priority = 1000`. Commit
  `lazy-lock.json` after any plugin change.
- **bat's `--theme` is the .tmTheme *filename*** (`kanagawa-dragon`), not the
  plist's `name` key. A wrong value is silent — bat prints its Monokai default
  rather than erroring. The vendored file is upstream's *Wave* tmTheme remapped
  to Dragon, because upstream ships no Dragon tmTheme.
- **tmux hex must stay lowercase.** `#F`/`#I`/`#W`/`#S`/`#T`/`#P`/`#H`/`#D` are
  legacy format specifiers.
- **tig's 256-colour values are hand-picked, not computed.** Nearest-RGB sends
  Dragon's low-chroma palette onto the greyscale ramp. Don't "correct" them.
- **`LS_COLORS` is not from `vivid generate <name>`** — vivid has no Kanagawa.
  It is vivid's `gruvbox-dark` output with the palette remapped role-by-role;
  see the header of `zsh/.config/zsh/ls_colors.zsh`.
- **The `claude` package tracks `~/.claude/themes/` only.** `settings.json`
  selects the theme but also holds API tokens — never add it to the repo.

## Commit messages

Follow the seven rules (cbea.ms/git-commit); nothing enforces this.

- Subject: imperative mood ("Add", "Fix" — not "Added"/"Adds"), capitalized,
  ≤50 chars, no trailing period.
- Blank line after the subject; wrap the body at 72 chars.
- Body explains what and why, not how. A cohesive change gets prose; a commit
  grouping several distinct changes gets `-` bullets.
- Prefix the subject with the package when it's package-scoped, matching
  existing history: `zsh: ...`, `nvim: ...`, `skills: ...`.
