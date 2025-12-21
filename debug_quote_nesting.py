#!/usr/bin/env python3
"""Debug script to trace quote nesting context."""

from lxml import etree
from writers.common import parse_tei
from writers.core.traverser import TEITraverser
from writers.renderers.text_renderer import TextRenderer

# Monkey-patch to add debug output
original_render_paragraph = TextRenderer.render_paragraph

def debug_render_paragraph(self, elem, context, traverser):
    text = self._extract_text_with_emphasis(elem, context).strip()
    if text:
        print(f"[DEBUG] Paragraph:")
        print(f"  indent_level={context.indent_level}")
        print(f"  current_indent='{context.current_indent}' (len={len(context.current_indent)})")
        print(f"  effective_width={self.line_width - len(context.current_indent)}")
        print(f"  text preview={text[:50]}...")
    return original_render_paragraph(self, elem, context, traverser)

TextRenderer.render_paragraph = debug_render_paragraph

# Now run the conversion
xml_content = '''<div xmlns="http://www.tei-c.org/ns/1.0">
<quote>
<p>First level quote text here that should wrap at column 68.</p>

<quote>
<p>Second level quote text here that should wrap at column 64.</p>

<quote>
<p>Third level quote text here that should wrap at column 60.</p>
</quote>
</quote>

<p>Back to first level quote wrapping at column 68.</p>
</quote>
</div>'''

doc = etree.fromstring(xml_content)
renderer = TextRenderer(line_width=72)
traverser = TEITraverser(renderer)

from writers.core.context import RenderContext
context = RenderContext(parent_tag='body')

print("=" * 72)
result = traverser.traverse_element(doc, context)
print("=" * 72)
print("\nActual output:")
print("=" * 72)
if isinstance(result, list):
    for line in result:
        print(f"|{line}|")
else:
    print(result)
