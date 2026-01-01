"""
to_epub.py - Convert TEI to EPUB3

This module provides a backward-compatible API that wraps the new
EPUBRenderer implementation. The old implementation is preserved
in to_epub_old.py for reference.
"""

import os
import tempfile
import zipfile
from datetime import datetime
from lxml import etree
import html

from .common import parse_tei, get_title, TEI_NS
from .renderers.epub_renderer import EPUBRenderer
from .epub_image_utils import collect_graphic_urls, copy_images_to_epub


def convert(tei_file, output_file):
    """
    Convert TEI XML to EPUB3 format.

    Args:
        tei_file: Path to TEI XML input file
        output_file: Path to EPUB output file
    """
    # Parse the TEI document
    doc = parse_tei(tei_file)
    title = get_title(doc)

    # Discover custom CSS files for EPUB
    from .common import find_css_files, read_css_files
    css_paths = find_css_files(tei_file, 'epub')
    custom_css_content = read_css_files(css_paths) if css_paths else None

    if css_paths:
        print(f"Auto-detected CSS files: {', '.join([os.path.basename(p) for p in css_paths])}")

    # Create temporary directory for EPUB assembly
    temp_dir = tempfile.mkdtemp(prefix='epub_')

    try:
        # Create EPUB directory structure
        meta_inf = os.path.join(temp_dir, 'META-INF')
        oebps = os.path.join(temp_dir, 'OEBPS')
        os.makedirs(meta_inf)
        os.makedirs(oebps)

        # Create mimetype file
        with open(os.path.join(temp_dir, 'mimetype'), 'w', encoding='utf-8') as f:
            f.write('application/epub+zip')

        # Create container.xml
        create_container_xml(meta_inf)

        # Process images
        image_map = {}
        input_dir = os.path.dirname(os.path.abspath(tei_file))
        image_urls = collect_graphic_urls(doc, input_dir)
        if image_urls:
            images_dir = os.path.join(oebps, 'images')
            image_map = copy_images_to_epub(image_urls, input_dir, images_dir)

        # Create CSS file with custom styles appended
        css_content = create_css(custom_css_content)
        with open(os.path.join(oebps, 'styles.css'), 'w', encoding='utf-8') as f:
            f.write(css_content)

        # Build ID mapping for cross-references
        id_map = build_id_mapping(doc)

        # Create renderer
        renderer = EPUBRenderer()

        # Generate book ID
        book_id = f'urn:uuid:{title.replace(" ", "-").lower()}-{datetime.now().strftime("%Y%m%d")}'

        # Process document sections
        chapters = []
        toc_entries = []

        # Process front matter
        front = doc.find('.//tei:front', TEI_NS)
        if front is not None:
            for i, div in enumerate(front.findall('tei:div', TEI_NS)):
                filename = f'front{i+1}.xhtml'
                chapter_title = get_div_title(div)
                create_chapter_file(oebps, filename, div, title, renderer, id_map, image_map)
                chapters.append({'filename': filename, 'title': chapter_title or f'Front Matter {i+1}'})
                if chapter_title:
                    toc_entries.append({'filename': filename, 'title': chapter_title})

        # Process body chapters
        body = doc.find('.//tei:body', TEI_NS)
        if body is not None:
            for i, div in enumerate(body.findall('tei:div', TEI_NS)):
                filename = f'chapter{i+1}.xhtml'
                chapter_title = get_div_title(div)
                create_chapter_file(oebps, filename, div, title, renderer, id_map, image_map)
                chapters.append({'filename': filename, 'title': chapter_title or f'Chapter {i+1}'})
                if chapter_title:
                    toc_entries.append({'filename': filename, 'title': chapter_title})

        # Process back matter
        back = doc.find('.//tei:back', TEI_NS)
        if back is not None:
            for i, div in enumerate(back.findall('tei:div', TEI_NS)):
                if div.getparent().tag == f"{{{TEI_NS['tei']}}}back":
                    filename = f'back{i+1}.xhtml'
                    chapter_title = get_div_title(div)
                    create_chapter_file(oebps, filename, div, title, renderer, id_map, image_map)
                    chapters.append({'filename': filename, 'title': chapter_title or f'Back Matter {i+1}'})
                    if chapter_title:
                        toc_entries.append({'filename': filename, 'title': chapter_title})

        # Create navigation document (EPUB3 requirement)
        create_nav_doc(oebps, title, toc_entries)

        # Create package document (OPF)
        create_package_doc(oebps, title, book_id, chapters, doc, image_map)

        # Create EPUB file
        create_epub_archive(temp_dir, output_file)

        print(f"EPUB conversion complete: {output_file}")

    finally:
        # Clean up temporary directory
        import shutil
        shutil.rmtree(temp_dir)


