import zipfile
from pathlib import Path
import io
import sys
import os

import pytest

from writers import to_html, to_epub

SAMPLE_TEI = '''<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt>
        <title>Sample</title>
      </titleStmt>
      <publicationStmt>
        <p>None</p>
      </publicationStmt>
      <sourceDesc>
        <p>Generated</p>
      </sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <body>
      <div>
        <head>Verse</head>
        <lg>
          <l>DOUBLEDAY, PAGE &amp; COMPANY</l>
          <l>P. F. COLLIER &amp; SON COMPANY</l>
        </lg>
      </div>
    </body>
  </text>
</TEI>
'''


def test_html_escape(tmp_path):
    tei_path = tmp_path / "sample_verse.xml"
    html_out = tmp_path / "out.html"
    tei_path.write_text(SAMPLE_TEI, encoding="utf-8")

    # Run HTML conversion
    to_html.convert(str(tei_path), str(html_out))

    content = html_out.read_text(encoding="utf-8")

    # Ensure the entity is present as &amp; in output
    assert "&amp;" in content, "Expected '&amp;' in produced HTML but not found"


def test_epub_escape(tmp_path):
    tei_path = tmp_path / "sample_verse.xml"
    epub_out = tmp_path / "out.epub"
    tei_path.write_text(SAMPLE_TEI, encoding="utf-8")

    # Run EPUB conversion
    to_epub.convert(str(tei_path), str(epub_out))

    # Inspect EPUB contents for XHTML files and check for &amp;
    found = False
    with zipfile.ZipFile(str(epub_out), 'r') as z:
        for name in z.namelist():
            if name.lower().endswith('.xhtml') or name.lower().endswith('.html'):
                data = z.read(name).decode('utf-8')
                if '&amp;' in data:
                    found = True
                    break

    assert found, "Expected '&amp;' in EPUB XHTML content but not found"
