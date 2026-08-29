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
  `vesper`, served by the vendored `colors/vesper.lua` — the single source of
  the palette in this package. Personal settings go in
  `lua/config/{options,keymaps,autocmds}.lua`; extra plugins in `lua/plugins/`.
  `lazy-lock.json` is tracked; commit it after plugin updates.
- **bat** — the Vesper theme is a Sublime `.tmTheme`
  (`bat/.config/bat/themes/Vesper.tmTheme`) that bat only picks up from a
  compiled cache. After stowing the package, or after editing the theme, run
  `bat cache --build`; without it `--theme="Vesper"` in
  `bat/.config/bat/config` fails with "unknown theme".
- **herdr** — only `config.toml` is tracked. Logs, `session.json`,
  `release-notes.json` and `.plugins.lock` are runtime state; leave them out.
- **opencode** — `~/.config/opencode/skills/` contains skills this repo does not
  track (Supacode's own, and symlinks into `~/.agents/skills/`). Don't assume
  everything there is version-controlled. Skill-specific rules live in
  `opencode/.config/opencode/skills/AGENTS.md` — read it before touching any
  skill script.

## Vesper theme

Upstream is <https://github.com/raunofreiberg/vesper>. Ghostty and herdr use
its **built-in** theme by name; every other tool has the palette **vendored**
into its package so a fresh `./install.sh` never reaches out to another repo.
If the palette changes upstream, re-copy the affected files; don't hand-edit
one tool's colors in isolation (README has the full table).

## Commit messages

Follow the seven rules (cbea.ms/git-commit); nothing enforces this.

- Subject: imperative mood ("Add", "Fix" — not "Added"/"Adds"), capitalized,
  ≤50 chars, no trailing period.
- Blank line after the subject; wrap the body at 72 chars.
- Body explains what and why, not how. A cohesive change gets prose; a commit
  grouping several distinct changes gets `-` bullets.
- Prefix the subject with the package when it's package-scoped, matching
  existing history: `zsh: ...`, `nvim: ...`, `skills: ...`.
