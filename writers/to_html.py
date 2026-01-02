"""
to_html.py - Convert TEI to HTML

This module provides a backward-compatible API that wraps the new
HTMLRenderer implementation. The old implementation is preserved
in to_html_old.py for reference.
"""

from datetime import datetime
import os
import tempfile

from .common import parse_tei, find_css_files, read_css_files, filter_css_for_format
from .renderers.html_renderer import HTMLRenderer
from .core.traverser import TEITraverser


def convert(tei_file, output_file, css_file=None):
    """
    Convert TEI XML to HTML.

    Args:
        tei_file: Path to TEI XML input file
        output_file: Path to HTML output file
        css_file: Optional path to external CSS file (default: auto-detect from css/html/)
    """
    # Discover CSS files if not explicitly provided
    temp_css_file = None
    if css_file is None:
        css_paths = find_css_files(tei_file, 'html')
        if css_paths:
            raw_css_content = read_css_files(css_paths)
            # Filter CSS for HTML format (process @html/@epub/@both directives)
            css_content = filter_css_for_format(raw_css_content, 'html')
            # Write combined CSS to temp file for HTMLRenderer
            temp_css = tempfile.NamedTemporaryFile(mode='w', suffix='.css',
                                                   delete=False, encoding='utf-8')
            temp_css.write(css_content)
            temp_css.close()
            temp_css_file = temp_css.name
            css_file = temp_css_file
            print(f"Auto-detected CSS files: {', '.join([os.path.basename(p) for p in css_paths])}")

    try:
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
    finally:
        # Clean up temp file if created
        if temp_css_file and os.path.exists(temp_css_file):
            os.unlink(temp_css_file)