def get_div_title(div):
    """Extract title from div's head element."""
    head = div.find('tei:head', TEI_NS)
    if head is not None:
        return ''.join(head.itertext()).strip()
    return ''


def build_id_mapping(doc):
    """Build a mapping of XML IDs to their containing filenames."""
    id_map = {}

    # Process front matter
    front = doc.find('.//tei:front', TEI_NS)
    if front is not None:
        for i, div in enumerate(front.findall('tei:div', TEI_NS)):
            filename = f'front{i+1}.xhtml'
            collect_ids_from_div(div, filename, id_map)

    # Process body chapters
    body = doc.find('.//tei:body', TEI_NS)
    if body is not None:
        for i, div in enumerate(body.findall('tei:div', TEI_NS)):
            filename = f'chapter{i+1}.xhtml'
            collect_ids_from_div(div, filename, id_map)

    # Process back matter
    back = doc.find('.//tei:back', TEI_NS)
    if back is not None:
        for i, div in enumerate(back.findall('tei:div', TEI_NS)):
            if div.getparent().tag == f"{{{TEI_NS['tei']}}}back":
                filename = f'back{i+1}.xhtml'
                collect_ids_from_div(div, filename, id_map)

    return id_map


def collect_ids_from_div(div, filename, id_map):
    """Collect all XML IDs from a div and its descendants."""
    # Check div itself for ID
    div_id = div.get('{http://www.w3.org/XML/1998/namespace}id', '')
    if div_id:
        id_map[div_id] = filename

    # Check all descendant elements for IDs
    for elem in div.iter():
        elem_id = elem.get('{http://www.w3.org/XML/1998/namespace}id', '')
        if elem_id:
            id_map[elem_id] = filename


def create_container_xml(meta_inf):
    """Create META-INF/container.xml"""
    container = '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>'''

    with open(os.path.join(meta_inf, 'container.xml'), 'w', encoding='utf-8') as f:
        f.write(container)


def create_css(custom_css_content=None):
    """
    Create CSS stylesheet with optional custom styles appended.

    Args:
        custom_css_content: Optional string containing custom CSS rules

    Returns:
        Complete CSS content as string
    """
    css = '''body { max-width: 40em; margin: 2em auto; padding: 0 1em; font-family: serif; line-height: 1.6; }
h1 { text-align: center; }
h2 { margin-top: 2em; }
.italic { font-style: italic; }
.bold { font-weight: bold; }
.underline { text-decoration: underline; }
.small-caps { font-variant: small-caps; }
.signature { text-align: right; font-style: italic; margin-top: 0.5em; }
blockquote { margin: 1em 2em; }
figure { margin: 2em auto; width: 80%; max-width: 100%; text-align: center; }
figure.left { float: left; margin: 0 2em 1em 0; width: 50%; max-width: 50%; }
figure.right { float: right; margin: 0 0 1em 2em; width: 50%; max-width: 50%; }
figure.center { margin: 2em auto; display: block; }
figure img { width: 100%; height: auto; }
figcaption { margin-top: 0.5em; font-style: italic; }
.poem { margin: 2em 0; }
.poem.center { text-align: center; }
.poem.center .stanza { display: inline-block; text-align: left; }
.poem-title { text-align: center; font-weight: bold; margin-bottom: 1em; }
.stanza { margin-bottom: 1em; }
.line { margin-top: 0; margin-bottom: 0; }
.indent { margin-left: 2em; }
.indent2 { margin-left: 4em; }
.indent3 { margin-left: 6em; }
.center { text-align: center; }
.milestone { text-align: center; margin: 2em 0; }
.milestone.stars::before { content: "*       *       *       *       *"; white-space: pre; }
.milestone.space { height: 2em; }
table { border-collapse: collapse; margin: 1em 0; }
td, th { border: 1px solid #ccc; padding: 0.5em; }
'''

    # Append custom CSS if provided
    if custom_css_content:
        css += '\n\n/* Custom styles */\n'
        css += custom_css_content

    return css


def create_chapter_file(oebps, filename, div, book_title, renderer, id_map, image_map):
    """Create an XHTML chapter file using EPUBRenderer."""
    # Render chapter using EPUBRenderer
    chapter_html = renderer.render_chapter(div, book_title, id_map)

    # Replace image src paths if needed
    if image_map:
        import re
        def replace_img_src(match):
            src = match.group(2)
            new_src = image_map.get(src, src)
            return match.group(1) + new_src + match.group(3)
        chapter_html = re.sub(r'(<img[^>]*src=")([^"]+)(")', replace_img_src, chapter_html)

    # Write chapter file
    with open(os.path.join(oebps, filename), 'w', encoding='utf-8') as f:
        f.write(chapter_html)


