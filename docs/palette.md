# Default+ palette

**This file is the source of truth for every colour in this repo.**

Default+ began as an Xcode Font & Color Theme. Its own source of truth is
`xcode/Library/Developer/Xcode/UserData/FontAndColorThemes/Default+.xccolortheme`,
tracked in the `xcode` package, and the upstream that every port is generated
or copied from is `~/Developer/default-plus` (`palette.yaml` + `bin/build.py`).

To change a colour: change it in Xcode, run `bin/build.py` upstream, then
re-copy the affected ports here. Do not edit a vendored file by hand.

Xcode 27's `.xcworkspacecolortheme` recipe format is **not** a source. This
targets Xcode 26 and the classic plist.

## Syntax roles — read this first

Default+ does not follow the usual terminal convention, and that is the point:

- **comments are green** (`#2EA85B`), not grey
- **strings are red** (`#FC4651`), not green
- types, functions, variables and constants **you declare** share one teal
  (`#56D0B3`); SDK members are purple (`#AB64FF`) and SDK types light purple
  (`#D0A8FF`)

The project-vs-system split is the distinction Xcode draws. Ports reproduce it
through treesitter's `.builtin` captures and the LSP `defaultLibrary` modifier.
A port that "corrects" green comments back to grey stops looking like Default+;
that inversion is the whole signature of the theme.

## The palette

`RGB` is decimal, for `LS_COLORS` (`38;2;r;g;b`). `256` is the nearest xterm
index — a **starting point only**; tig's own header table is the authority for
that file, because nearest-RGB collapses distinct roles onto the grey ramp.

| Name | Xcode key | Hex | RGB | 256 | Role |
|---|---|---|---|---|---|
| `background` | `DVTSourceTextBackground` | `#171717` | `23;23;23` | 233 | terminal and editor ground |
| `foreground` | `xcode.syntax.plain` | `#FFFFFF` | `255;255;255` | 231 | body text |
| `cursor` | `DVTSourceTextInsertionPointColor` | `#FFFFFF` | `255;255;255` | 231 | caret |
| `selection_background` | `DVTSourceTextSelectionColor` | `#515B70` | `81;91;112` | 59 | selected region |
| `current_line` | `DVTSourceTextCurrentLineHighlightColor` | `#343540` | `52;53;64` | 237 | cursor line, 50% alpha |
| `invisibles` | `DVTSourceTextInvisiblesColor` | `#4C4C4C` | `76;76;76` | 239 | whitespace marks |
| `muted` | = invisibles | `#4C4C4C` | `76;76;76` | 239 | borders, inactive chrome |
| `muted_text` | `DVTScrollbarMarkerDiffColor` | `#8E8E8E` | `142;142;142` | 245 | secondary text |
| `panel_background` | derived | `#111111` | `17;17;17` | 233 | panels, status bars |
| `subtle` | derived | `#242424` | `36;36;36` | 235 | raised surface, hover |

### Syntax

| Name | Xcode key | Hex | RGB | 256 | Role |
|---|---|---|---|---|---|
| `plain` | `xcode.syntax.plain` | `#FFFFFF` | `255;255;255` | 231 | plain text, operators |
| `comment` | `xcode.syntax.comment` | `#2EA85B` | `46;168;91` | 35 | comments, marks — **green** |
| `string` | `xcode.syntax.string` | `#FC4651` | `252;70;81` | 203 | strings, regex — **red** |
| `keyword` | `xcode.syntax.keyword` | `#F2248C` | `242;36;140` | 198 | keywords, storage |
| `number` | `xcode.syntax.number` | `#FFE76D` | `255;231;109` | 221 | numbers, characters |
| `macro` | `xcode.syntax.identifier.macro` | `#FD8F3F` | `253;143;63` | 209 | macros, preprocessor |
| `attribute` | `xcode.syntax.attribute` | `#E09D65` | `224;157;101` | 179 | attributes, decorators |
| `url` | `xcode.syntax.url` | `#4FA5FF` | `79;165;255` | 75 | links |
| `declaration` | `xcode.syntax.declaration.other` | `#35B0D8` | `53;176;216` | 74 | declarations — the accent |
| `declaration_type` | `xcode.syntax.declaration.type` | `#66DAFF` | `102;218;255` | 81 | type declarations |
| `project_identifier` | `xcode.syntax.identifier.type` | `#56D0B3` | `86;208;179` | 79 | your types/functions/variables |
| `system_member` | `xcode.syntax.identifier.function.system` | `#AB64FF` | `171;100;255` | 135 | SDK functions/variables |
| `system_type` | `xcode.syntax.identifier.type.system` | `#D0A8FF` | `208;168;255` | 183 | SDK types/classes |
| `markup_code` | `xcode.syntax.markup.code` | `#F2248C` | `242;36;140` | 198 | inline code — **corrected**, see below |

