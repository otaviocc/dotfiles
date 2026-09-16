# Catppuccin Mocha — the palette this repo draws with

The single source of truth for every color in these dotfiles. Upstream is
[catppuccin/palette](https://github.com/catppuccin/palette): the names below are
Catppuccin's own, and the role each one plays is its
[style guide](https://github.com/catppuccin/catppuccin/blob/main/docs/style-guide.md).
Nothing here is invented — even the diff backgrounds come from an upstream port.

**Flavor: Mocha.** Catppuccin ships four (Latte, Frappé, Macchiato, Mocha).
Mocha is the darkest: its background is `#1e1e2e` — R30 G30 B46, blue-violet
rather than warm-neutral. Every neutral in the theme leans blue, which is the
character of the theme and not something to correct.

**Accent: `mauve` (`#cba6f7`).** Catppuccin parameterizes a single accent and
mauve is its default — it is what the official nvim, lazygit, yazi and Sublime
ports ship unless told otherwise, so choosing it means those ports drop in
verbatim with no accent rewiring. Swapping it for `peach` (`#fab387`) or `blue`
(`#89b4fa`) is a one-line change in the ports that parameterize it, and a
find-and-replace in the hand-ported tools.

## The palette

`RGB` is the decimal form zsh's `LS_COLORS` needs (`38;2;r;g;b`). `256` is the
nearest xterm-256 index, computed — see the warning under the table before using
it for tig.

| Name | Hex | RGB | 256 |
|---|---|---|---|
| `base` | `#1e1e2e` | `30;30;46` | `color235` |
| `mantle` | `#181825` | `24;24;37` | `color234` |
| `crust` | `#11111b` | `17;17;27` | `color233` |
| `surface0` | `#313244` | `49;50;68` | `color237` |
| `surface1` | `#45475a` | `69;71;90` | `color239` |
| `surface2` | `#585b70` | `88;91;112` | `color241` |
| `overlay0` | `#6c7086` | `108;112;134` | `color243` |
| `overlay1` | `#7f849c` | `127;132;156` | `color103` |
| `overlay2` | `#9399b2` | `147;153;178` | `color103` |
| `subtext0` | `#a6adc8` | `166;173;200` | `color146` |
| `subtext1` | `#bac2de` | `186;194;222` | `color146` |
| `text` | `#cdd6f4` | `205;214;244` | `color189` |
| `rosewater` | `#f5e0dc` | `245;224;220` | `color224` |
| `flamingo` | `#f2cdcd` | `242;205;205` | `color224` |
| `pink` | `#f5c2e7` | `245;194;231` | `color218` |
| `mauve` | `#cba6f7` | `203;166;247` | `color183` |
| `red` | `#f38ba8` | `243;139;168` | `color211` |
| `maroon` | `#eba0ac` | `235;160;172` | `color181` |
| `peach` | `#fab387` | `250;179;135` | `color216` |
| `yellow` | `#f9e2af` | `249;226;175` | `color223` |
| `green` | `#a6e3a1` | `166;227;161` | `color151` |
| `teal` | `#94e2d5` | `148;226;213` | `color116` |
| `sky` | `#89dceb` | `137;220;235` | `color116` |
| `sapphire` | `#74c7ec` | `116;199;236` | `color117` |
| `blue` | `#89b4fa` | `137;180;250` | `color111` |
| `lavender` | `#b4befe` | `180;190;254` | `color147` |

Two things to know about this palette:

- **The 256 column has collisions and is a starting point, not an answer.**
  Nearest-RGB collapses `overlay1`/`overlay2` onto `color103`,
  `subtext0`/`subtext1` onto `color146`, `teal`/`sky` onto `color116` and
  `rosewater`/`flamingo` onto `color224`. tig is the only consumer and it needs
  roles to stay *distinguishable* more than it needs them accurate, so
  `tig/.config/tig/config` hand-picks around these. Its table is the authority
  for tig; this one is the authority for everything else.
- **Mocha has exactly one shade per hue.** Unlike the previous theme there is no
  muted/saturated pair to draw a ramp from, so the three-step ramps below walk
  between hues instead of between shades of one.

## Semantic roles

| Role | Color |
|---|---|
| Editor / terminal background | `base` — Ghostty's built-in Catppuccin Mocha sets the terminal bg to `#1e1e2e`, so every vendored background must agree |
| Panels, status bars | `mantle` — one step darker than content |
| Darkest level | `crust` |
| Text on an accent chip | `base` (style guide: "text on accents: Base") |
| Selection, highlighted row | `surface0` |
| Secondary panel, cherry-picked commit bg | `surface1` |
| Borders, dividers | `surface2` |
| Foreground text | `text` |
| Dimmed / secondary text | `overlay1` |
| Slightly brighter dim text | `overlay2` |
| **Accent** — active border, current window, focus | `mauve` |
| Added / staged / success | `green` |
| Removed / error | `red` |
| Modified / warning | `yellow` |
| Links | `blue` |
| Authors, refs, chunk headers | `lavender` |

Syntax slots are the style guide's own table, verbatim:

| Syntax role | Color |
|---|---|
| Keywords | `mauve` |
| Strings | `green` |
| Symbols, atoms, builtins | `red` |
| Escape sequences, regex | `pink` |
| Comments | `overlay2` |
| Constants, numbers | `peach` |
| Operators | `sky` |
| Braces, delimiters, punctuation | `overlay2` |
| Methods, functions | `blue` |
| Parameters | `maroon` |
| Classes, types, annotations, attributes | `yellow` |
| Enum variants | `teal` |
| Properties (JSON keys) | `blue` |
| Macros | `rosewater` |

Note there is no dedicated variable color: variables take the plain `text`
foreground.

## Derived shades

Catppuccin publishes no diff-background table — the style guide only says a
selection is "Overlay 2 at 20–30% opacity", which a terminal cannot do. The
four row and word backgrounds below are taken from
[catppuccin/delta](https://github.com/catppuccin/delta), the one upstream port
that resolves that guidance into opaque hex (✓).

Those four turn out to follow an exact formula: **a row is its color 20% into
`base`, a word-level highlight is 35%.** That formula reproduces all four delta
values to the last digit, so the remaining shades are extrapolated with it
rather than invented from scratch.

| Purpose | Source | Hex |
|---|---|---|
| Added row background | `green` 20% into `base` | `#394545` ✓ |
| Removed row background | `red` 20% into `base` | `#493447` ✓ |
| Added word (intra-line) highlight | `green` 35% into `base` | `#4e6356` ✓ |
| Removed word (intra-line) highlight | `red` 35% into `base` | `#694559` ✓ |
| Moved-added row background | `blue` 20% into `base` | `#333c57` |
| Moved-removed row background | `yellow` 20% into `base` | `#4a4548` |
| Added gutter | `green` 22% into `base` | `#3c4947` |
| Removed gutter | `red` 22% into `base` | `#4d3649` |
| Accent, muted (note borders) | `mauve` 35% into `base` | `#5b4e74` |
| Muted added sign / badge | `green` | `#a6e3a1` ✓ |
| Muted removed sign / badge | `red` | `#f38ba8` ✓ |
| Muted changed sign / badge | `yellow` | `#f9e2af` ✓ |

Claude Code's theme also needs a lighter "shimmer" twin for seven colors. Those
follow one rule too — **the color 40% into `text`** — so they are recorded here
rather than left as orphan hexes in the theme file the way the last palette left
them:

| Shimmer of | Hex |
|---|---|
| `mauve` (also `rainbow_violet`) | `#ccb9f6` |
| `pink` (also `permission`) | `#e5caec` |
| `peach` (also `fastMode`, `rainbow_orange`) | `#e8c1b3` |
| `red` | `#e4a9c6` |
| `yellow` | `#e7ddcb` |
| `green` | `#b6dec2` |
| `blue` | `#a4c2f8` |
| `lavender` | `#bec8fa` |

Three-step ramps walk along real palette entries instead of blending. Because
Mocha has one shade per hue, each step moves hue rather than saturation —
cooler and paler at the bottom, warmer and more alarming at the top:

| Ramp | cool → warm → hot |
|---|---|
| Added heat | `teal #94e2d5` → `green #a6e3a1` → `yellow #f9e2af` |
| Removed heat | `flamingo #f2cdcd` → `maroon #eba0ac` → `red #f38ba8` |
| Mixed heat | `sapphire #74c7ec` → `peach #fab387` → `red #f38ba8` |
| Accent pulse | `lavender #b4befe` → `mauve #cba6f7` → `pink #f5c2e7` |
| Track (behind any ramp) | `surface1 #45475a` |

## Where the copies live

| Tool | How it gets the palette |
|---|---|
| Ghostty | built-in — `theme = "Catppuccin Mocha"` |
| Neovim | the `catppuccin/nvim` plugin — `flavour = "mocha"` |
| herdr | built-in — `name = "catppuccin"` |
| opencode | built-in — `"theme": "catppuccin-mocha"` |
| bat | `bat/.config/bat/themes/catppuccin-mocha.tmTheme`, vendored from `catppuccin/bat` verbatim |
| lazygit | `gui.theme` from `catppuccin/lazygit`, the `mocha/mauve` variant |
| yazi | `yazi/.config/yazi/theme.toml`, vendored from `catppuccin/yazi` (`mocha-mauve`). Code previews reuse the bat vendored `.tmTheme` via `syntect_theme` |
| zsh | `LS_COLORS` from `vivid generate catppuccin-mocha` |
| Sublime Text | `sublime/.../User/catppuccin-mocha.sublime-color-scheme`, vendored from `catppuccin/sublime-text` verbatim |
| tmux, tig, hunk, vigia | hand-ported inline — no upstream port this repo can consume |
| holodeck | built-in — `"theme": "catppuccin-mocha"` |
| vademecum | built-in — `base = "catppuccin-mocha"` |
| Claude Code | theme: `claude/.claude/themes/catppuccin-mocha.json`; statusline: `claude/.claude/statusline.py` emits truecolor escapes for the hexes inline |

The hand-ported four are the only places a value is transcribed by hand.
**tmux's** official port is a TPM plugin and this repo runs no tmux plugin
manager; **tig**, **hunk** and **vigia** have no Catppuccin port at all.
