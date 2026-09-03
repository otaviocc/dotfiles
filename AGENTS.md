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
- **nvim** — a hand-written single-file config: everything lives in
  `init.lua`, on Neovim's built-in `vim.pack` manager. There is no distro and
  no plugin-manager bootstrap, so there is no upstream to re-diff against —
  edit `init.lua` directly. **Requires Neovim >= 0.12** for `vim.pack`,
  `vim.lsp.enable`, the `lsp/` directory and `vim.opt.winborder`; it will not
  start on 0.11. Only two things sit outside `init.lua`: `lsp/<server>.lua`,
  autoloaded by `vim.lsp.enable` to override nvim-lspconfig's defaults for
  that server, and `.luarc.json`, which is for `lua-language-server` (not
  Neovim) and only makes editing this config comfortable. Completion is
  Neovim's built-in `vim.lsp.completion`, not a plugin — the `LspAttach`
  autocmd widens `triggerCharacters` to all printable ASCII, which is what
  makes it fire as you type. Servers are installed manually with `:Mason`;
  `sourcekit` comes from the Xcode toolchain instead. The tracked lockfile is
  `nvim-pack-lock.json`: `vim.pack` writes it, so **never hand-edit it** and
  commit it after plugin changes (`:h vim.pack-lockfile`). Plugins install to
  `~/.local/share/nvim/site/pack/core/opt`, outside this repo. Before this it
  was the LazyVim starter; `70ad436` and its parent hold that history.
  Three mini.nvim traps: `mini.icons` is the icon provider and
  `mock_nvim_web_devicons()` is what keeps oil and telescope working, so do
  not "fix" a missing `nvim-web-devicons` by reinstalling it; `mini.diff` is
  pinned to `style = "sign"` because its default tints the line number
  whenever `'number'` is set; and `mini.ai` deliberately has no
  `gen_spec.treesitter` entries, since nvim-treesitter's `main` branch ships
  no textobjects queries and such specs would silently never match.
  **Treesitter highlighting depends on symlinks outside this repo.** On the
  `main` branch the highlight queries live in the plugin's
  `runtime/queries/<lang>/`, which is *not* on the runtimepath; `install()`
  symlinks each language into `~/.local/share/nvim/site/queries/<lang>` and
  skips any link that already exists, so a stale one silently survives
  forever. If files look unhighlighted, that is the first thing to check:
  `find -L ~/.local/share/nvim/site/queries -maxdepth 1 -type l` lists broken
  links; delete them and re-run `require("nvim-treesitter").install(langs,
  { force = true })` to relink. Only `c`, `lua`, `markdown`,
  `markdown_inline`, `query`, `vim` and `vimdoc` keep working when the links
  are broken, because Neovim ships those queries itself -- which makes the
  breakage look language-specific rather than systemic. This happened once
  already: the links pointed into the old LazyVim plugin tree and broke when
  it was deleted.
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

- **herdr's base is Wave, corrected by `[theme.custom]`.** Its built-in
  `kanagawa` is the Wave variant; all 19 tokens of its `CustomThemeColors`
  struct are overridden to Dragon in `config.toml`. Colours herdr derives
  outside those 19 still come from Wave. `herdr config check` does not validate
  colour values — a bad hex silently falls back — and `herdr server
  reload-config` applies changes without a restart.
- **Kanagawa Dragon sets ANSI 8 ("bright black") to a LIGHT grey** `#a6a69c`,
  unlike almost every other dark theme. Anything that assumes bright-black is a
  dark background breaks. That is why the Claude Code theme overrides
  `userMessageBackground`, `userMessageBackgroundHover`,
  `composerSidebarBackground` and `memoryBackgroundColor`: its `dark-ansi` base
  maps three of them to `ansi:blackBright`, which rendered user messages as
  light-on-light. Watch for the same trap in any other ANSI-based theme.
- **opencode uses a vendored theme, not its built-in.** opencode's own
  `kanagawa` is Wave (its bundled defs are `sumiInk*`/`fujiWhite`), so a Dragon
  theme is vendored at `opencode/.config/opencode/themes/kanagawa-dragon.json`.
  opencode loads global themes from `<config>/themes/<name>.json`; the file's
  50 theme keys mirror its built-in kanagawa exactly, and every value is a
  reference into `defs`.
- **nvim needs a plugin spec.** Nothing ships kanagawa, so `init.lua` adds
  `rebelot/kanagawa.nvim` to `vim.pack.add` and calls
  `require("kanagawa").setup{ theme = "dragon" }` followed by
  `colorscheme kanagawa-dragon` immediately after, so the theme is applied
  before the first buffer is drawn. There is no vendored `colors/` directory.
  Commit `nvim-pack-lock.json` after any plugin change.
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
