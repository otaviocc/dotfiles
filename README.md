# dotfiles

Personal configuration files, managed with [GNU Stow](https://www.gnu.org/software/stow/),
shared between a Fedora Linux machine and macOS machines.

## Layout

One directory per tool ("package" in Stow terminology). Each mirrors the
path it should end up at under `$HOME`:

```
zsh/.zshrc                       git/.gitconfig                  nvim/.config/nvim/...
zsh/.zshrc.linux                 git/.gitconfig.linux             tmux/.config/tmux/...
zsh/.zshrc.macos                 git/.gitconfig.macos             ghostty/.config/ghostty/...
zsh/.zsh_default-plus.zsh                                          lazygit/.config/lazygit/...
                                                                    tig/.config/tig/...
                                                                    herdr/.config/herdr/...
                                                                    opencode/.config/opencode/...
                                                                    vscode/.config/Code/User/...
```

### Handling Fedora vs macOS differences

Most config is identical on both machines. Where it isn't, each package
takes whichever approach fits the tool best, so nothing has to be edited
by hand after cloning:

- **zsh, tmux** — the shared file branches at *runtime* using
  `uname`/`if-shell`, and sources a tracked `*.linux` / `*.macos` sibling
  file. Zero setup required.
- **git, Ghostty** — these config formats can't branch on their own, so
  both OS variants are tracked (`git/.gitconfig.linux` /
  `.gitconfig.macos`, `ghostty/.config/ghostty/config.linux` / `.macos`)
  and `install.sh` symlinks the right one to `~/.gitconfig.local` /
  `~/.config/ghostty/config.local` — a name each main config already
  includes unconditionally.
- **VS Code** — the settings path is completely different on macOS
  (`~/Library/Application Support/Code/User/`) vs Linux
  (`~/.config/Code/User/`). `install.sh` handles this as a special case
  outside of Stow.

### The Default+ theme

[`default-plus`](https://github.com/otaviocc/default-plus) is the
canonical source for this color theme (it also covers Xcode and other
non-dotfile contexts, so it stays its own repo). The bits each tool here
needs are **vendored directly** into the relevant package, so a fresh
`./install.sh` run never has to reach out to another repo:

| Tool | Vendored as |
|---|---|
| Ghostty | `ghostty/.config/ghostty/themes/Default+` |
| Neovim | `nvim/.config/nvim/colors/default-plus.lua` |
| zsh (prompt/colors/`LS_COLORS`) | `zsh/.zsh_default-plus.zsh` |
| opencode | `opencode/.config/opencode/themes/default-plus.json` |
| lazygit, tig, herdr | merged directly into their config files (no separate theme file needed) |

If the palette changes upstream in `default-plus`, re-copy the affected
file(s) from that repo into the matching package here and commit.

### Things intentionally *not* in this repo

- Secrets: `~/.ssh`, `~/.gnupg`, `~/.config/gh` (has tokens), `~/.putty`.
- Anything from the old `~/Developer/dot.config` repo that isn't listed
  above (fish config, lsd, starship) — dropped since we standardized on
  zsh; revive them here as their own package if you go back to fish.
- `oh-my-zsh` itself — the framework is gone; `zsh/.zshrc` is a small
  plain config now.
- herdr's log files, `session.json`, `release-notes.json`,
  `.plugins.lock` — runtime state, not config; only `config.toml` is
  tracked.

### OpenCode skills

`opencode/.config/opencode/skills/` tracks the skills that are genuinely
mine and have no other repo backing them: `brrr`, `stash-cli`,
`flac-to-alac` (its `scripts/` are tracked; the local `.venv/` it creates
at runtime is not).

Four other skills — `swift-concurrency`, `swift-testing-expert`,
`swiftui-expert-skill`, `xcode-disk-cleanup` — are **not** vendored here.
They're third-party (`AvdLee/*-Agent-Skill` on GitHub), installed and kept
up to date via Claude Code's plugin/marketplace system into
`~/.agents/skills/<name>`. `install.sh` re-creates the symlink from
`~/.config/opencode/skills/<name>` to `~/.agents/skills/<name>` on any
package install that includes `opencode`, but only if the plugin is
already installed — install the Claude Code plugins first on a new
machine, then run `./install.sh opencode` (or just re-run it) to pick
them up.

Media-management skills (`immich-upload`, `rename-movies`, `rename-tv`,
`tidy-kids-shows`) live in the still-unfinished `otaviocc/hometools` repo
and aren't tracked here yet.

## Usage

```bash
git clone git@github.com:<you>/dotfiles.git ~/.dotfiles
cd ~/.dotfiles
./install.sh                # stow everything
./install.sh zsh git nvim   # or just a subset
```

`install.sh` will:
- install `stow` if it's missing (`dnf` / `brew`),
- back up any real (non-symlink) files it would otherwise overwrite to
  `~/.dotfiles-backup-<timestamp>` before linking,
- wire up the git/Ghostty local-include symlinks,
- special-case VS Code on macOS.

Re-run `./install.sh <package>` any time after editing a file in the repo
that isn't already a symlink target (new files need re-stowing).

## Adding a new machine

1. Install Fedora/macOS packages you rely on (see below).
2. `git clone ... ~/.dotfiles && cd ~/.dotfiles && ./install.sh`
3. Anything truly one-off for that machine (work email override, extra
   PATH entry, etc.) goes in `~/.zshrc.local` — untracked, sourced last.

### Fedora packages used by this config

`zsh tmux ghostty neovim lazygit tig stow xclip wl-clipboard`

### macOS packages used by this config (Homebrew)

`zsh tmux ghostty neovim lazygit tig stow`

## Migration notes (2026-07-31)

- This repo replaces `otaviocc/dot.config` (macOS/fish-focused). Its
  `ghostty`, `git`, `nvim`, and `tmux` content has been folded in here,
  reconciled with the already-adapted Fedora versions. Once this repo is
  pushed and verified on both machines, archive or delete
  `otaviocc/dot.config` on GitHub and remove the local
  `~/Developer/dot.config` checkout.
- `otaviocc/hometools` (OpenCode skills/scripts) stays a separate repo —
  not dotfiles.
- `~/.config/git/` (the old XDG-style git config) is redundant now that
  `~/.gitconfig` exists and takes precedence — safe to delete after
  `install.sh` runs.
