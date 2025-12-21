#!/usr/bin/env python3
"""Debug script to check xml:id attribute access."""

from lxml import etree

xml = '''<div xmlns="http://www.tei-c.org/ns/1.0" xml:id="ch1">
    <head>Chapter One</head>
    <p>Content.</p>
</div>'''

elem = etree.fromstring(xml)

print("Element tag:", elem.tag)
print("Element attributes:", elem.attrib)
print()

# Try different ways to get xml:id
print("Method 1 - using '{http://www.w3.org/XML/1998/namespace}id':")
id1 = elem.get('{http://www.w3.org/XML/1998/namespace}id', '')
print(f"  Result: '{id1}'")
print()

print("Method 2 - using '{http://www.w3.org/1998/namespace}id':")
id2 = elem.get('{http://www.w3.org/1998/namespace}id', '')
print(f"  Result: '{id2}'")
print()

print("Method 3 - using QName:")
from lxml.etree import QName
xml_ns = "http://www.w3.org/XML/1998/namespace"
qname = QName(xml_ns, 'id')
id3 = elem.get(qname, '')
print(f"  Result: '{id3}'")
print()

print("All attributes with full namespace:")
for key, value in elem.attrib.items():
    print(f"  {key} = {value}")
