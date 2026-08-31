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
zsh/.config/zsh/...                                        lazygit/.config/lazygit/...
                                                            tig/.config/tig/...
                                                            herdr/.config/herdr/...
                                                            opencode/.config/opencode/...
                                                            hunk/.config/hunk/...
                                                            bat/.config/bat/...
                                                            claude/.claude/themes/...
                                                            holodeck/.config/holodeck/...
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

## The Kanagawa Dragon theme

[Kanagawa](https://github.com/rebelot/kanagawa.nvim) is the canonical source
for this color theme; the variant is **Dragon**, the darkest and warmest of its
three. Its background is `#181616` — R24 G22 B22, warm-neutral rather than
blue-tinted — and every accent is deliberately low-chroma, which is the whole
point of it. **[`docs/palette.md`](docs/palette.md) is the single source of
truth**, including the upstream name of every color.

**The accent is `yellow` (`dragonYellow`, `#c4b28a`).** Kanagawa declares no
single accent the way Catppuccin parameterizes one, so that is a choice made
here: it is the closest thing in the palette to the warm sandy `#FFC799` the
old Vesper setup used.

| Tool | How it's applied |
|---|---|
| Ghostty | built-in — `theme = "Kanagawa Dragon"` in `config.ghostty` |
| Neovim | the `kanagawa.nvim` plugin, declared in `lua/plugins/colorscheme.lua` — LazyVim does **not** bundle it, unlike tokyonight/catppuccin |
| herdr | built-in — `name = "kanagawa"` in `config.toml` (**Wave**, not Dragon — see below) |
| opencode | built-in — `theme: "kanagawa"` in `tui.json` (**Wave**, not Dragon — see below) |
| bat | vendored as `bat/.config/bat/themes/kanagawa-dragon.tmTheme`; run `bat cache --build` once after stowing |
| lazygit | `gui.theme` in `config.yml`, hand-ported — upstream ships no lazygit extra |
| zsh (`LS_COLORS`) | vendored as `zsh/.config/zsh/ls_colors.zsh`, remapped from vivid's `gruvbox-dark` — vivid has no Kanagawa |
| zsh (prompt, `LSCOLORS`) | merged into `zsh/.zshrc` |
| vigia | vendored as `vigia/.config/vigia/theme` |
| tmux, tig, hunk | merged directly into their config files |
| Claude Code | vendored as `claude/.claude/themes/kanagawa-dragon.json` |
| holodeck | built-in — `"theme": "kanagawa-dragon"` in `config.json` (added to holodeck in 5c12fe6) |

Kanagawa is less thoroughly ported than the previous two themes, so more here is
hand-assembled — but almost none of it is *invented*: the diff row backgrounds
are upstream's own `diff` table, the muted signs its `vcs` table, and every
syntax slot its `syn` table. Only the word-level and gutter diff steps are
extrapolated.

Four things that will bite:

- **herdr and opencode ship only the Wave variant.** Wave's background is
  `#1F1F28`, noticeably purple next to Dragon's warm `#181616`, so those two
  panes read cooler than everything around them. Fixing it needs a
  `[theme.custom]` block in herdr's config and a custom theme file for
  opencode; neither is done here.
- **bat needs the vendored theme and `bat cache --build`.** Upstream's
  `extras/tmTheme` only ships **Wave**, so the vendored file is that Wave
  tmTheme with every color swapped to its Dragon counterpart, paired by the role
  each fills in `themes.lua`. Also remember `--theme` takes the *filename*
  (`kanagawa-dragon`), not the plist's `name` key, and a wrong value silently
  falls back to bat's Monokai default.
- **tmux hex must stay lowercase.** `#F`, `#I`, `#W`, `#S`, `#T`, `#P`, `#H` and
  `#D` are legacy format specifiers, so `bg=#C4B28A` silently expands to the
  nonsense `bg=*4B28A`.
- **tig's 256-color values are hand-picked, not nearest-RGB.** Dragon is so
  low-chroma that a nearest-neighbour search drops half the palette onto the
  xterm greyscale ramp and collapses three syntax roles into one index. The
  values in `tig/config` trade exactness for staying distinguishable; the
  truecolor tools are the reference.

## Things intentionally not in this repo

- Secrets: `~/.ssh`, `~/.gnupg`, `~/.config/gh` (has tokens), `~/.putty`.
- `oh-my-zsh` — removed; `zsh/.zshrc` is a small plain config.
- herdr's log files, `session.json`, `release-notes.json`,
  `.plugins.lock` — runtime state, not config; only `config.toml` is
  tracked.
- `~/.claude/settings.json` — it selects the Claude Code theme, but also
  carries API tokens; `.gitignore` blocks everything under
  `claude/.claude/` except `themes/`. Same for the rest of `~/.claude`
  (history, projects, todos), which is session state.
- holodeck's `url-history.json` — runtime state; only `config.json` is
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

`zsh tmux ghostty neovim lazygit tig bat stow xclip wl-clipboard`

### macOS packages used by this config (Homebrew)

`zsh tmux ghostty neovim lazygit tig bat stow`
