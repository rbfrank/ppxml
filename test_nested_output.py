#!/usr/bin/env python3
"""
Quick script to visualize nested blockquote output.
"""

from lxml import etree
from writers.core.context import RenderContext
from writers.core.traverser import TEITraverser
from writers.renderers.text_renderer import TextRenderer

# Create a long paragraph to test wrapping
long_text = ' '.join(['word'] * 20)  # Long enough to wrap
xml = f'''<quote xmlns="http://www.tei-c.org/ns/1.0">
    <quote>
        <p>{long_text}</p>
    </quote>
</quote>'''

elem = etree.fromstring(xml)
renderer = TextRenderer(line_width=72)
traverser = TEITraverser(renderer)
context = RenderContext(parent_tag='div')

result = renderer.render_quote(elem, context, traverser)

print("=" * 72)
print("Nested blockquote output (72 char ruler above):")
print("=" * 72)
for i, line in enumerate(result):
    # Show line number, length, and content
    print(f"{i:2d} [{len(line):2d}] |{line}|")
print("=" * 72)
