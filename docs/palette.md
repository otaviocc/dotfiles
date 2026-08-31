# Catppuccin Mocha — the palette this repo draws with

The single source of truth for every color in these dotfiles. Upstream is
<https://github.com/catppuccin/catppuccin>; the hexes below are copied from
[`catppuccin/palette`](https://github.com/catppuccin/palette)'s `palette.json`,
`mocha` flavor.

**Flavor: Mocha. Accent: mauve `#cba6f7`.**

Ghostty, herdr, opencode, Neovim, bat and holodeck select Catppuccin *by name*
from a built-in or bundled theme, so they never repeat these values. Every other tool
vendors them, because a fresh `./install.sh` must not have to reach out to
another repo — so six config files hold copies of this table, in six different
syntaxes. When a value here changes, they all have to change with it.

## The 26 colors

`RGB` is the decimal form zsh's `LS_COLORS` needs (`38;2;r;g;b`). `256` is the
nearest xterm-256 index, for tig, which has no truecolor.

| Name | Hex | RGB | 256 |
|---|---|---|---|
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
| `text` | `#cdd6f4` | `205;214;244` | `color189` |
| `subtext1` | `#bac2de` | `186;194;222` | `color146` |
| `subtext0` | `#a6adc8` | `166;173;200` | `color146` |
| `overlay2` | `#9399b2` | `147;153;178` | `color103` |
| `overlay1` | `#7f849c` | `127;132;156` | `color103` |
| `overlay0` | `#6c7086` | `108;112;134` | `color243` |
| `surface2` | `#585b70` | `88;91;112` | `color241` |
| `surface1` | `#45475a` | `69;71;90` | `color239` |
| `surface0` | `#313244` | `49;50;68` | `color237` |
| `base` | `#1e1e2e` | `30;30;46` | `color235` |
| `mantle` | `#181825` | `24;24;37` | `color234` |
| `crust` | `#11111b` | `17;17;27` | `color233` |

Note where the 256-color column collapses distinctions the truecolor palette
makes: `rosewater`/`flamingo` both land on `color224`, `teal`/`sky` both on
`color116`, `subtext1`/`subtext0` both on `color146`, and `overlay2`/`overlay1`
both on `color103`. Worse, Mocha's three darks are all blue-tinted and the
256-color palette has no tinted near-blacks — `base`, `mantle` and `crust`
approximate to the *grayscale* ramp (`color235`/`234`/`233`), so tig reads
slightly cooler-neutral than everything else. That is inherent to 256 colors,
not a mistake to fix.

## Semantic roles

Which slot plays which part, consistently across tools:

| Role | Color |
|---|---|
| Editor / terminal background | `base` — ghostty's built-in Catppuccin Mocha sets the terminal background to `#1e1e2e`, so every vendored background must agree with it |
| Panels, status bars | `mantle` — chrome sits *darker* than content in Catppuccin |
| Darkest level; text on an accent chip | `crust` |
| Selection, highlighted row | `surface0` |
| Secondary panel, cherry-picked commit bg | `surface1` |
| Borders, dividers, inactive gutter text | `surface2` |
| Foreground text | `text` |
| Dimmed / secondary text | `overlay1` |
| **Accent** — active border, current window, focus | `mauve` |
| Added / staged / success | `green` |
| Removed / error | `red` |
| Modified / warning | `peach` |
| Types, classes | `peach` |
| Functions | `mauve` |
| Strings | `teal` |
| Numbers, constants, tags | `pink` |
| Variables | `text` |
| Comments, punctuation | `overlay1` |
| Authors, refs, chunk headers | `lavender` |

## Derived shades

Some tools need shades between two palette entries — diff row backgrounds, and
the three-step "heat" ramps in vigia. Rather than inventing colors, these follow
the convention the official [`catppuccin/delta`](https://github.com/catppuccin/delta)
port established and publishes in `catppuccin.gitconfig`: **mix an accent into
`base` at 20% for a row background and 35% for word-level emphasis.** Values
marked ✓ are copied verbatim from that port; the rest are the same formula
applied to another accent.

| Purpose | Mix | Hex |
|---|---|---|
| Added row background | `green` 20% | `#394545` ✓ |
| Removed row background | `red` 20% | `#493447` ✓ |
| Added word (intra-line) highlight | `green` 35% | `#4e6356` ✓ |
| Removed word (intra-line) highlight | `red` 35% | `#694559` ✓ |
| Added gutter | `green` 28% | `#44554e` |
| Removed gutter | `red` 28% | `#5a3d50` |
| Moved-added row background | `mauve` 20% | `#413956` |
| Moved-removed row background | `blue` 20% | `#333c57` |
| Accent, muted (`accentMuted`, note borders) | `mauve` 35% | `#5b4e74` ✓ |
| Muted added sign / badge | `green` 55% | `#698a6d` |
| Muted removed sign / badge | `red` 55% | `#935a71` |

Beware: `base` is blue-tinted (`#1e1e2e`), so a 20% mix pulls every hue toward
slate — `green` 20% is `#394545`, which reads as a cool grey-teal rather than a
green. That is correct and intended; the row background is meant to be felt, not
seen, with the `+`/`-` sign and the syntax color carrying the actual signal.

Three-step ramps walk along real palette entries instead of blending, so each
step stays a true Catppuccin color:

| Ramp | cool → warm → hot |
|---|---|
| Added heat | `green #a6e3a1` → `teal #94e2d5` → `sky #89dceb` |
| Removed heat | `maroon #eba0ac` → `red #f38ba8` → `flamingo #f2cdcd` |
| Mixed heat | `peach #fab387` → `yellow #f9e2af` → `rosewater #f5e0dc` |
| Accent pulse | `mauve #cba6f7` → `pink #f5c2e7` → `rosewater #f5e0dc` |
| Track (behind any ramp) | `surface1 #45475a` |

## Where the copies live

| Tool | How it gets the palette |
|---|---|
| Ghostty | built-in — `theme = "Catppuccin Mocha"` |
| herdr | built-in — `name = "catppuccin"` |
| opencode | built-in — `theme: "catppuccin"` |
| Neovim | the `catppuccin` plugin, already bundled by LazyVim |
| bat | built-in (bat >= 0.25) — `--theme="Catppuccin Mocha"` |
| holodeck | built-in — `"theme": "catppuccin-mocha"` |
| Claude Code | `claude/.claude/themes/catppuccin-mocha.json` — `dark-ansi` base + accent overrides |
| lazygit | `gui.theme` block, from [`catppuccin/lazygit`](https://github.com/catppuccin/lazygit) `themes/mocha/mauve.yml` |
| tmux | hand-ported inline (the official port needs tpm, which this repo doesn't use) |
| zsh | hand-ported inline — `LS_COLORS`, prompt, `zstyle` formats |
| tig | hand-ported inline, 256-color approximation |
| hunk | hand-ported inline — `[custom_theme]` |
| vigia | hand-ported in `vigia/.config/vigia/theme` |
