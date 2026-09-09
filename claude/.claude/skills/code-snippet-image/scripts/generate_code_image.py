#!/usr/bin/env python3
"""
Generate beautiful code snippet images with macOS-style window chrome.
Supports Swift syntax highlighting with a warm, professional color palette.
Optimized for retina/high-DPI displays.
"""

import argparse
import os
import shutil
import subprocess
import sys
from PIL import Image, ImageDraw, ImageFont
from pygments.lexers import SwiftLexer
from pygments.token import Token


# Color palette: warm, dark theme with orange accents
# Crail (#C15F3C), Pampas (#F4F3EE), Cloudy (#B1ADA1)
COLORS = {
    'background': '#1a1a1a',           # Rich dark background
    'window_chrome': '#2d2d2d',        # Slightly lighter chrome
    'orange_bg': '#C15F3C',            # Crail orange border
    
    # Traffic lights - orange theme
    'traffic_light_1': '#C15F3C',      # Crail orange
    'traffic_light_2': '#D4763F',      # Lighter orange
    'traffic_light_3': '#E89142',      # Warm orange-gold
    
    # Swift syntax colors - warm, professional palette
    # Keywords
    Token.Keyword: '#E89142',                    # Warm orange-gold for keywords
    Token.Keyword.Declaration: '#E89142',        # func, let, var, class, struct
    Token.Keyword.Constant: '#E89142',           # true, false, nil, _
    
    # Names and identifiers
    Token.Name: '#F4F3EE',                       # Off-white (Pampas) for names
    Token.Name.Variable: '#F4F3EE',              # Variable names
    Token.Name.Builtin: '#9DB4C0',               # Built-in types (Int, String, etc.)
    Token.Name.Builtin.Pseudo: '#9DB4C0',        # Built-in functions (print, reduce)
    Token.Name.Class: '#C15F3C',                 # Crail orange for classes
    Token.Name.Function: '#D4763F',              # Light orange for functions
    
    # Strings
    Token.String: '#87C38F',                     # Soft green for strings
    Token.Literal.String: '#87C38F',             # String literals
    Token.Literal.String.Double: '#87C38F',      # Double-quoted strings
    Token.Literal.String.Single: '#87C38F',      # Single-quoted strings
    Token.Literal.String.Interpol: '#E89142',    # String interpolation markers
    
    # Numbers
    Token.Number: '#9DB4C0',                     # Soft blue for numbers
    Token.Literal.Number: '#9DB4C0',             # Number literals
    Token.Literal.Number.Integer: '#9DB4C0',     # Integers
    Token.Literal.Number.Float: '#9DB4C0',       # Floats
    
    # Comments
    Token.Comment: '#B1ADA1',                    # Cloudy grey for comments
    Token.Comment.Single: '#B1ADA1',             # Single-line comments
    Token.Comment.Multiline: '#B1ADA1',          # Multi-line comments
    
    # Operators and punctuation
    Token.Operator: '#E89142',                   # Orange-gold for operators
    Token.Punctuation: '#F4F3EE',                # Off-white for punctuation
}


# Absolute paths to a monospace face, most-preferred first. PIL needs a real
# path or a font registered with the OS; bare names like "Menlo" do not resolve
# on Linux, so we look these up explicitly and fall back to fontconfig.
FONT_CANDIDATES = [
    '/System/Library/Fonts/Menlo.ttc',            # macOS
    '/System/Library/Fonts/Monaco.ttf',           # macOS
    '/Library/Fonts/Menlo.ttc',
    '/usr/share/fonts/liberation-mono-fonts/LiberationMono-Regular.ttf',
    '/usr/share/fonts/adwaita-mono-fonts/AdwaitaMono-Regular.ttf',
    '/usr/share/fonts/adobe-source-code-pro-fonts/SourceCodePro-Regular.otf',
    '/usr/share/fonts/dejavu-sans-mono-fonts/DejaVuSansMono.ttf',
    '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',       # Debian/Ubuntu
    '/usr/share/fonts/TTF/DejaVuSansMono.ttf',                   # Arch
]


