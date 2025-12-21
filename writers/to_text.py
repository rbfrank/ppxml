"""
to_text.py - Convert TEI to plain text with wrapping

This module provides a backward-compatible API that wraps the new
TextRenderer implementation. The old implementation is preserved
in to_text_old.py for reference.
"""

from .common import parse_tei
from .renderers.text_renderer import TextRenderer
from .core.traverser import TEITraverser


def convert(tei_file, output_file, line_width=72):
    """
    Convert TEI XML to plain text with wrapping.

    Args:
        tei_file: Path to TEI XML input file
        output_file: Path to text output file
        line_width: Width for line wrapping (default 72)
    """
    # Parse the TEI document
    doc = parse_tei(tei_file)

    # Create renderer and traverser
    renderer = TextRenderer(line_width=line_width)
    traverser = TEITraverser(renderer)

    # Render the document
    result = traverser.traverse_document(doc)

    # Convert result to lines
    if isinstance(result, str):
        output_lines = result.split('\n')
    elif isinstance(result, list):
        # Flatten nested lists and convert to strings
        output_lines = []
        for item in result:
            if isinstance(item, list):
                output_lines.extend(str(line) for line in item)
            else:
                output_lines.append(str(item))
    else:
        output_lines = [str(result)]

    # Write output
    with open(output_file, 'w', encoding='utf-8') as f:
        # Convert non-breaking spaces to regular spaces before writing
        output_text = '\n'.join(output_lines)
        output_text = output_text.replace('\xa0', ' ')  # Replace non-breaking spaces
        f.write(output_text)
        if output_lines:
            f.write('\n')

    print(f"Text conversion complete: {output_file}")
