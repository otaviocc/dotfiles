# dotfiles

Personal configuration files, managed with [GNU Stow](https://www.gnu.org/software/stow/),
shared between a Fedora Linux machine and macOS machines.

Single repo, same setup on every machine — Stow symlinks each tool's config
into place under `$HOME`.

## What's inside

One directory per tool ("package" in Stow terminology), kept under version
control:

```
zsh      shell prompt, aliases, LS_COLORS
git      global git config
nvim     Neovim (LazyVim)
tmux     tmux
ghostty  Ghostty terminal
lazygit  lazygit
tig      tig
herdr    herdr
opencode OpenCode
hunk     hunk
vigia    vigia
bat      bat
claude   Claude Code themes
holodeck holodeck
```

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
  exists (e.g. `git` + `git-macos`).

Editing a file that is already linked takes effect immediately. Re-run
`./install.sh <package>` after adding a new file to a package so the new
symlink gets created.

## Per-machine overrides

Anything private or specific to a single machine (work email, an SSH-signing
key path, a `PATH` entry, ...) does **not** go in this repo. Create these by
hand on whichever machine needs them — both are optional and silently ignored
if absent:

| File | Sourced by | Typical contents |
|---|---|---|
| `~/.zshrc.local` | `zsh/.zshrc`, always last | one-off env vars, aliases, PATH entries |
| `~/.gitconfig.local.machine` | `git/.gitconfig` | `user.email`, `gpg.ssh.program`, issue-tracker templates |

## Adding a new machine

1. Install your dependencies: `zsh tmux ghostty neovim lazygit tig bat stow`

   - **Fedora** also needs `xclip wl-clipboard`
   - **macOS (Homebrew)** uses the same list as above
2. `git clone ... ~/.dotfiles && cd ~/.dotfiles && ./install.sh`
3. Create `~/.zshrc.local` and/or `~/.gitconfig.local.machine` as needed
   (see "Per-machine overrides").