def resolve_font_path(explicit=None):
    """Return a path to a usable monospace font, or exit with a clear message.

    Never falls back to PIL's bitmap default: that font ignores the requested
    size and renders unusably small.
    """
    if explicit:
        if os.path.isfile(explicit):
            return explicit
        print(f"Error: font not found: {explicit}", file=sys.stderr)
        sys.exit(1)

    for path in FONT_CANDIDATES:
        if os.path.isfile(path):
            return path

    fc_match = shutil.which("fc-match")
    if fc_match:
        try:
            out = subprocess.run(
                [fc_match, "-f", "%{file}", "monospace"],
                capture_output=True, text=True, check=True,
            ).stdout.strip()
            if out and os.path.isfile(out):
                return out
        except (OSError, subprocess.CalledProcessError):
            pass

    print(
        "Error: no monospace font found. Install one (macOS ships Menlo; on "
        "Linux try 'dnf install liberation-mono-fonts' or 'apt install "
        "fonts-liberation'), or pass --font /path/to/font.ttf",
        file=sys.stderr,
    )
    sys.exit(1)


def load_font(font_path, size):
    try:
        return ImageFont.truetype(font_path, size)
    except OSError:
        print(f"Error: could not load font: {font_path}", file=sys.stderr)
        sys.exit(1)


def tokenize_swift_code(code):
    """Tokenize Swift code using Pygments."""
    lexer = SwiftLexer()
    tokens = list(lexer.get_tokens(code))
    return tokens


def draw_traffic_lights(draw, x, y, radius=6, spacing=8):
    """Draw macOS-style traffic light buttons."""
    colors = [
        COLORS['traffic_light_1'],
        COLORS['traffic_light_2'], 
        COLORS['traffic_light_3']
    ]
    current_x = x
    
    for color in colors:
        # Draw circle
        draw.ellipse(
            [current_x, y, current_x + radius * 2, y + radius * 2],
            fill=color
        )
        current_x += radius * 2 + spacing


def calculate_image_dimensions(tokens, font, line_height, padding, chrome_height):
    """Calculate required image dimensions based on code content."""
    lines = []
    current_line = []
    
    for token_type, token_value in tokens:
        if '\n' in token_value:
            parts = token_value.split('\n')
            for i, part in enumerate(parts):
                if part:
                    current_line.append((token_type, part))
                if i < len(parts) - 1:
                    lines.append(current_line)
                    current_line = []
        else:
            current_line.append((token_type, token_value))
    
    if current_line:
        lines.append(current_line)
    
    # Calculate width. Use advance width (getlength), not the ink bounding box:
    # getbbox ignores leading/trailing whitespace, which would drop indentation.
    max_width = 0
    for line in lines:
        line_text = ''.join(token[1] for token in line)
        line_width = font.getlength(line_text)
        max_width = max(max_width, line_width)
    
    # Calculate dimensions (+1 to absorb the float text width truncation)
    width = int(max_width) + 1 + padding * 2
    height = chrome_height + len(lines) * line_height + padding * 2

    return width, height, lines


