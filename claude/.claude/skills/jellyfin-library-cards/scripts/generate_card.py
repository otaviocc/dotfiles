#!/usr/bin/env python3
"""
Generate Jellyfin-style library card artwork: bold rounded text with a
purple-to-cyan horizontal gradient, on a transparent background.

This is a deterministic, code-only renderer (no AI image generation) so the
same input always produces pixel-identical output.

Usage:
    python3 generate_card.py "4K Movies" -o out/4k_movies.png
    python3 generate_card.py "TV Shows" -o out/tv_shows.png --width 1800 --height 1000
    python3 generate_card.py "Anime" -o out/anime.png --start-color "#AA5CC3" --end-color "#00A4DC"

Defaults were reverse-engineered from reference Jellyfin library cards:
  - Font: Fredoka (SemiBold, wght=600), bundled in ../assets/Fredoka.ttf
  - Canvas: 1800x1000, transparent background
  - Gradient: left-to-right, linear, mapped across the TEXT's own bounding
    box (not the canvas) -- so short and long strings both start fully
    purple and end fully cyan.
  - Colors: #AA5CC3 (purple) -> #00A4DC (cyan, Jellyfin's brand blue)
  - Horizontal text margin: ~10% of canvas width on each side.
  - Font size: a fixed 300 (--font-size), shrunk only when the name is too
    long to fit the available width. A shared size is what makes a set of
    cards look like a set; sizing each name to fill the width instead would
    render "Kids" nearly three times taller than "Collections".
"""

import argparse
import os
import sys
from PIL import Image, ImageDraw, ImageFont

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_FONT = os.path.join(SCRIPT_DIR, "..", "assets", "Fredoka.ttf")

DEFAULT_WIDTH = 1800
DEFAULT_HEIGHT = 1000
DEFAULT_START_COLOR = "#AA5CC3"  # purple
DEFAULT_END_COLOR = "#00A4DC"    # Jellyfin brand cyan
DEFAULT_WEIGHT = 600             # Fredoka SemiBold
DEFAULT_MARGIN_FRAC = 0.10       # horizontal margin as fraction of width
DEFAULT_FONT_SIZE = 300          # shared across a card set; see fit_font_size


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        raise ValueError(f"Invalid hex color: {hex_color}")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def load_font(font_path: str, size: int, weight: int) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(font_path, size)
    try:
        font.set_variation_by_axes([weight])
    except Exception:
        # Non-variable font fallback -- ignore, use as-is.
        pass
    return font


def fit_font_size(
    text: str,
    font_path: str,
    weight: int,
    max_width: int,
    max_height: int,
    max_size: int = DEFAULT_FONT_SIZE,
    min_size: int = 20,
) -> ImageFont.FreeTypeFont:
    """Binary-search the largest font size <= max_size whose text still fits.

    The cap is what keeps a card set consistent: every name renders at the
    same size unless it is too long for the canvas, in which case it shrinks
    just enough to fit. Fitting each name to the full available width instead
    would tie glyph size to name length -- "Kids" would come out nearly three
    times taller than "Collections".

    Width is the advance width and height comes from the font's own
    ascent/descent, so neither depends on which glyphs a name happens to use.
    """
    lo, hi = min_size, max_size
    best_font = None

    dummy_img = Image.new("RGBA", (10, 10))
    draw = ImageDraw.Draw(dummy_img)

    while lo <= hi:
        mid = (lo + hi) // 2
        font = load_font(font_path, mid, weight)
        ascent, descent = font.getmetrics()
        if draw.textlength(text, font=font) <= max_width \
                and ascent + descent <= max_height:
            best_font = font
            lo = mid + 1
        else:
            hi = mid - 1

    if best_font is None:
        raise ValueError("Could not fit text at any size >= min_size")
    return best_font


