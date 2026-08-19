# dotfiles

Personal configuration files, managed with [GNU Stow](https://www.gnu.org/software/stow/),
shared between a Fedora Linux machine and macOS machines.

## Layout

One directory per tool ("package" in Stow terminology). Each mirrors the
path it should end up at under `$HOME`:

```
zsh/.zshrc                   git/.gitconfig                nvim/.config/nvim/...
zsh/.zshrc.linux             git/.gitconfig.linux          tmux/.config/tmux/...
zsh/.zshrc.macos             git/.gitconfig.macos          ghostty/.config/ghostty/...
                                                            lazygit/.config/lazygit/...
                                                            tig/.config/tig/...
                                                            herdr/.config/herdr/...
                                                            opencode/.config/opencode/...
                                                            hunk/.config/hunk/...
```

## Handling Fedora vs macOS differences

Most config is identical on both machines. Where it isn't:

- **zsh, tmux** — the shared file branches at *runtime* using
  `uname`/`if-shell`, and sources a tracked `*.linux` / `*.macos` sibling
  file. Zero setup required.
- **git, Ghostty** — these config formats can't branch on their own, so
  both OS variants are tracked (`git/.gitconfig.linux` / `.gitconfig.macos`,
  `ghostty/.config/ghostty/config.linux` / `.macos`). A tiny OS-specific
  overlay package (`git-macos`/`git-linux`, `ghostty-macos`/`ghostty-linux`)
  carries a pre-committed relative symlink — e.g.
  `git-macos/.gitconfig.local -> ../git/.gitconfig.macos` — for the
  `.gitconfig.local` / `config.local` name each main config already
  includes unconditionally. `install.sh` stows whichever overlay matches
  `uname`; you never create or edit these symlinks by hand.

## Local machine overrides (untracked)

Anything private or specific to a single machine (work email, an
SSH-signing key path, an extra `PATH` entry, ...) does **not** go in this
repo. Instead, create these files by hand on whichever machine needs them
— both are optional and silently ignored by their parent config if absent:

| File | Sourced by | Typical contents |
|---|---|---|
| `~/.zshrc.local` | `zsh/.zshrc`, always last | one-off env vars, aliases, PATH entries |
| `~/.gitconfig.local.machine` | `git/.gitconfig.macos` / `.linux` | `user.email`, `gpg.ssh.program`, issue-tracker templates |

Don't confuse `~/.gitconfig.local.machine` with `~/.gitconfig.local` —
the latter is the OS-selection symlink described above and is managed by
Stow, not created by hand.

## The Vesper theme

[Vesper](https://github.com/raunofreiberg/vesper) is the canonical source
for this color theme. Ghostty and herdr ship it as a built-in theme, so
those two packages just select it by name; every other tool vendors the
same palette directly into its own config, so a fresh `./install.sh` run
never has to reach out to another repo:

| Tool | How it's applied |
|---|---|
| Ghostty | built-in — `theme = "Vesper"` in `config.ghostty` |
| herdr | built-in — `name = "vesper"` in `config.toml` |
| opencode | built-in — `theme: "vesper"` in `tui.json` |
| Neovim | vendored as `nvim/.config/nvim/colors/vesper.lua` |
| zsh (prompt/colors/`LS_COLORS`) | merged into `zsh/.zshrc` |
| vigia | vendored as `vigia/.config/vigia/theme` |
| lazygit, tig, hunk | merged directly into their config files (no separate theme file needed) |

If the palette changes upstream in Vesper, re-copy the affected file(s)
into the matching package here and commit.

## Things intentionally not in this repo

- Secrets: `~/.ssh`, `~/.gnupg`, `~/.config/gh` (has tokens), `~/.putty`.
- `oh-my-zsh` — removed; `zsh/.zshrc` is a small plain config.
- herdr's log files, `session.json`, `release-notes.json`,
  `.plugins.lock` — runtime state, not config; only `config.toml` is
  tracked.
- Third-party OpenCode skills/plugins (e.g. `AvdLee/*-Agent-Skill`) —
  install/manage those separately on whichever machine needs them.
  `opencode/.config/opencode/skills/` only tracks skills genuinely
  authored here with no other repo backing them.

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
- stow each requested package, plus its OS-specific overlay package if one
  exists (e.g. `git` + `git-macos`). Every symlink in `$HOME`, including
  the local-include ones, is created by `stow` itself — `install.sh`
  never calls `ln`.

Re-run `./install.sh <package>` any time after editing a file in the repo
that isn't already a symlink target (new files need re-stowing).

## Adding a new machine

1. Install the packages you rely on (see below).
2. `git clone ... ~/.dotfiles && cd ~/.dotfiles && ./install.sh`
3. Create `~/.zshrc.local` and/or `~/.gitconfig.local.machine` if this
   machine needs anything from "Local machine overrides" above.

### Fedora packages used by this config

`zsh tmux ghostty neovim lazygit tig stow xclip wl-clipboard`

### macOS packages used by this config (Homebrew)

`zsh tmux ghostty neovim lazygit tig stow`
