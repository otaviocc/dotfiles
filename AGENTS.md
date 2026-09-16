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

Packages: `zsh git nvim tmux ghostty sublime lazygit tig yazi herdr opencode hunk vigia bat
claude holodeck vademecum`, plus `xcode` (macOS only) and the
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
  a bare `./install.sh` will silently skip it. Two exceptions: overlay packages
  are derived as `${package}-${OS_SUFFIX}` and must **not** be listed, and
  macOS-only packages go in `DARWIN_ONLY_PACKAGES` instead.
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

   `sublime-macos` is the same mechanism pointed at a different problem: macOS
   keeps the whole Sublime Text data dir under `~/Library/Application Support`
   while Linux uses `~/.config/sublime-text`. The base `sublime` package uses the
   Linux path, and the macOS overlay ships one symlink mounting
   `Packages/User` there back at the same content
   (`sublime-macos/Library/Application Support/Sublime Text/Packages/User ->
   ../../../../../sublime/.config/sublime-text/Packages/User`). The committed
   relative target is counted from inside the repo package; stow re-creates it
   at `$HOME`.

There is also a **third, simpler case**: a package with no Linux counterpart at
all. `xcode` is the only one. It is an ordinary package listed in
`DARWIN_ONLY_PACKAGES`, appended to the default set on Darwin and skipped with a
log line on Linux even when named explicitly. Do not confuse this with the
`*-macos` overlays: `sublime` exists on both machines and only its *path*
differs, whereas Xcode does not exist on Fedora at all, so stowing it there
would create an empty `~/Library/Developer` tree.

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
- **bat** — Catppuccin is not built into bat, so the theme is vendored as
  `themes/catppuccin-mocha.tmTheme` (copied verbatim from `catppuccin/bat`) and
  bat only picks it up from a compiled cache: run `bat cache --build` after
  stowing or after editing it. See the theme trap in the Catppuccin Mocha
  section about the `--theme` value.
