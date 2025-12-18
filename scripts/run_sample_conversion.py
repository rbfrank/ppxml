#!/usr/bin/env python3
"""Simple helper to run sample conversions without pytest.

Usage:
  python scripts/run_sample_conversion.py --html   # produce out.html and report
  python scripts/run_sample_conversion.py --epub   # produce out.epub and report
  python scripts/run_sample_conversion.py --both   # run both

Runs from the repository root so `from writers import to_html` should work.
"""
import argparse
import tempfile
from pathlib import Path
import zipfile

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


def run_html(sample_path: Path, out_path: Path):
    from writers import to_html
    to_html.convert(str(sample_path), str(out_path))
    content = out_path.read_text(encoding='utf-8')
    ok = '&amp;' in content
    print(f"HTML -> {out_path} contains '&amp;': {ok}")
    if not ok:
        # show a short snippet around the lines with '&'
        for i, line in enumerate(content.splitlines(), 1):
            if '&' in line and '&amp;' not in line:
                print(f"  Line {i}: {line}")


def run_epub(sample_path: Path, out_path: Path):
    from writers import to_epub
    to_epub.convert(str(sample_path), str(out_path))
    found = False
    with zipfile.ZipFile(str(out_path), 'r') as z:
        for name in z.namelist():
            if name.lower().endswith(('.xhtml', '.html')):
                data = z.read(name).decode('utf-8')
                if '&amp;' in data:
                    found = True
                    break
    print(f"EPUB -> {out_path} contains '&amp;' in XHTML: {found}")


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--html', action='store_true')
    p.add_argument('--epub', action='store_true')
    p.add_argument('--both', action='store_true')
    args = p.parse_args()

    tmpdir = Path(tempfile.mkdtemp(prefix='ppxml-sample-'))
    sample = tmpdir / 'sample_verse.xml'
    sample.write_text(SAMPLE_TEI, encoding='utf-8')

    if args.both or args.html:
        out_html = tmpdir / 'out.html'
        run_html(sample, out_html)
    if args.both or args.epub:
        out_epub = tmpdir / 'out.epub'
        run_epub(sample, out_epub)

    print(f"Temporary files in: {tmpdir}")
