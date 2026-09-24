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
claude holodeck vademecum rewind`, plus `xcode` (macOS only) and the
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
- **nvim** — a hand-written config: everything lives in `init.lua`, on
  Neovim's built-in `vim.pack` manager. The colorscheme is the one exception:
  Default+ has no upstream Neovim plugin, so `colors/default-plus.lua` is
  vendored from `~/Developer/default-plus-nvim`. Re-copy it rather than
  editing it here, and note that `vim.pack.add` therefore lists **no theme
  plugin at all** — a `require("<theme>").setup{}` call would be a mistake. There is no distro and
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
- **bat** — Default+ is not built into bat, so the theme is vendored as
  `themes/default-plus.tmTheme` and bat only picks it up from a compiled
  cache: run `bat cache --build` after stowing or after editing it. See the
  theme trap in the Default+ section about the `--theme` value. The file is
  hand-written here — there is no upstream tmTheme to re-copy — so its scope
  list is the only place a missing scope can be fixed. Known limitation: the
  bundled Swift grammar does not emit `entity.name.type`/`entity.name.function`
  for plain declarations, so a `struct Foo` name renders as plain text rather
  than teal. That is the grammar, not the theme.
- **yazi** — only `theme.toml` is tracked; yazi's own keymap/yazi.toml stay on
  defaults. The theme is hand-written (Default+ has no yazi flavor at all) and
  the `[icon]` table is deliberately absent, so the icon preset stays on
  yazi's default. `mgr.syntect_theme` points at
  `$HOME/.config/bat/themes/default-plus.tmTheme`, reusing the bat package's
  vendored tmTheme for code previews. Two traps on that path: it must stay
  absolute (26.x rejects relative ones and does not expand `~`, though it does
  expand `$HOME`), and a bad path silently falls back to yazi's built-in dark
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

- **xcode** — macOS only, listed in `DARWIN_ONLY_PACKAGES`. Tracks exactly one
  file, `Default+.xccolortheme`, under
  `~/Library/Developer/Xcode/UserData/FontAndColorThemes/`. Everything else in
  `UserData/` is runtime state; leave it out.

  **This file is the source of truth for the whole repo's palette** — it is not
  a port, it is the original. `docs/palette.md` is derived from it, and
  upstream's `bin/build.py --check` re-reads it and fails if they disagree.
  Unlike the Catppuccin package this replaces, the values are **not**
  pre-compensated for Xcode's rendering: this targets Xcode 26 and the classic
  plist, which it renders directly.

  Two traps:

  Xcode 27's second format, `.xcworkspacecolortheme` (JSON, OKLCh, **not** a
  plist — `plutil` accepts both, so a plist there lints clean and fails
  silently), is out of scope. An unfinished `Default+.xcworkspacecolortheme`
  sits in `UserData/` on the macOS machine; it is deliberately untracked and is
  **not** a source of anything. Do not read values out of it.

  Theme *selection* lives in
  `UserData/XcodeSettings/<user>.xcodesettings/UserDefaults/XcodeDefaults.plist`
  (`XCFontAndColorCurrentDarkTheme`), not in
  `~/Library/Preferences/com.apple.dt.Xcode.plist`, which is a stale shadow —
  editing the latter does nothing.

- **rewind** — only `theme.toml` is tracked, and it is one line:
  `base = "default-plus"`. rewind uses the same theme schema as vademecum —
  the same 15 `[palette]` slots and the same `[elements.*]` tables, because
  its built-ins were ported from vademecum's — and, like vademecum, it
  **ships Default+ as a built-in**, so the base is all this file needs. Add a
  `[palette]` or `[elements.*]` table below the `base` line only for slots you
  want different from the built-in. Upstream is `~/Developer/rewind`
  (`themes/default-plus.toml`); that repo's gate is `make check`, and a change
  to a theme key updates its README in the same PR under a `docs:` commit.
  Nothing else in `~/.config/rewind/` is written by the program — it reads
  that directory and caches elsewhere — so the whole directory is safe to stow.
- **vademecum** — the theme is the whole config; there is no "default theme by
  name" setting. `~/.config/vademecum/theme.toml` *is* the default theme.
  It now ships Default+ as a built-in (`--list-themes` lists it alongside
  `catppuccin-mocha`, `kanagawa-dragon`, etc.), so the file is back to the
  one-line `base = "default-plus"` form, same as `rewind`. Earlier palettes
  needed the full 15 `[palette]` slots plus the three `code_block` elements
  spelled out by hand because vademecum shipped no Default+ of its own yet;
  that manual form is only needed again if you want to override a slot below
  the `base` line. `--list-themes` and `--list-syntax-themes` print what it
  knows. **`syntax_theme` takes a name, not a path**, so unlike yazi it cannot
  reuse the bat package's tmTheme: fenced code blocks inside Markdown are
  *not* Default+, and `base16-ocean.dark` is the least discordant of its
  seven built-ins.

## Default+ theme

**`docs/palette.md` is the source of truth for every colour in this repo**, and
its own source is the `xcode` package's `Default+.xccolortheme`.

Unlike Kanagawa, Catppuccin and Vesper before it, Default+ is not a published
palette with community ports. It is a personal theme, so the standing "prefer
re-copying upstream over editing a vendored file by hand" rule needed an
upstream to point at. That upstream is **`~/Developer/default-plus`**
(`palette.yaml` + `bin/build.py`), with satellites `default-plus-nvim`,
`default-plus-obsidian` and `default-plus-vscode`.

Workflow for any colour change:

1. change it in Xcode;
2. copy the theme to `~/Developer/default-plus/xcode/`;
3. run `bin/build.py` there — `--check` re-reads the plist and recomputes every
   derived blend, `--generate` rewrites the mechanical ports, `--validate`
   fails on any port using a colour outside the palette;
4. re-copy the affected files here, and regenerate `docs/palette.md`.

Run upstream's validator across the satellites too:

```sh
cd ~/Developer/default-plus
bin/build.py --validate --also ../default-plus-nvim ../default-plus-obsidian ../default-plus-vscode
```

### The one thing to not "fix"

**Comments are green and strings are red.** That is Xcode's own role assignment
and the single thing that distinguishes Default+ from Apple's stock dark theme.
Every TUI/editor port in the wild gets this backwards, because the terminal
convention is grey comments and green strings. It was backwards in this repo's
own ports until it was corrected deliberately. Identifiers you declare share
one teal; SDK members are purple and SDK types light purple — that split is
project-vs-system, reproduced through treesitter's `.builtin` captures and the
LSP `defaultLibrary` modifier.

### Traps worth knowing

- **Nothing selects the theme purely by name any more.** Under Catppuccin, six
  tools did. Default+ is nobody else's built-in, so every tool now carries a
  vendored or hand-written palette — except holodeck, which *is* a built-in
  there because holodeck is one of this user's own projects
  (`~/Developer/holodeck`, `crates/holodeck-tui/src/theme.rs`,
  `Theme::default_plus`, and its default). Change the palette and that Rust
  constructor has to change with it; its unit test pins the hexes.
- **ANSI normal and bright are distinct**, so anything that promotes bold to
  bright must be off: ghostty `bold-is-bright = false`, Apple Terminal
  `UseBrightBold = false`. Both are set by upstream's generator.
- **Apple Terminal rewrites ANSI foregrounds** when `DynamicANSIForegroundColors`
  is true, silently overriding the palette. The generator pins it false; the
  live profile had it on.
- **Apple Terminal cannot be stowed.** Profiles live in the `com.apple.Terminal`
  preferences domain, not a file in `$HOME`; the `.terminal` file is an import
  artifact. It stays upstream, imported by hand.
- **bat's `--theme` is the .tmTheme *filename*** (`default-plus`), not the
  plist's `name` key (`Default+`). A wrong value is silent — bat prints its
  Monokai default rather than erroring. Run `bat cache --build` after any edit.
- **tmux hex must stay lowercase.** `#F`/`#I`/`#W`/`#S`/`#T`/`#P`/`#H`/`#D` are
  legacy format specifiers, so `bg=#35B0D8` expands to nonsense. The one
  uppercase hex in `tmux.conf` is the counter-example inside that comment.
