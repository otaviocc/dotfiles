---
name: code-snippet-image
description: Generate code snippet images with syntax highlighting for 220+ languages - a macOS-style window on a colored, gradient, or image background. Use when the user asks to create, generate, or convert code into a shareable image, or wants a visual representation of code for documentation, presentations, or social media.
---

# Code Snippet Image Generator

Renders a code snippet to a PNG or SVG using `snapcode`, a Rust binary. Defaults
to the warm palette this skill has always used: dark window, orange field,
traffic lights, 2x retina.

## Quick Start

```bash
# From a file
snapcode snippet.swift -o ~/Desktop/snippet.png

# From a string, via stdin
printf 'let x = 1\n' | snapcode - --lang swift -o ~/Desktop/snippet.png
```

## Workflow

When the user requests a code snippet image:

1. Write the code to a temp file with the right extension — `/tmp/snippet.swift`,
   `/tmp/snippet.rs`. The extension drives language detection, so this is
   preferable to piping.
2. Run `snapcode /tmp/snippet.swift -o <output>.png`.
3. Tell the user the output path.

Use `--lang` only when the language cannot be inferred from the filename.

## Options

| Flag | Default | Purpose |
|---|---|---|
| `-o, --output` | input name + `.png` | Output path; `.svg` extension emits SVG, `-` writes stdout |
| `--lang` | detected | Language override (`snapcode languages` lists them) |
| `--theme` | `warm` | Window chrome: `warm`, `midnight`, `paper` |
| `--syntax-theme` | `warm` | Token colors; 30+ bundled (`snapcode themes`) |
| `--scale` | `2` | 1 normal, 2 retina, 3+ print |
| `--dpi` | `144` | DPI metadata written into the PNG |
| `--bg` | theme | Color, `linear:<angle>:<c1>,<c2>`, `radial:<c1>,<c2>`, or an image path |
| `--line-numbers` | off | Show a gutter |
| `--highlight-lines` | — | e.g. `3-5,9` — emphasize those, dim the rest |
| `--diff` | off | Render leading `+`/`-` as diff backgrounds |
| `--title` | filename | Titlebar text; `--no-titlebar` removes the bar |
| `--copy` | off | Also copy the image to the clipboard |
| `--no-shadow`, `--border`, `--padding`, `--margin`, `--radius` | | Window geometry |

Run `snapcode --help` for the full list.

## Common Recipes

```bash
# Emphasize the lines being discussed
snapcode api.swift --line-numbers --highlight-lines 12-18 -o out.png

# A diff, on the light theme
snapcode change.diff --diff --theme paper --line-numbers -o out.png

# Gradient background, no titlebar, straight to the clipboard
snapcode snippet.rs --bg 'linear:135:#1e3a8a,#701a75' --no-titlebar --copy -o out.png

# Vector output for a slide deck
snapcode snippet.ts -o out.svg
```

## Quality Guide

| Setting | Use case |
|---|---|
| `--scale 1 --dpi 72` | Web thumbnails, quick preview |
| `--scale 2` (default) | Most uses: retina displays, presentations, social |
| `--scale 3 --dpi 216` | Large format, high-res displays |
| SVG output | Slides and docs where it may be scaled arbitrarily |

## Interactive Mode

If the user wants to tune the look rather than specify it, suggest
`snapcode tui <file>`: a settings form with a live preview in the terminal, in
the colors of the theme being edited. Theme, syntax theme, and language open a
searchable list (`enter`); everything else steps with left/right. Pressing `p`
quits and prints the equivalent command line.

## Notes

- 220+ languages via `syntect`, detected from the file extension.
- The font is embedded in the binary, so output is pixel-identical across
  machines. `--font "Family"` uses a system font instead.
- Image backgrounds are not embedded in SVG output; snapcode says so when it
  drops one.

## Dependencies

`snapcode` on `PATH`. If it is missing, build it:

```bash
cargo install --path ~/Developer/snapcode/crates/snapcode-cli
```