def make_horizontal_gradient(width: int, height: int, start_rgb, end_rgb) -> Image.Image:
    """Linear left-to-right RGB gradient, width x height, fully opaque."""
    gradient = Image.new("RGB", (width, 1))
    for x in range(width):
        t = x / max(width - 1, 1)
        r = round(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * t)
        g = round(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * t)
        b = round(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * t)
        gradient.putpixel((x, 0), (r, g, b))
    return gradient.resize((width, height))


def generate_card(
    text: str,
    output_path: str,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    font_path: str = DEFAULT_FONT,
    weight: int = DEFAULT_WEIGHT,
    start_color: str = DEFAULT_START_COLOR,
    end_color: str = DEFAULT_END_COLOR,
    margin_frac: float = DEFAULT_MARGIN_FRAC,
    font_size: int = DEFAULT_FONT_SIZE,
) -> str:
    start_rgb = hex_to_rgb(start_color)
    end_rgb = hex_to_rgb(end_color)

    margin_x = int(width * margin_frac)
    max_text_w = width - 2 * margin_x
    max_text_h = int(height * 0.6)  # keep generous vertical breathing room

    font = fit_font_size(text, font_path, weight, max_text_w, max_text_h,
                         font_size)

    # Draw the mask on a full-size canvas, positioned by the font's own metrics
    # ("mm" centres the advance width and the ascent/descent box). Centring on
    # the ink box instead would let a descender or a missing cap shift the
    # baseline from one card to the next.
    mask_img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    mask_draw = ImageDraw.Draw(mask_img)
    mask_draw.text((width // 2, height // 2), text, font=font,
                   fill=(0, 0, 0, 255), anchor="mm")
    alpha = mask_img.split()[3]

    ink = alpha.getbbox()
    if ink is None:
        raise ValueError(f"{text!r} renders no visible glyphs")

    # Gradient still spans the TEXT's own ink box, so whatever the name's
    # length its leftmost pixel is fully start_color and its rightmost fully
    # end_color.
    gradient = make_horizontal_gradient(ink[2] - ink[0], ink[3] - ink[1],
                                        start_rgb, end_rgb)
    gradient_rgba = gradient.convert("RGBA")
    gradient_rgba.putalpha(alpha.crop(ink))

    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    canvas.alpha_composite(gradient_rgba, (ink[0], ink[1]))

    os.makedirs(os.path.dirname(os.path.abspath(output_path)) or ".", exist_ok=True)
    canvas.save(output_path)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Generate a Jellyfin-style library card image.")
    parser.add_argument("text", help="Library name to render, e.g. '4K Movies'")
    parser.add_argument("-o", "--output", required=True, help="Output PNG path")
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    parser.add_argument("--font", default=DEFAULT_FONT, help="Path to a .ttf/.otf font")
    parser.add_argument("--weight", type=int, default=DEFAULT_WEIGHT,
                         help="Variable font weight axis value (Fredoka: 300-700)")
    parser.add_argument("--start-color", default=DEFAULT_START_COLOR, help="Hex color, left side")
    parser.add_argument("--end-color", default=DEFAULT_END_COLOR, help="Hex color, right side")
    parser.add_argument("--margin-frac", type=float, default=DEFAULT_MARGIN_FRAC,
                         help="Horizontal margin as a fraction of width (each side)")
    parser.add_argument("--font-size", type=int, default=DEFAULT_FONT_SIZE,
                         help="Font size shared across a card set; a name too "
                              "long for the canvas shrinks below it "
                              f"(default: {DEFAULT_FONT_SIZE})")
    args = parser.parse_args()

    try:
        out = generate_card(
            text=args.text,
            output_path=args.output,
            width=args.width,
            height=args.height,
            font_path=args.font,
            weight=args.weight,
            start_color=args.start_color,
            end_color=args.end_color,
            margin_frac=args.margin_frac,
            font_size=args.font_size,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        if "fit" in str(exc).lower():
            print("  try a larger --width or a smaller --margin-frac",
                  file=sys.stderr)
        sys.exit(1)
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