- **tig's 256-colour values are hand-picked, not computed.** Nearest-RGB puts
  the selection colour on the grey ramp right next to `muted`, collapsing two
  distinct roles. `docs/palette.md`'s 256 column is a starting point; the table
  in upstream's `bin/build.py` (`TIG_256`) is the authority.
- **vademecum's `syntax_theme` takes a name, not a path**, so fenced code inside
  Markdown is not Default+. yazi's `syntect_theme` *does* take a path and reuses
  bat's tmTheme — but it must stay absolute, and a bad path falls back silently.
- **`LS_COLORS` is vivid's filetype database with the palette substituted role
  by role**, because vivid ships no Default+. Under Catppuccin this was a plain
  `vivid generate catppuccin-mocha`; it cannot be now. The 17-colour
  substitution table is committed in the file's own header this time, rather
  than left in a commit message as the Kanagawa one was. Directories are
  `declaration` `#35B0D8`, and `LSCOLORS` (BSD `/bin/ls` only) now agrees with
  it — the two used to disagree.
- **`herdr config check` does not validate colours.** A typo'd hex reports
  "config: ok" and silently falls back. `herdr server reload-config` applies
  changes without a restart.
- **Claude Code's theme carries no background overrides.** Default+ maps ANSI
  bright-black to `#515B70`, a normal dark blue-grey, so the `dark-ansi` base
  renders user messages correctly without them. If some future palette ever
  shows light-on-light text, that is the knob. The seven `*Shimmer` values are
  `colour 40% toward foreground` and are recorded in `docs/palette.md`.
- **Xcode's `markup.code` slot is corrected, not copied.** Apple ships the light
  theme's magenta `#AA0D91` there in both stock dark and light themes; at
  2.71:1 on `#171717` it is the only slot failing WCAG AA. It is the one value
  in `palette.yaml` deliberately not bound to the Xcode file.

## Commit messages

Follow the seven rules (cbea.ms/git-commit); nothing enforces this.

- Subject: imperative mood ("Add", "Fix" — not "Added"/"Adds"), capitalized,
  ≤50 chars, no trailing period.
- Blank line after the subject; wrap the body at 72 chars.
- Body explains what and why, not how. A cohesive change gets prose; a commit
  grouping several distinct changes gets `-` bullets.
- Prefix the subject with the package when it's package-scoped, matching
  existing history: `zsh: ...`, `nvim: ...`, `skills: ...`.
