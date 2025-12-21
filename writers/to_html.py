"""
to_html.py - Convert TEI to HTML

This module provides a backward-compatible API that wraps the new
HTMLRenderer implementation. The old implementation is preserved
in to_html_old.py for reference.
"""

from datetime import datetime
import os
import glob

from .common import parse_tei
from .renderers.html_renderer import HTMLRenderer
from .core.traverser import TEITraverser


def convert(tei_file, output_file, css_file=None):
    """
    Convert TEI XML to HTML.

    Args:
        tei_file: Path to TEI XML input file
        output_file: Path to HTML output file
        css_file: Optional path to external CSS file (default: auto-detect or use embedded styles)
    """
    print(f"[INFO] to_html.py run at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Auto-detect CSS file in same directory if not specified
    if css_file is None:
        input_dir = os.path.dirname(os.path.abspath(tei_file))
        css_files = glob.glob(os.path.join(input_dir, '*.css'))
        if css_files:
            css_file = css_files[0]  # Use first CSS file found
            print(f"Auto-detected CSS file: {os.path.basename(css_file)}")

    # Parse the TEI document
    doc = parse_tei(tei_file)

    # Create renderer and traverser
    renderer = HTMLRenderer(css_file=css_file)
    traverser = TEITraverser(renderer)

    # Render the document
    html = traverser.traverse_document(doc)

    # Write output
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"HTML conversion complete: {output_file}")