def create_nav_doc(oebps, title, toc_entries):
    """Create navigation document (nav.xhtml) for EPUB3."""
    nav = ['<?xml version="1.0" encoding="UTF-8"?>']
    nav.append('<!DOCTYPE html>')
    nav.append('<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">')
    nav.append('<head>')
    nav.append('  <title>Table of Contents</title>')
    nav.append('  <link rel="stylesheet" type="text/css" href="styles.css"/>')
    nav.append('</head>')
    nav.append('<body>')
    nav.append('  <nav epub:type="toc" id="toc">')
    nav.append(f'    <h1>{html.escape(title)}</h1>')
    nav.append('    <ol>')

    for entry in toc_entries:
        nav.append(f'      <li><a href="{entry["filename"]}">{html.escape(entry["title"])}</a></li>')

    nav.append('    </ol>')
    nav.append('  </nav>')
    nav.append('</body>')
    nav.append('</html>')

    with open(os.path.join(oebps, 'nav.xhtml'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(nav))


def create_package_doc(oebps, title, book_id, chapters, doc, image_map):
    """Create package document (content.opf)."""
    # Extract metadata from TEI header
    header = doc.find('.//tei:teiHeader', TEI_NS)

    # Get author if available
    author = 'Unknown'
    if header is not None:
        author_elem = header.find('.//tei:author', TEI_NS)
        if author_elem is not None:
            author = ''.join(author_elem.itertext()).strip()

    # Get language
    lang = doc.getroot().get('{http://www.w3.org/1998/namespace}lang', 'en')

    opf = ['<?xml version="1.0" encoding="UTF-8"?>']
    opf.append('<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="book-id">')

    # Metadata
    opf.append('  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">')
    opf.append(f'    <dc:identifier id="book-id">{book_id}</dc:identifier>')
    opf.append(f'    <dc:title>{html.escape(title)}</dc:title>')
    opf.append(f'    <dc:language>{lang}</dc:language>')
    opf.append(f'    <dc:creator>{html.escape(author)}</dc:creator>')
    opf.append(f'    <meta property="dcterms:modified">{datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}</meta>')

    # Add cover metadata if cover image exists
    if image_map:
        cover_candidates = ['cover.jpg', 'cover.jpeg', 'cover.png', 'cover.gif']
        cover_filename = next((path for path in image_map.values() if path in cover_candidates), None)
        if cover_filename:
            cover_id = f"img_{cover_filename.replace('.', '_')}"
            opf.append(f'    <meta name="cover" content="{cover_id}"/>')

    opf.append('  </metadata>')

    # Manifest
    opf.append('  <manifest>')
    opf.append('    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>')
    opf.append('    <item id="css" href="styles.css" media-type="text/css"/>')

    for i, chapter in enumerate(chapters):
        opf.append(f'    <item id="chapter{i+1}" href="{chapter["filename"]}" media-type="application/xhtml+xml"/>')

    # Add images to manifest
    if image_map:
        for new_path in image_map.values():
            filename = os.path.basename(new_path)
            ext = os.path.splitext(filename)[1].lower()
            if ext == '.png':
                media_type = 'image/png'
            elif ext in ['.jpg', '.jpeg']:
                media_type = 'image/jpeg'
            elif ext == '.gif':
                media_type = 'image/gif'
            elif ext == '.svg':
                media_type = 'image/svg+xml'
            else:
                media_type = 'image/png'  # default
            item_id = f"img_{filename.replace('.', '_')}"
            opf.append(f'    <item id="{item_id}" href="{new_path}" media-type="{media_type}"/>')

    opf.append('  </manifest>')

    # Spine
    opf.append('  <spine>')
    for i in range(len(chapters)):
        opf.append(f'    <itemref idref="chapter{i+1}"/>')
    opf.append('  </spine>')

    opf.append('</package>')

    with open(os.path.join(oebps, 'content.opf'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(opf))


def create_epub_archive(temp_dir, output_file):
    """Create the final EPUB ZIP archive."""
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as epub:
        # Add mimetype first (uncompressed)
        epub.write(os.path.join(temp_dir, 'mimetype'), 'mimetype', compress_type=zipfile.ZIP_STORED)

        # Add all other files
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file == 'mimetype':
                    continue
                filepath = os.path.join(root, file)
                arcname = os.path.relpath(filepath, temp_dir)
                epub.write(filepath, arcname)