- **yazi** — only `theme.toml` is tracked; yazi's own keymap/yazi.toml stay on
  defaults. The theme is vendored from `catppuccin/yazi` (`mocha-mauve`) with
  exactly two changes, both documented in its header: upstream's `[icon]`
  section is dropped (the icon preset stays on yazi's default), and
  `mgr.syntect_theme` points at
  `$HOME/.config/bat/themes/catppuccin-mocha.tmTheme`, reusing the bat
  package's vendored tmTheme for code previews. Two traps on that path: it must
  stay absolute (26.x rejects relative ones and does not expand `~`, though it
  does expand `$HOME` — upstream ships it as `~/...`, which is why it cannot be
  copied verbatim), and a bad path silently falls back to yazi's built-in dark
  theme — same silent failure as bat's `--theme`.
- **herdr** — only `config.toml` is tracked. Logs, `session.json`,
  `release-notes.json` and `.plugins.lock` are runtime state; leave them out.
- **holodeck** — only `config.json` is tracked. `url-history.json` next to it
  is runtime state; leave it out. The file is strict JSON (serde_json), so it
  takes no comments — document choices here or in the README, not inline.
- **claude** — the package tracks exactly three things: `~/.claude/themes/`,
  `~/.claude/skills/`, and `~/.claude/statusline.py`. Each needs its own `!`
  negation in `.gitignore` (the blanket `/claude/.claude/*` ignore is there so a
  stray `git add` can't commit `settings.json`, which holds API tokens).
  `settings.json` itself is never tracked, so wiring the statusline is a
  per-machine bootstrap step — add
  `"statusLine": { "type": "command", "command": "~/.claude/statusline.py" }`
  by hand. The script is Python 3 stdlib-only, reads Claude Code's status JSON
  on stdin, and uses truecolor escapes from `docs/palette.md` directly, so it
  does not depend on how the terminal maps the ANSI slots.
- **skills** — personal agent skills live in the `claude` package at
  `claude/.claude/skills/`, stowed to `~/.claude/skills/`, which both Claude Code
  and opencode read natively. Skill-specific rules live in
  `claude/.claude/skills/AGENTS.md` — read it before touching any skill script.
  On the macOS machine `~/.config/opencode/skills/` still holds a few
  opencode-only skills this repo does not track (Supacode's own, and symlinks
  into `~/.agents/skills/`) — don't assume everything there is version-controlled.

- **xcode** — tracks exactly two files, both Xcode colour themes, under
  `~/Library/Developer/Xcode/UserData/FontAndColorThemes/`. Everything else in
  `UserData/` is runtime state; leave it out. Two traps:

  **The hex values in these files are deliberately NOT the Catppuccin ones.**
  Xcode does not render a theme's colours literally — it derives a "recipe" from
  them and regenerates against its own contrast curve, which lifts lightness and
  drains chroma. Measured off a screenshot (converted out of the display's ICC
  profile into sRGB), the shift is **L +0.043, C x0.8**, hue untouched. Both
  files are therefore pre-compensated by the inverse, **L -0.043, C x1.25**, so
  that what lands on screen is true Catppuccin Mocha. `background` is stored as
  `#141327` and renders as `#1e1e2e`; `keyword` is stored as `#c292f7` and
  renders as `#cba6f7`. Do not "correct" them back to the palette — that is what
  produced the washed-out look in the first place. Re-derive with the script in
  the commit that added this package if the shift ever changes.

  The two files are the same theme in Xcode's two formats: `.xccolortheme` is
  the classic plist, `.xcworkspacecolortheme` is the Xcode 27 recipe format
  (JSON, **not** a plist — `plutil` accepts both, so a plist here lints clean
  and fails silently). The recipe stores OKLCh (`lightness`/`chroma`/`hue` in
  radians); despite `"gamut": "P3"` the numbers are **sRGB-relative**. Xcode 26.6
  already runs the recipe engine, so both files matter on both versions. They
  agree slot for slot.

  The upstream `catppuccin/xcode` themes sit next to these as untracked real
  files; `Catppuccin Mocha` is kept unmodified as a reference to compare against.
  Theme *selection* lives in
  `UserData/XcodeSettings/<user>.xcodesettings/UserDefaults/XcodeDefaults.plist`,
  not in `~/Library/Preferences/com.apple.dt.Xcode.plist`, which is a stale
  shadow — editing the latter does nothing. Opening Xcode 27 re-runs a theme
  migration that pins a `savedRecipe` UUID and can silently re-theme Xcode 26,
  since both share one preferences domain.

- **vademecum** — the theme is the whole config; there is no "default theme by
  name" setting. `~/.config/vademecum/theme.toml` *is* the default theme, so
  `theme.toml` here is the one line `base = "catppuccin-mocha"`: `base` names a
  built-in and the rest of the file merges over *that* (not over `ansi`), so
  there is no palette to copy and nothing to drift out of sync with upstream.
  Add a `[palette]` or `[elements.*]` table below the `base` line only for
  slots you actually want different from upstream. `--theme catppuccin-mocha`
  selects the same theme per run without this file at all; the file exists only
  to make it the default.

## Catppuccin Mocha theme

**`docs/palette.md` is the source of truth for every color in this repo.**
Flavor is **Mocha**, accent is **mauve** `#cba6f7`.

Nothing here is invented. Syntax slots are Catppuccin's own
[style guide](https://github.com/catppuccin/catppuccin/blob/main/docs/style-guide.md)
(keyword=mauve, string=green, operator=sky, comment/punctuation=overlay2,
constant+number=peach, function=blue, type/class/attribute=yellow,
parameter=maroon, builtin=red, escape/regex=pink). Catppuccin names no variable
colour, so variables inherit the plain foreground.

Catppuccin publishes no diff-background table — the style guide only says a
selection is "Overlay 2 at 20–30% opacity", which a terminal cannot do. The four
row and word backgrounds come from `catppuccin/delta`, the one upstream port
that resolves that into opaque hex. They follow an exact rule (row = colour 20%
into `base`, word = 35%), so the moved-row and gutter steps are extrapolated
with the same rule rather than guessed.

**Most tools now take an upstream port rather than a hand-transcription.** Only
four are hand-ported — tmux, tig, hunk and vigia — and each says so in its own
header. Prefer re-copying upstream over editing a vendored file by hand.

Traps worth knowing:

- **Six tools select the theme purely by name**: ghostty (`Catppuccin Mocha`),
  herdr (`catppuccin`), opencode, holodeck, vademecum (`catppuccin-mocha`) and
  bat. Nothing to keep in sync in those files beyond the string.
- **herdr's built-in `catppuccin` is Mocha, but that cannot be proven
  statically.** herdr stores its colours non-textually; the flavour is inferred
  from it pairing with `catppuccin-latte` and from Mocha being the only dark
  Catppuccin hexes in the binary. Check by eye that its background matches
  Ghostty's `#1e1e2e`. This replaced a 19-token `[theme.custom]` block that
  existed only because herdr's `kanagawa` was the Wave variant — do not
  reintroduce an override without a reason. `herdr config check` validates the
  TOML but NOT colour values: a typo'd hex reports "config: ok" and silently
  falls back. `herdr server reload-config` applies changes without a restart.
- **opencode uses its built-in `catppuccin-mocha`.** It previously needed a
  vendored 90-line theme because its bundled `kanagawa` was Wave; that file is
  gone. `opencode/.config/opencode/themes/` no longer exists, so a re-stow is
  needed to clear the old symlink.
- **nvim needs a plugin spec, with an explicit `name`.** `init.lua` adds
  `catppuccin/nvim` to `vim.pack.add` **with `name = "catppuccin"`** — the repo
  is called `nvim`, so without that override vim.pack installs it as `nvim` and
  `require("catppuccin")` fails. `setup{ flavour = "mocha" }` and
  `colorscheme catppuccin` run immediately after, so the theme is applied before
  the first buffer is drawn. The colorscheme resolves to `catppuccin-mocha`.
  Commit `nvim-pack-lock.json` after any plugin change, and never hand-edit it —
  use `vim.pack.del()` to drop a plugin so the lock entry goes with it.
- **bat's `--theme` is the .tmTheme *filename*** (`catppuccin-mocha`), not the
  plist's `name` key (which is `Catppuccin Mocha`). A wrong value is silent —
  bat prints its Monokai default rather than erroring.
- **tmux hex must stay lowercase.** `#F`/`#I`/`#W`/`#S`/`#T`/`#P`/`#H`/`#D` are
  legacy format specifiers, so `bg=#CBA6F7` expands to nonsense. The accent
  beginning with a literal `C` makes this easier than usual to hit.
- **tig's 256-colour values are hand-picked, not computed.** Nearest-RGB
  collides `overlay1`/`overlay2`, `subtext0`/`subtext1` and `teal`/`sky`, which
  would collapse distinct roles. `docs/palette.md`'s 256 column is a starting
  point; tig's own header table is the authority for that file.
- **`LS_COLORS` *is* `vivid generate catppuccin-mocha`**, verbatim. vivid ships
  a Mocha theme, so the role-by-role gruvbox remap the previous palette needed
  is gone — regenerate rather than edit. Note it colours directories blue, not
  the accent; `LSCOLORS` (BSD `/bin/ls` only) was re-slotted to match.
- **Claude Code's theme carries no background overrides any more.** It used to
  override `userMessageBackground`, `userMessageBackgroundHover`,
  `composerSidebarBackground` and `memoryBackgroundColor`, purely because the
  previous theme mapped ANSI bright-black to a *light* grey and the `dark-ansi`
  base rendered user messages light-on-light. Mocha maps bright-black to
  `surface2` `#585b70`, a normal dark grey, so those four slots now inherit the
  ANSI base and follow Ghostty's Catppuccin Mocha palette. **Don't reintroduce
  them without a rendering problem to point at** — but if some other ANSI-based
  theme ever shows light-on-light text, this is the knob. The seven `*Shimmer`
  values are `colour 40% into text` and are recorded in `docs/palette.md` rather
  than left as orphan hexes.
- **The `claude` package tracks `~/.claude/themes/`, `~/.claude/skills/` and
  `~/.claude/statusline.py` only.** `settings.json` selects the theme
  (`"theme": "custom:catppuccin-mocha"`) and wires the statusline but also holds
  API tokens — never add it to the repo; the rest of `~/.claude` is
  session/runtime state.

## Commit messages

Follow the seven rules (cbea.ms/git-commit); nothing enforces this.

- Subject: imperative mood ("Add", "Fix" — not "Added"/"Adds"), capitalized,
  ≤50 chars, no trailing period.
- Blank line after the subject; wrap the body at 72 chars.
- Body explains what and why, not how. A cohesive change gets prose; a commit
  grouping several distinct changes gets `-` bullets.
- Prefix the subject with the package when it's package-scoped, matching
  existing history: `zsh: ...`, `nvim: ...`, `skills: ...`.
