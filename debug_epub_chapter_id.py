#!/usr/bin/env python3
"""Debug script to check chapter with ID rendering."""

from lxml import etree
from writers.renderers.epub_renderer import EPUBRenderer

xml = '''<div xmlns="http://www.tei-c.org/ns/1.0" xml:id="ch1">
    <head>Chapter One</head>
    <p>Content.</p>
</div>'''

elem = etree.fromstring(xml)
renderer = EPUBRenderer()
result = renderer.render_chapter(elem, 'Book Title')

print("=" * 72)
print("Chapter output:")
print("=" * 72)
print(result)
print("=" * 72)

# Check what we're looking for
if '<h2 id="ch1">Chapter One</h2>' in result:
    print("✓ Found expected heading with ID")
else:
    print("✗ Expected heading not found")
    # Show what h2 tags we have
    import re
    h2_tags = re.findall(r'<h2[^>]*>.*?</h2>', result)
    print(f"Found h2 tags: {h2_tags}")
