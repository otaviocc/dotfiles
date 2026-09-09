#!/usr/bin/env python3
"""
Generate beautiful code snippet images with macOS-style window chrome.
Supports Swift syntax highlighting with a warm, professional color palette.
Optimized for retina/high-DPI displays.
"""

import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from pygments import highlight
from pygments.lexers import SwiftLexer
from pygments.token import Token
import argparse


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


def get_font(size, bold=False):
    """Get font, trying multiple common system fonts."""
    font_names = [
        'Menlo',
        'Monaco', 
        'Courier New',
        'DejaVuSansMono',
        'LiberationMono-Regular',
        'FreeMono'
    ]
    
    for font_name in font_names:
        try:
            if bold:
                return ImageFont.truetype(font_name + '-Bold', size)
            return ImageFont.truetype(font_name, size)
        except:
            continue
    
    # Fallback to default font
    return ImageFont.load_default()


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
    
    # Calculate width
    max_width = 0
    for line in lines:
        line_text = ''.join(token[1] for token in line)
        bbox = font.getbbox(line_text)
        line_width = bbox[2] - bbox[0]
        max_width = max(max_width, line_width)
    
    # Calculate dimensions
    width = max_width + padding * 2
    height = chrome_height + len(lines) * line_height + padding * 2
    
    return width, height, lines


def render_code_image(code, output_path, with_border=True, scale_factor=2, dpi=144):
    """
    Render code as an image with macOS-style window chrome.
    Warm, professional color palette. Optimized for retina/high-DPI displays.

    Args:
        code: Swift code string to render
        output_path: Path to save the output image
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
    font = get_font(font_size)
    
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
            
            # Move x position
            bbox = font.getbbox(token_value)
            x_position += bbox[2] - bbox[0]
        
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
    
    # Generate image
    output_path = render_code_image(
        code, 
        args.output, 
        with_border=not args.no_border,
        scale_factor=args.scale,
        dpi=args.dpi
    )
    print(f"Code snippet image saved to: {output_path}")
    print(f"Resolution: {args.scale}x scale, {args.dpi} DPI")
    print(f"Color palette: warm, professional")


if __name__ == '__main__':
    main()
