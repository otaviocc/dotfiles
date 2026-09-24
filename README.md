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
nvim     Neovim (single-file config on vim.pack)
tmux     tmux
ghostty  Ghostty terminal
sublime  Sublime Text (Default+ scheme, LSP-SourceKit)
lazygit  lazygit
tig      tig
yazi     yazi
herdr    herdr
opencode OpenCode
hunk     hunk
vigia    vigia
bat      bat
claude   Claude Code theme + statusline + shared agent skills
holodeck holodeck
vademecum vademecum
rewind   rewind (Claude Code history browser)
lyrics   lyrics-sidecar (lyrics fetcher + tui)
xcode    Xcode colour theme (macOS only)
```

Everything is themed **Default+**, a dark colourscheme that began as an Xcode
Font & Color Theme. Its canonical palette is documented in
[`docs/palette.md`](docs/palette.md); the upstream every port is generated or
copied from is `~/Developer/default-plus`.

Default+ does not follow the usual terminal convention: **comments are green
and strings are red**, which is Xcode's own role assignment and the thing that
distinguishes it from Apple's stock dark theme. That is deliberate.

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
  exists (e.g. `git` + `git-macos`, `sublime` + `sublime-macos`).

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
4. Claude Code's `~/.claude/settings.json` is not tracked (it holds API
   tokens). Set `"theme": "custom:default-plus"` and wire the statusline:

   ```json
   "statusLine": { "type": "command", "command": "~/.claude/statusline.py" }
   ```