def render_code_image(code, output_path, font_path, with_border=True,
                      scale_factor=2, dpi=144):
    """
    Render code as an image with macOS-style window chrome.
    Warm, professional color palette. Optimized for retina/high-DPI displays.

    Args:
        code: Swift code string to render
        output_path: Path to save the output image
        font_path: Path to the monospace .ttf/.otf to render with
        with_border: Whether to include the orange border background
        scale_factor: Resolution multiplier for retina displays (2 = 2x retina, 3 = 3x)
        dpi: DPI setting for the output image (default: 144 for retina)
    """
    # Configuration (scaled for high DPI)
    font_size = 18 * scale_factor
    line_height = 28 * scale_factor
    padding = 30 * scale_factor
    chrome_height = 50 * scale_factor
    border_padding = (40 * scale_factor) if with_border else 0
    corner_radius = 10 * scale_factor
    traffic_light_radius = 6 * scale_factor
    traffic_light_spacing = 8 * scale_factor
    
    # Get font
    font = load_font(font_path, font_size)
    
    # Tokenize code
    tokens = tokenize_swift_code(code)
    
    # Calculate dimensions
    code_width, code_height, lines = calculate_image_dimensions(
        tokens, font, line_height, padding, chrome_height
    )
    
    # Create image with border if requested
    if with_border:
        total_width = code_width + border_padding * 2
        total_height = code_height + border_padding * 2
        img = Image.new('RGB', (total_width, total_height), COLORS['orange_bg'])
        
        # Create rounded rectangle for window with anti-aliasing
        window_img = Image.new('RGBA', (code_width, code_height), (0, 0, 0, 0))
        window_draw = ImageDraw.Draw(window_img)
        window_draw.rounded_rectangle(
            [0, 0, code_width, code_height],
            radius=corner_radius,
            fill=COLORS['background']
        )
        img.paste(window_img, (border_padding, border_padding), window_img)
        
        draw = ImageDraw.Draw(img)
        offset_x = border_padding
        offset_y = border_padding
    else:
        img = Image.new('RGB', (code_width, code_height), COLORS['background'])
        draw = ImageDraw.Draw(img)
        offset_x = 0
        offset_y = 0
    
    # Draw window chrome
    draw.rectangle(
        [offset_x, offset_y, offset_x + code_width, offset_y + chrome_height],
        fill=COLORS['window_chrome']
    )
    
    # Draw traffic lights
    draw_traffic_lights(
        draw, 
        offset_x + 20 * scale_factor, 
        offset_y + 20 * scale_factor,
        radius=traffic_light_radius,
        spacing=traffic_light_spacing
    )
    
    # Draw code
    y_position = offset_y + chrome_height + padding
    
    for line in lines:
        x_position = offset_x + padding
        
        for token_type, token_value in line:
            # Get color for token type
            color = COLORS.get(token_type, COLORS[Token.Name])
            
            # Draw text
            draw.text((x_position, y_position), token_value, font=font, fill=color)

            # Advance by the glyph advance width, not the ink box — otherwise
            # whitespace-only tokens (indentation, inter-token spaces) collapse.
            x_position += font.getlength(token_value)
        
        y_position += line_height
    
    # Save image with high quality and DPI metadata
    img.save(output_path, quality=100, dpi=(dpi, dpi), optimize=False)
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description='Generate code snippet images for Swift code with a warm color palette (optimized for retina displays)'
    )
    parser.add_argument(
        'code',
        nargs='?',
        help='Swift code to render (or use --file)'
    )
    parser.add_argument(
        '-f', '--file',
        help='Read code from file'
    )
    parser.add_argument(
        '-o', '--output',
        default='code_snippet.png',
        help='Output image path (default: code_snippet.png)'
    )
    parser.add_argument(
        '--no-border',
        action='store_true',
        help='Disable the orange border background'
    )
    parser.add_argument(
        '--font',
        help='Path to a monospace .ttf/.otf (default: auto-detect, '
             'then fontconfig)'
    )
    parser.add_argument(
        '--scale',
        type=int,
        default=2,
        choices=[1, 2, 3, 4],
        help='Resolution scale factor (1=normal, 2=retina 2x, 3=retina 3x, 4=ultra-high) (default: 2)'
    )
    parser.add_argument(
        '--dpi',
        type=int,
        default=144,
        help='DPI setting for output image (default: 144 for retina)'
    )
    
    args = parser.parse_args()
    
    # Get code from argument or file
    if args.file:
        with open(args.file, 'r') as f:
            code = f.read()
    elif args.code:
        code = args.code
    else:
        print("Error: Must provide code via argument or --file", file=sys.stderr)
        sys.exit(1)
    
    font_path = resolve_font_path(args.font)

    # Generate image
    output_path = render_code_image(
        code,
        args.output,
        font_path,
        with_border=not args.no_border,
        scale_factor=args.scale,
        dpi=args.dpi
    )
    print(f"Code snippet image saved to: {output_path}")
    print(f"Resolution: {args.scale}x scale, {args.dpi} DPI")
    print(f"Color palette: warm, professional")


if __name__ == '__main__':
    main()
