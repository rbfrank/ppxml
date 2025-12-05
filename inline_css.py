#!/usr/bin/env python3

"""
inline_css.py - Replace CSS <link> with inline <style> block

Takes an HTML file with external CSS link and inlines the CSS.

Usage:
    python inline_css.py mycss.css myfile.html
    
This will:
1. Read the CSS file
2. Find the <link> tag pointing to that CSS file in the HTML
3. Replace it with a <style> block containing the CSS
4. Overwrite the HTML file with the inlined version
"""

import sys
import os
import re

def inline_css(css_file, html_file):
    """
    Inline CSS from css_file into html_file.
    
    Args:
        css_file: Path to CSS file
        html_file: Path to HTML file to modify
    """
    # Check files exist
    if not os.path.exists(css_file):
        print(f"Error: CSS file not found: {css_file}")
        sys.exit(1)
    
    if not os.path.exists(html_file):
        print(f"Error: HTML file not found: {html_file}")
        sys.exit(1)
    
    # Read CSS file
    with open(css_file, 'r', encoding='utf-8') as f:
        css_content = f.read()
    
    # Read HTML file
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Get just the filename (not path) for matching the link tag
    css_filename = os.path.basename(css_file)
    
    # Find and replace the link tag
    # Matches: <link rel="stylesheet" href="mycss.css">
    link_pattern = rf'<link\s+rel="stylesheet"\s+href="{re.escape(css_filename)}">'
    
    if not re.search(link_pattern, html_content):
        print(f"Error: Could not find <link> tag for {css_filename} in {html_file}")
        print("Make sure the HTML file has a link tag like:")
        print(f'  <link rel="stylesheet" href="{css_filename}">')
        sys.exit(1)
    
    # Create style block
    style_block = f'<style>\n{css_content}\n  </style>'
    
    # Replace link with style block
    html_content = re.sub(link_pattern, style_block, html_content)
    
    # Write back to HTML file
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Successfully inlined {css_file} into {html_file}")

def main():
    if len(sys.argv) != 3:
        print("Usage: python inline_css.py <css_file> <html_file>")
        print("")
        print("Example:")
        print("  python inline_css.py mystyles.css book.html")
        print("")
        print("This will replace the <link> tag in the HTML file")
        print("with an inline <style> block containing the CSS.")
        sys.exit(1)
    
    css_file = sys.argv[1]
    html_file = sys.argv[2]
    
    inline_css(css_file, html_file)

if __name__ == '__main__':
    main()

