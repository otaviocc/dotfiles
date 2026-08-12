---
name: jellyfin-library-cards
description: Generate Jellyfin library card/collection artwork -- bold rounded text with a purple-to-cyan gradient on a transparent background, matching Otávio's existing card set ("4K Movies", "Collections", "Movies"). Use whenever he asks for a new Jellyfin library card, library image, library artwork, or collection thumbnail, or mentions wanting more cards "in the same style" as his existing ones. Deterministic Python/Pillow rendering -- same input always produces the same pixel output, no AI image generation involved.
---

# Jellyfin Library Cards

Generates title-card artwork for Jellyfin libraries/collections: bold rounded
text, purple-to-cyan horizontal gradient, transparent background. Reverse-
engineered from Otávio's existing card set to match exactly.

## Style spec (reverse-engineered from reference cards)

- **Font**: Fredoka, SemiBold (variable weight axis = 600). Bundled at
  `assets/Fredoka.ttf` — no network access needed at runtime.
- **Canvas**: 1800×1000 px, fully transparent background (RGBA).
- **Gradient**: linear, left-to-right, mapped across the *text's own bounding
  box* (not the canvas) — so short and long strings both go fully purple
  at their leftmost pixel to fully cyan at their rightmost pixel.
  - Start (left): `#AA5CC3` (purple)
  - End (right): `#00A4DC` (cyan — Jellyfin's own brand blue)
- **Layout**: text is centered on the canvas, auto-sized to the largest
  font size that fits within a horizontal margin (default 10% of width on
  each side) and a vertical cap (60% of height).

## Usage

Run the bundled script directly — don't reimplement this logic inline:

```bash
python3 scripts/generate_card.py "TV Shows" -o /path/to/output/tv_shows.png
```

Generate a whole batch in one go:

```bash
for name in "TV Shows" "Anime" "Home Videos" "Kids"; do
  slug=$(echo "$name" | tr '[:upper:] ' '[:lower:]_')
  python3 scripts/generate_card.py "$name" \
    -o "/path/to/output/${slug}.png"
done
```

Always write output to a path the user specifies (e.g. `~/Desktop/`) and
report the saved file path so the user can find it.

## Options

| Flag | Default | Purpose |
|---|---|---|
| `-o, --output` | *(required)* | Output PNG path |
| `--width` | `1800` | Canvas width in px |
| `--height` | `1000` | Canvas height in px |
| `--font` | bundled Fredoka.ttf | Path to an alternate .ttf/.otf |
| `--weight` | `600` | Variable weight axis (Fredoka supports ~300–700) |
| `--start-color` | `#AA5CC3` | Hex color at the left edge of the text |
| `--end-color` | `#00A4DC` | Hex color at the right edge of the text |
| `--margin-frac` | `0.10` | Horizontal margin as a fraction of width per side |

## Notes

- If the user wants a different look (color pair, font, diagonal gradient,
  icon, etc.), adjust the script's parameters rather than generating the
  image any other way — the whole point of this skill is deterministic,
  repeatable output.
- If asked to match a *new* reference image style, sample its colors and
  identify its font the same way this skill's colors/font were derived:
  sample pixel colors at the text's left/right edges, and test-render
  candidate open-source fonts until the glyph shapes match. Then extend or
  fork this script rather than hand-drawing text.

## Dependencies

- **Pillow** (`pip install Pillow`) — image rendering
