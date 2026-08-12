---
name: code-snippet-image
description: Generate macOS-style code snippet images with Swift syntax highlighting. Warm color palette with a dark background, window chrome, and traffic lights. Use when the user asks to create, generate, or convert code into a shareable image, or wants a visual representation of Swift code for documentation, presentations, or social media.
---

# Code Snippet Image Generator

Generate shareable code snippet images with macOS-style window chrome and Swift
syntax highlighting. Warm color palette on a dark background, optimized for
retina and high-DPI displays.

## Quick Start

```bash
# From a string
python3 scripts/generate_code_image.py 'print("Hello, World!")' -o output.png

# From a file
python3 scripts/generate_code_image.py -f code.swift -o output.png
```

The script produces a PNG with:
- 2x retina resolution by default (144 DPI)
- macOS-style window chrome with traffic lights
- Dark background (#1a1a1a) and warm syntax colors
- Automatic sizing to fit the code content

## Workflow

When the user requests a code snippet image:

1. Extract or receive the Swift code from the request
2. Save it to a temporary file or pass it as a string
3. Run the script:
   ```bash
   # Retina (recommended)
   python3 scripts/generate_code_image.py -f /tmp/snippet.swift -o ~/Desktop/snippet.png --scale 2

   # Ultra-high quality
   python3 scripts/generate_code_image.py -f /tmp/snippet.swift -o ~/Desktop/snippet.png --scale 3
   ```
4. Tell the user the output path

## Script Options

| Flag | Default | Purpose |
|---|---|---|
| `code` (positional) | — | Swift code as a string |
| `-f, --file` | — | Read code from a file instead |
| `-o, --output` | `code_snippet.png` | Output PNG path |
| `--no-border` | off | Disable the orange border background |
| `--scale` | `2` | Resolution multiplier: 1 normal, 2 retina 2x, 3 retina 3x, 4 ultra |
| `--dpi` | `144` | DPI metadata written into the PNG |

## Quality Guide

| Setting | Use case | Typical size |
|---|---|---|
| `--scale 1 --dpi 72` | Web thumbnails, quick preview | ~25 KB |
| `--scale 2` (default) | Most uses, retina displays, presentations | ~50–60 KB |
| `--scale 3 --dpi 216` | Ultra-high-res displays, print | ~90–100 KB |
| `--scale 4 --dpi 288` | Professional print, large-format | ~150 KB+ |

## Dependencies

- **Pillow** (`pip install Pillow`) — image rendering
- **Pygments** (`pip install Pygments`) — Swift tokenization

## Limitations

- Swift syntax highlighting only (hardcoded to Pygments' `SwiftLexer`)
- Fixed dark color theme; no light mode
- Uses system monospace fonts (Menlo, Monaco, Courier New, or fallback)