`markup_code` is the one value that does **not** match the Xcode file. Apple
ships `#AA0D91` in that slot in both `Default (Dark)` and `Default (Light)` —
it is the *light* theme's keyword magenta, left unchanged in the dark theme.
On `#171717` it measures **2.71:1**, the only slot in Default+ failing WCAG AA.
It is corrected to the dark keyword magenta, which is what the light theme's
own value means: inline code renders in the keyword colour.

### Status

| Name | Xcode key | Hex | RGB | 256 | Role |
|---|---|---|---|---|---|
| `error` | `DVTScrollbarMarkerErrorColor` | `#F74A4A` | `247;74;74` | 203 | errors, deletions |
| `warning` | `DVTScrollbarMarkerWarningColor` | `#EFB759` | `239;183;89` | 215 | warnings, modifications |
| `success` | `DVTConsoleDebuggerPromptTextColor` | `#41B645` | `65;182;69` | 71 | success, additions |
| `info` | = declaration | `#35B0D8` | `53;176;216` | 74 | informational |
| `runtime_issue` | `DVTScrollbarMarkerRuntimeIssueColor` | `#A482FF` | `164;130;255` | 141 | runtime issues |
| `analyzer` | `DVTScrollbarMarkerAnalyzerColor` | `#675FFF` | `103;95;255` | 63 | analyzer findings |
| `breakpoint` | `DVTScrollbarMarkerBreakpointColor` | `#4A4AF7` | `74;74;247` | 63 | breakpoints |
| `neutral` | `DVTScrollbarMarkerDiffColor` | `#8E8E8E` | `142;142;142` | 245 | neutral diff marker |

## ANSI 0–15

Xcode has no ANSI concept, so this ramp is **designed**, not transcribed — but
every entry is a real Default+ colour, none invented. Ghostty, Claude Code's
`dark-ansi` base and `LSCOLORS` all key off it.

Normal and bright are genuinely distinct, so terminals must also set
`bold-is-bright = false` (ghostty) / `UseBrightBold = false` (Apple Terminal),
or bold changes hue as well as weight.

| # | Slot | Hex | Source | Contrast on bg |
|---|---|---|---|---|
| 0 | black | `#4C4C4C` | `base.invisibles` | 2.09:1 *(background tone)* |
| 1 | red | `#FC4651` | `syntax.string` | 5.24:1 |
| 2 | green | `#2EA85B` | `syntax.comment` | 5.86:1 |
| 3 | yellow | `#E09D65` | `syntax.attribute` | 7.84:1 |
| 4 | blue | `#4FA5FF` | `syntax.url` | 6.96:1 |
| 5 | magenta | `#F2248C` | `syntax.keyword` | 4.62:1 |
| 6 | cyan | `#35B0D8` | `syntax.declaration` | 7.13:1 |
| 7 | white | `#8E8E8E` | `base.muted_text` | 5.47:1 |
| 8 | bright black | `#515B70` | `base.selection_background` | 2.63:1 *(background tone)* |
| 9 | bright red | `#F74A4A` | `status.error` | 5.15:1 |
| 10 | bright green | `#41B645` | `status.success` | 6.83:1 |
| 11 | bright yellow | `#FFE76D` | `syntax.number` | 14.43:1 |
| 12 | bright blue | `#66DAFF` | `syntax.declaration_type` | 11.13:1 |
| 13 | bright magenta | `#AB64FF` | `syntax.system_member` | 5.12:1 |
| 14 | bright cyan | `#56D0B3` | `syntax.project_identifier` | 9.45:1 |
| 15 | bright white | `#FFFFFF` | `syntax.plain` | 17.93:1 |

Every slot except 0 and 8 — which are background tones and never carry text —
clears WCAG AA (4.5:1). Upstream's `bin/build.py --check` enforces this.

## The usage heat ramp

`claude/.claude/statusline.py` colours each usage percentage by how much of the
window is spent. Every band carries a colour, including the lowest — an earlier
version left anything under 60% grey, which meant the numbers only became
legible once they were already a problem.

| Usage | Colour | Hex |
|---|---|---|
| < 60% | `status.success` | `#41B645` |
| 60–79% | `syntax.number` | `#FFE76D` |
| 80–94% | `status.warning` | `#EFB759` |
| ≥ 95% | `status.error` | `#F74A4A` |

The number is bold, its label is `base.muted_text`, and the reset countdown is
`base.muted` — number, label, qualifier, in descending prominence.

## Derived shades

Default+ ships no diff table, so these follow one rule rather than taste: each
is its source composited over `background` at a fixed opacity. Row = 20%,
word-level highlight = 35%, muted accent = 50%. Upstream recomputes them in
`--check`; do not hand-tune.

