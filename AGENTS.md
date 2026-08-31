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
  `lua/plugins/colorscheme.lua`, which points LazyVim's `colorscheme` option at
  `catppuccin-mocha`. LazyVim already ships the `catppuccin` plugin, so nothing
  is vendored here and there is no `colors/` directory. Personal settings go in
  `lua/config/{options,keymaps,autocmds}.lua`; extra plugins in `lua/plugins/`.
  `lazy-lock.json` is tracked; commit it after plugin updates.
- **bat** — "Catppuccin Mocha" is built into bat >= 0.25, so `config` is the
  whole package: no vendored `.tmTheme`, no `themes/` directory, and no
  `bat cache --build` step. (That step *was* needed under Vesper, which bat
  does not ship — don't reintroduce it from muscle memory.) Only add a
  `themes/` dir back if a machine ends up on bat < 0.25.
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

## Catppuccin Mocha theme

**`docs/palette.md` is the source of truth for every color in this repo.** Read
it before touching any color anywhere.

Ghostty, herdr, opencode, Neovim, bat and holodeck select Catppuccin **by
name** from a built-in or bundled theme; every other tool has the palette **vendored** into
its package so a fresh `./install.sh` never reaches out to another repo. Two of
One of those vendored copies comes from an official port and should be
re-synced from upstream rather than hand-edited (lazygit, from
`catppuccin/lazygit`); the rest — tmux, zsh, tig, hunk, vigia — are hand-ported
because no usable port exists for them.

Never hand-edit one tool's colors in isolation: change `docs/palette.md` first,
then propagate. Two traps worth knowing:

- **tmux hex must stay lowercase.** `#F`, `#I`, `#W`, `#S`, `#T`, `#P`, `#H` and
  `#D` are legacy format specifiers, so `bg=#CBA6F7` silently expands to the
  nonsense `bg=*BA6F7` instead of erroring.
- **tig has no truecolor.** Its config is a 256-color approximation, and its
  backgrounds are deliberately `default` so it inherits the terminal's real
  `#1e1e2e` rather than the grey `color235` the 256-color palette would force.
- **zsh has two `ls` variables.** `LS_COLORS` (GNU, truecolor, ~677 rules) is
  vendored in `zsh/.config/zsh/ls_colors.zsh` and regenerated with
  `vivid generate catppuccin-mocha` — don't hand-edit it. `LSCOLORS` is the
  8-colour BSD form that only `/bin/ls` reads; macOS aliases `ls` to `gls` so
  the truecolor set is what actually renders on both machines.
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
