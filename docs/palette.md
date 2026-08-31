# Kanagawa Dragon — the palette this repo draws with

The single source of truth for every color in these dotfiles. Upstream is
[rebelot/kanagawa.nvim](https://github.com/rebelot/kanagawa.nvim): the names in
the second column are its own, from `lua/kanagawa/colors.lua`, and the role each
one plays is the `dragon` block of `lua/kanagawa/themes.lua`. Nothing here is
invented — even the diff backgrounds are upstream's.

**Variant: Dragon.** Kanagawa ships three (Wave, Dragon, Lotus). Dragon is the
darkest and the warmest: its background is `#181616` — R24 G22 B22, warm-neutral
rather than the blue-violet `#1e1e2e` of Catppuccin or the `#1a1b26` of Tokyo
Night. Every neutral in the theme leans warm, which is the point.

**Accent: `yellow` (`dragonYellow`, `#c4b28a`).** Kanagawa declares no single
accent the way Catppuccin parameterizes one, so this is a choice made here: it
is the closest thing in the palette to the warm sandy `#FFC799` that the old
Vesper setup used as its accent. Swapping it for `orange` (`#b6927b`) or `blue`
(`#8ba4b0`) is a one-line change per tool.

## The palette

`RGB` is the decimal form zsh's `LS_COLORS` needs (`38;2;r;g;b`). `256` is the
nearest xterm-256 index, for tig, which has no truecolor.

| Name | Upstream name | Hex | RGB | 256 |
|---|---|---|---|---|
| `bg` | `dragonBlack3` | `#181616` | `24;22;22` | `color233` |
| `bg_m1` | `dragonBlack2` | `#1d1c19` | `29;28;25` | `color234` |
| `bg_m2` | `dragonBlack1` | `#12120f` | `18;18;15` | `color233` |
| `bg_m3` | `dragonBlack0` | `#0d0c0c` | `13;12;12` | `color232` |
| `bg_p1` | `dragonBlack4` | `#282727` | `40;39;39` | `color235` |
| `bg_p2` | `dragonBlack5` | `#393836` | `57;56;54` | `color237` |
| `whitespace` | `dragonBlack6` | `#625e5a` | `98;94;90` | `color59` |
| `border` | `sumiInk6` | `#54546d` | `84;84;109` | `color59` |
| `selection` | `waveBlue1` | `#223249` | `34;50;73` | `color236` |
| `search` | `waveBlue2` | `#2d4f67` | `45;79;103` | `color239` |
| `comment` | `dragonAsh` | `#737c73` | `115;124;115` | `color243` |
| `special` | `dragonGray3` | `#7a8382` | `122;131;130` | `color244` |
| `punct` | `dragonGray2` | `#9e9b93` | `158;155;147` | `color247` |
| `param` | `dragonGray` | `#a6a69c` | `166;166;156` | `color247` |
| `fg_dim` | `oldWhite` | `#c8c093` | `200;192;147` | `color180` |
| `fg` | `dragonWhite` | `#c5c9c5` | `197;201;197` | `color251` |
| `red` | `dragonRed` | `#c4746e` | `196;116;110` | `color173` |
| `green` | `dragonGreen2` | `#8a9a7b` | `138;154;123` | `color245` |
| `green_br` | `dragonGreen` | `#87a987` | `135;169;135` | `color108` |
| `yellow` | `dragonYellow` | `#c4b28a` | `196;178;138` | `color180` |
| `orange` | `dragonOrange` | `#b6927b` | `182;146;123` | `color138` |
| `orange2` | `dragonOrange2` | `#b98d7b` | `185;141;123` | `color138` |
| `blue` | `dragonBlue2` | `#8ba4b0` | `139;164;176` | `color109` |
| `pink` | `dragonPink` | `#a292a3` | `162;146;163` | `color247` |
| `aqua` | `dragonAqua` | `#8ea4a2` | `142;164;162` | `color247` |
| `violet` | `dragonViolet` | `#8992a7` | `137;146;167` | `color103` |
| `teal` | `dragonTeal` | `#949fb5` | `148;159;181` | `color109` |
| `error` | `samuraiRed` | `#e82424` | `232;36;36` | `color160` |
| `warning` | `roninYellow` | `#ff9e3b` | `255;158;59` | `color215` |
| `ok` | `springGreen` | `#98bb6c` | `152;187;108` | `color107` |
| `info` | `dragonBlue` | `#658594` | `101;133;148` | `color66` |
| `hint` | `waveAqua1` | `#6a9589` | `106;149;137` | `color66` |
| `diff_add` | `winterGreen` | `#2b3328` | `43;51;40` | `color236` |
| `diff_delete` | `winterRed` | `#43242b` | `67;36;43` | `color236` |
| `diff_change` | `winterBlue` | `#252535` | `37;37;53` | `color235` |
| `diff_text` | `winterYellow` | `#49443c` | `73;68;60` | `color238` |
| `vcs_added` | `autumnGreen` | `#76946a` | `118;148;106` | `color101` |
| `vcs_removed` | `autumnRed` | `#c34043` | `195;64;67` | `color131` |
| `vcs_changed` | `autumnYellow` | `#dca561` | `220;165;97` | `color179` |

Two things to know about this palette:

- **`selection` and `search` are the only blue in Dragon.** `waveBlue1`
  `#223249` and `waveBlue2` `#2d4f67` are borrowed from the Wave variant, and
  upstream uses them for `bg_visual` / `bg_search` even in Dragon. They are kept
  rather than warmed, because they are what gives a selected row enough contrast
  against a background this dark — but they *are* the one cool note in an
  otherwise warm theme.
- **`error`, `warning` and `ok` are much more saturated than everything else**
  (`samuraiRed #e82424`, `roninYellow #ff9e3b`, `springGreen #98bb6c`). That is
  deliberate upstream: Dragon's ordinary syntax colors are deliberately muted,
  so diagnostics need the extra punch to read as alarming. Don't "fix" them to
  match the muted accents.

## Semantic roles

| Role | Color |
|---|---|
| Editor / terminal background | `bg` — Ghostty's built-in Kanagawa Dragon sets the terminal bg to `#181616`, so every vendored background must agree |
| Panels, status bars | `bg_m2` — one step darker than content |
| Darkest level; text on an accent chip | `bg_m3` |
| Selection, highlighted row | `selection` |
| Secondary panel, cherry-picked commit bg | `bg_p1` |
| Borders, dividers | `whitespace` (warm grey) |
| Foreground text | `fg` |
| Dimmed / secondary text | `comment` |
| Slightly brighter dim text | `punct` |
| **Accent** — active border, current window, focus | `yellow` |
| Added / staged / success | `vcs_added` |
| Removed / error | `vcs_removed` |
| Modified / warning | `vcs_changed` |
| Authors, refs, chunk headers | `violet` |

Syntax slots follow Dragon's own `syn` table rather than translating whatever
theme came before — the point of a port is to look like the thing it ports:

| Syntax role | Color | Upstream key |
|---|---|---|
| Keywords, statements | `violet` | `syn.keyword`, `syn.statement` |
| Operators, preprocessor, regex | `red` | `syn.operator`, `syn.preproc` |
| Types | `aqua` | `syn.type` |
| Functions | `blue` | `syn.fun` |
| Identifiers | `yellow` | `syn.identifier` |
| Constants | `orange` | `syn.constant` |
| Numbers | `pink` | `syn.number` |
| Strings | `green` | `syn.string` |
| Parameters | `param` | `syn.parameter` |
| Punctuation | `punct` | `syn.punct` |
| Comments | `comment` | `syn.comment` |

Note Dragon sets `syn.variable = "none"` — variables deliberately inherit the
plain foreground rather than getting a color of their own.

## Derived shades

Unlike the previous two themes, almost nothing needs deriving: Kanagawa ships
real diff *backgrounds* in its `diff` table and real sign *foregrounds* in its
`vcs` table, so the row level is upstream's verbatim (✓). Only the word-level
and gutter steps are extrapolated, by mixing the matching `vcs` color into `bg`.

| Purpose | Source | Hex |
|---|---|---|
| Added row background | `diff_add` (`winterGreen`) | `#2b3328` ✓ |
| Removed row background | `diff_delete` (`winterRed`) | `#43242b` ✓ |
| Moved-added row background | `diff_change` (`winterBlue`) | `#252535` ✓ |
| Moved-removed row background | `diff_text` (`winterYellow`) | `#49443c` ✓ |
| Added word (intra-line) highlight | `vcs_added` 35% into `bg` | `#394233` |
| Removed word (intra-line) highlight | `vcs_removed` 35% into `bg` | `#542526` |
| Added gutter | `vcs_added` 22% into `bg` | `#2d3228` |
| Removed gutter | `vcs_removed` 22% into `bg` | `#3e1f20` |
| Accent, muted (note borders) | `yellow` 35% into `bg` | `#544d3f` |
| Muted added sign / badge | `vcs_added` (`autumnGreen`) | `#76946a` ✓ |
| Muted removed sign / badge | `vcs_removed` (`autumnRed`) | `#c34043` ✓ |
| Muted changed sign / badge | `vcs_changed` (`autumnYellow`) | `#dca561` ✓ |

Three-step ramps walk along real palette entries instead of blending:

| Ramp | cool → warm → hot |
|---|---|
| Added heat | `green #8a9a7b` → `green_br #87a987` → `ok #98bb6c` |
| Removed heat | `red #c4746e` → `vcs_removed #c34043` → `error #e82424` |
| Mixed heat | `orange #b6927b` → `vcs_changed #dca561` → `warning #ff9e3b` |
| Accent pulse | `yellow #c4b28a` → `vcs_changed #dca561` → `fg_dim #c8c093` |
| Track (behind any ramp) | `bg_p2 #393836` |

Each ramp deliberately ends on one of the saturated diagnostic colors, so "hot"
genuinely escalates out of the muted range rather than staying inside it.

## Where the copies live

| Tool | How it gets the palette |
|---|---|
| Ghostty | built-in — `theme = "Kanagawa Dragon"` |
| Neovim | the `kanagawa.nvim` plugin — `colorscheme = "kanagawa-dragon"` |
| herdr | built-in — `name = "kanagawa"` (**Wave**, not Dragon — see below) |
| opencode | `opencode/.config/opencode/themes/kanagawa-dragon.json` — vendored, because its built-in `kanagawa` is Wave |
| bat | `bat/.config/bat/themes/kanagawa-dragon.tmTheme`, from upstream `extras/tmTheme` |
| lazygit | `gui.theme` hand-ported (no official lazygit port) |
| zsh | `LS_COLORS` hand-ported (vivid has no Kanagawa) |
| tmux, tig, hunk, vigia | hand-ported inline |
| holodeck | built-in — `"theme": "kanagawa-dragon"` (added upstream) |
| Claude Code | `claude/.claude/themes/kanagawa-dragon.json` |

**The one real gap: herdr ships a single `kanagawa` and it is the Wave
variant** (herdr stores its colors non-textually so the variant could not be read out of
the binary, but Wave is Kanagawa's default and herdr exposes no variant
switch). Wave's background is `#1F1F28` — noticeably purple next to Dragon's
warm `#181616`, so that pane reads cooler than everything around it. Fixing it
means a `[theme.custom]` block in herdr's config, which is not done here.

opencode had the identical problem — its bundled `kanagawa` defines
`sumiInk0: #1F1F28` and `fujiWhite`, so it is unambiguously Wave — and *was*
fixed, by vendoring a Dragon theme into
`opencode/.config/opencode/themes/kanagawa-dragon.json`. opencode loads global
themes from `<config>/themes/<name>.json`, and the vendored file mirrors the
50 theme keys of its built-in kanagawa exactly.