| Name | Hex | RGB | Rule |
|---|---|---|---|
| `diff_added_bg` | `#1C3425` | `28;52;37` | `syntax.comment` at 20% |
| `diff_removed_bg` | `#452023` | `69;32;35` | `syntax.string` at 20% |
| `diff_moved_added_bg` | `#1D363E` | `29;54;62` | `syntax.declaration` at 20% |
| `diff_moved_removed_bg` | `#352645` | `53;38;69` | `syntax.system_member` at 20% |
| `diff_added_content_bg` | `#1F4A2F` | `31;74;47` | `syntax.comment` at 35% |
| `diff_removed_content_bg` | `#67272B` | `103;39;43` | `syntax.string` at 35% |
| `context_content_bg` | `#2F2F2F` | `47;47;47` | `base.muted_text` at 20% |
| `current_line_solid` | `#26262C` | `38;38;44` | `base.current_line` at 50% |
| `accent_muted` | `#266478` | `38;100;120` | `syntax.declaration` at 50% |
| `muted_green` | `#226039` | `34;96;57` | `syntax.comment` at 50% |
| `muted_red` | `#8A2E34` | `138;46;52` | `syntax.string` at 50% |
| `muted_yellow` | `#7C5A3E` | `124;90;62` | `syntax.attribute` at 50% |
| `note_title_bg` | `#1D363E` | `29;54;62` | = `diff_moved_added_bg` |

### Shimmer

Claude Code pairs each accent with a lighter "shimmer" twin for its spinner
gradient. Rule: **the colour 40% of the way toward `foreground`**. Recorded
here rather than left as orphan hexes inside the theme JSON.

| Name | Hex | Rule |
|---|---|---|
| `shimmer_blue` | `#86D0E8` | `syntax.declaration` 40% toward foreground |
| `shimmer_magenta` | `#F77CBA` | `syntax.keyword` 40% toward foreground |
| `shimmer_yellow` | `#FFF1A7` | `syntax.number` 40% toward foreground |
| `shimmer_orange` | `#FEBC8C` | `syntax.macro` 40% toward foreground |
| `shimmer_red` | `#FD9097` | `syntax.string` 40% toward foreground |
| `shimmer_green` | `#82CB9D` | `syntax.comment` 40% toward foreground |
| `shimmer_indigo` | `#95C9FF` | `syntax.url` 40% toward foreground |
| `shimmer_violet` | `#CDA2FF` | `syntax.system_member` 40% toward foreground |

## Where the copies live

Upstream is `~/Developer/default-plus`. Files marked *generated* are emitted by
its `bin/build.py`; re-copy rather than editing either end by hand.

| Tool | File | How it gets the palette |
|---|---|---|
| xcode | `xcode/…/FontAndColorThemes/Default+.xccolortheme` | the source of truth itself |
| ghostty | `ghostty/.config/ghostty/themes/Default+` | vendored, *generated* |
| tig | `tig/.config/tig/config` | vendored, *generated* — 256 indices, hand-picked |
| lazygit | `lazygit/.config/lazygit/config.yml` | `theme:` block vendored, *generated* |
| herdr | `herdr/.config/herdr/config.toml` | `[theme.custom]` vendored, *generated* |
| zsh | `zsh/.config/zsh/ls_colors.zsh` | vivid's filetype DB, palette substituted by role |
| zsh | `zsh/.zshrc` | prompt + `LSCOLORS`, inline |
| hunk | `hunk/.config/hunk/config.toml` | `[custom_theme]` vendored |
| vigia | `vigia/.config/vigia/theme` | vendored |
| opencode | `opencode/.config/opencode/themes/default-plus.json` | vendored |
| claude | `claude/.claude/themes/default-plus.json` | vendored |
| claude | `claude/.claude/statusline.py` | 8 constants, inline; see the heat ramp above |
| nvim | `nvim/.config/nvim/colors/default-plus.lua` | vendored from `default-plus-nvim` |
| bat | `bat/.config/bat/themes/default-plus.tmTheme` | hand-written here |
| sublime | `sublime/…/User/default-plus.sublime-color-scheme` | hand-written here |
| yazi | `yazi/.config/yazi/theme.toml` | hand-written here |
| tmux | `tmux/.config/tmux/tmux.conf` | hand-written here, inline |
| vademecum | `vademecum/.config/vademecum/theme.toml` | hand-written here, full 15-slot palette |
| rewind | `rewind/.config/rewind/theme.toml` | one line; rewind ships Default+ as a built-in |
| git | — | none; ANSI names only, no hex |
| holodeck | `holodeck/.config/holodeck/config.json` | **none — see the gap below** |

**holodeck is the one gap.** It selects a theme by name only, has no custom
theme support, and silently falls back on an unknown name — an invalid theme
still reports a clean run. It therefore stays on a built-in until a
`default-plus` theme is added to holodeck itself. Do not set it to
`"default-plus"` before then: that would look correct and render wrong.
