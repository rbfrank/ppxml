"""
v13 to_epub.py - Convert TEI to EPUB3 format
"""

import zipfile
import os
from datetime import datetime
import uuid
from .common import TEI_NS, parse_tei, get_metadata

def convert(tei_file, output_file, css_file=None):
    """
    Convert TEI XML to EPUB3.
    
    Args:
        tei_file: Path to TEI XML input file
        output_file: Path to EPUB output file
        css_file: Optional path to external CSS file (default: use embedded styles)
    """
    doc = parse_tei(tei_file)
    metadata = get_metadata(doc)
    
    # Generate unique book ID
    book_id = str(uuid.uuid4())
    
    # Collect all image references
    images = collect_images(doc)
    
    # Get base directory of TEI file for resolving image paths
    base_dir = os.path.dirname(os.path.abspath(tei_file))
    
    # Collect chapters and content
    chapters = []
    chapter_num = 0
    
    # Process front matter
    front = doc.find('.//tei:front', TEI_NS)
    if front is not None:
        for div in front.findall('.//tei:div', TEI_NS):
            chapter_num += 1
            div_type = div.get('type', 'front')
            title = get_div_title(div) or f"Front Matter {chapter_num}"
            content = process_div_to_html(div, metadata['title'])
            chapters.append({
                'id': f'chapter{chapter_num:03d}',
                'filename': f'chapter{chapter_num:03d}.xhtml',
                'title': title,
                'content': content
            })
    
    # Process body chapters
    body = doc.find('.//tei:body', TEI_NS)
    if body is not None:
        for div in body.findall('.//tei:div', TEI_NS):
            chapter_num += 1
            title = get_div_title(div) or f"Chapter {chapter_num}"
            content = process_div_to_html(div, metadata['title'])
            chapters.append({
                'id': f'chapter{chapter_num:03d}',
                'filename': f'chapter{chapter_num:03d}.xhtml',
                'title': title,
                'content': content
            })
    
    # Process back matter
    back = doc.find('.//tei:back', TEI_NS)
    if back is not None:
        for div in back.findall('.//tei:div', TEI_NS):
            chapter_num += 1
            div_type = div.get('type', 'back')
            title = get_div_title(div) or f"Back Matter {chapter_num}"
            content = process_div_to_html(div, metadata['title'])
            chapters.append({
                'id': f'chapter{chapter_num:03d}',
                'filename': f'chapter{chapter_num:03d}.xhtml',
                'title': title,
                'content': content
            })
    
    # Create EPUB file
    create_epub(output_file, metadata, chapters, book_id, images, base_dir, css_file)
    
    print(f"EPUB conversion complete: {output_file}")
    print(f"Generated {len(chapters)} chapter(s)")
    print(f"Included {len(images)} image(s)")

def collect_images(doc):
    """Collect all image references from the TEI document."""
    images = set()
    for graphic in doc.findall('.//tei:graphic', TEI_NS):
        url = graphic.get('url', '')
        if url:
            images.add(url)
    return sorted(images)

def get_div_title(div):
    """Extract title from div's head element."""
    head = div.find('tei:head', TEI_NS)
    if head is not None:
        return ''.join(head.itertext()).strip()
    return None

def process_div_to_html(div, book_title):
    """Convert a TEI div to XHTML content for EPUB."""
    parts = []
    
    # Get chapter title
    head = div.find('tei:head', TEI_NS)
    if head is not None:
        title = ''.join(head.itertext()).strip()
        parts.append(f'<h1>{title}</h1>')
    
    # Process all child elements
    for elem in div:
        if not isinstance(elem.tag, str):
            continue
        elem_tag = elem.tag.replace(f"{{{TEI_NS['tei']}}}", '')
        if elem_tag != 'head':  # Skip head, already processed
            parts.append(process_element(elem))
    
    return '\n'.join(parts)

def process_element(elem):
    """Process a TEI element and return XHTML string."""
    tag = elem.tag.replace(f"{{{TEI_NS['tei']}}}", '')
    
    if tag == 'p':
        return f'<p>{process_text_content(elem)}</p>'
    
    elif tag == 'quote':
        # Check if it's a block quote or inline
        parent_tag = elem.getparent().tag.replace(f"{{{TEI_NS['tei']}}}", '')
        if parent_tag == 'p':
            return f'<q>{process_text_content(elem)}</q>'
        else:
            return f'<blockquote><p>{process_text_content(elem)}</p></blockquote>'
    
    elif tag == 'list':
        items = []
        for item in elem.findall('tei:item', TEI_NS):
            items.append(f'  <li>{process_text_content(item)}</li>')
        return '<ul>\n' + '\n'.join(items) + '\n</ul>'
    
    elif tag == 'table':
        rows = []
        for row in elem.findall('tei:row', TEI_NS):
            cells = []
            for cell in row.findall('tei:cell', TEI_NS):
                cell_tag = 'th' if cell.get('role') == 'label' else 'td'
                cells.append(f'    <{cell_tag}>{process_text_content(cell)}</{cell_tag}>')
            rows.append('  <tr>\n' + '\n'.join(cells) + '\n  </tr>')
        return '<table>\n' + '\n'.join(rows) + '\n</table>'
    
    elif tag == 'figure':
        rend = elem.get('rend', '')
        if rend:
            parts = [f'<figure class="{rend}">']
        else:
            parts = ['<figure>']
        
        graphic = elem.find('tei:graphic', TEI_NS)
        if graphic is not None:
            url = graphic.get('url', '')
            figdesc = elem.find('tei:figDesc', TEI_NS)
            alt_text = ''.join(figdesc.itertext()).strip() if figdesc is not None else ''
            parts.append(f'  <img src="../{url}" alt="{alt_text}"/>')
        
        head = elem.find('tei:head', TEI_NS)
        if head is not None:
            parts.append(f'  <figcaption>{process_text_content(head)}</figcaption>')
        
        parts.append('</figure>')
        return '\n'.join(parts)
    
    elif tag == 'lg':
        parts = ['<div class="poem">']
        
        head = elem.find('tei:head', TEI_NS)
        if head is not None:
            parts.append(f'  <p class="poem-title">{process_text_content(head)}</p>')
        
        nested_lg = elem.findall('tei:lg', TEI_NS)
        if nested_lg:
            for stanza in nested_lg:
                parts.append('  <div class="stanza">')
                for line in stanza.findall('tei:l', TEI_NS):
                    rend = line.get('rend', '')
                    line_class = f'line {rend}' if rend else 'line'
                    parts.append(f'    <p class="{line_class}">{process_text_content(line)}</p>')
                parts.append('  </div>')
        else:
            parts.append('  <div class="stanza">')
            for line in elem.findall('tei:l', TEI_NS):
                rend = line.get('rend', '')
                line_class = f'line {rend}' if rend else 'line'
                parts.append(f'    <p class="{line_class}">{process_text_content(line)}</p>')
            parts.append('  </div>')
        
        parts.append('</div>')
        return '\n'.join(parts)
    
    elif tag == 'div':
        parts = []
        for child in elem:
            parts.append(process_element(child))
        return '\n'.join(parts)
    
    elif tag == 'milestone':
        # Section/thought break
        rend = elem.get('rend', 'space')
        return f'<div class="milestone {rend}"></div>'
    
    else:
        return process_text_content(elem)

def process_text_content(elem):
    """Extract text content from element, processing inline markup."""
    result = ''
    
    if elem.text:
        result = elem.text
    
    for child in elem:
        tag = child.tag.replace(f"{{{TEI_NS['tei']}}}", '')
        
        if tag == 'hi':
            rend = child.get('rend', 'italic')
            child_text = ''.join(child.itertext())
            if rend == 'italic':
                result += f'<i>{child_text}</i>'
            elif rend == 'bold':
                result += f'<b>{child_text}</b>'
            else:
                result += f'<span class="{rend}">{child_text}</span>'
        
        elif tag == 'emph':
            result += f'<em>{"".join(child.itertext())}</em>'
        
        elif tag == 'ref':
            result += f'<a href="{child.get("target", "#")}">{"".join(child.itertext())}</a>'
        
        elif tag == 'note':
            result += f'<sup>[{"".join(child.itertext())}]</sup>'
        
        elif tag == 'foreign':
            result += f'<i>{"".join(child.itertext())}</i>'
        
        elif tag == 'title':
            result += f'<i>{"".join(child.itertext())}</i>'
        
        else:
            result += ''.join(child.itertext())
        
        if child.tail:
            result += child.tail
    
    return result

def create_epub(output_file, metadata, chapters, book_id, images, base_dir, css_file=None):
    """Create the EPUB file structure."""
    
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as epub:
        # mimetype must be first and uncompressed
        epub.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
        
        # META-INF/container.xml
        epub.writestr('META-INF/container.xml', get_container_xml())
        
        # OEBPS/content.opf
        epub.writestr('OEBPS/content.opf', get_content_opf(metadata, chapters, book_id, images))
        
        # OEBPS/toc.ncx
        epub.writestr('OEBPS/toc.ncx', get_toc_ncx(metadata, chapters, book_id))
        
        # OEBPS/nav.xhtml
        epub.writestr('OEBPS/nav.xhtml', get_nav_xhtml(metadata, chapters))
        
        # OEBPS/stylesheet.css
        if css_file and os.path.exists(css_file):
            with open(css_file, 'r', encoding='utf-8') as f:
                epub.writestr('OEBPS/stylesheet.css', f.read())
        else:
            epub.writestr('OEBPS/stylesheet.css', get_stylesheet())
        
        # Chapter files
        for chapter in chapters:
            chapter_html = get_chapter_html(chapter, metadata['title'])
            epub.writestr(f'OEBPS/text/{chapter["filename"]}', chapter_html)
        
        # Image files
        for image_path in images:
            full_path = os.path.join(base_dir, image_path)
            if os.path.exists(full_path):
                with open(full_path, 'rb') as img_file:
                    epub.writestr(f'OEBPS/{image_path}', img_file.read())
            else:
                print(f"Warning: Image not found: {full_path}")

def get_container_xml():
    """Generate META-INF/container.xml."""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>'''

def get_content_opf(metadata, chapters, book_id, images):
    """Generate OEBPS/content.opf."""
    date = datetime.now().strftime('%Y-%m-%d')
    
    # Manifest items
    manifest_items = ['    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>']
    manifest_items.append('    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>')
    manifest_items.append('    <item id="css" href="stylesheet.css" media-type="text/css"/>')
    
    for chapter in chapters:
        manifest_items.append(f'    <item id="{chapter["id"]}" href="text/{chapter["filename"]}" media-type="application/xhtml+xml"/>')
    
    # Add images to manifest
    for i, image_path in enumerate(images):
        # Determine media type from extension
        ext = os.path.splitext(image_path)[1].lower()
        media_type_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml'
        }
        media_type = media_type_map.get(ext, 'image/jpeg')
        manifest_items.append(f'    <item id="img{i:03d}" href="{image_path}" media-type="{media_type}"/>')
    
    # Spine items
    spine_items = [f'    <itemref idref="{chapter["id"]}"/>' for chapter in chapters]
    
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="book-id">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="book-id">{book_id}</dc:identifier>
    <dc:title>{metadata['title']}</dc:title>
    <dc:language>en</dc:language>
    <dc:date>{date}</dc:date>
    <meta property="dcterms:modified">{datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}Z</meta>
  </metadata>
  <manifest>
{chr(10).join(manifest_items)}
  </manifest>
  <spine toc="ncx">
{chr(10).join(spine_items)}
  </spine>
</package>'''

def get_toc_ncx(metadata, chapters, book_id):
    """Generate OEBPS/toc.ncx for EPUB2 compatibility."""
    nav_points = []
    for i, chapter in enumerate(chapters, 1):
        nav_points.append(f'''    <navPoint id="nav{i}" playOrder="{i}">
      <navLabel>
        <text>{chapter['title']}</text>
      </navLabel>
      <content src="text/{chapter['filename']}"/>
    </navPoint>''')
    
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="{book_id}"/>
    <meta name="dtb:depth" content="1"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  <docTitle>
    <text>{metadata['title']}</text>
  </docTitle>
  <navMap>
{chr(10).join(nav_points)}
  </navMap>
</ncx>'''

def get_nav_xhtml(metadata, chapters):
    """Generate OEBPS/nav.xhtml for EPUB3."""
    nav_items = [f'      <li><a href="text/{chapter["filename"]}">{chapter["title"]}</a></li>' 
                 for chapter in chapters]
    
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
  <meta charset="UTF-8"/>
  <title>Table of Contents</title>
</head>
<body>
  <nav epub:type="toc">
    <h1>Table of Contents</h1>
    <ol>
{chr(10).join(nav_items)}
    </ol>
  </nav>
</body>
</html>'''

def get_stylesheet():
    """Generate OEBPS/stylesheet.css."""
    return '''body {
  font-family: serif;
  line-height: 1.6;
  margin: 1em;
}

h1 {
  text-align: center;
  margin-top: 2em;
  margin-bottom: 1em;
}

p {
  margin: 0;
  text-indent: 1.5em;
}

p:first-of-type,
h1 + p,
h2 + p,
blockquote + p,
figure + p {
  text-indent: 0;
}

blockquote {
  margin: 1em 2em;
}

figure {
  text-align: center;
  margin: 2em 0;
}

figure img {
  max-width: 100%;
}

figcaption {
  font-style: italic;
  margin-top: 0.5em;
}

.poem {
  margin: 2em 0;
}

.poem-title {
  text-align: center;
  font-weight: bold;
  text-indent: 0;
}

.stanza {
  margin-bottom: 1em;
}

.line {
  text-indent: 0;
  margin: 0;
}

.indent {
  margin-left: 2em;
}

.indent2 {
  margin-left: 4em;
}

.indent3 {
  margin-left: 6em;
}

.milestone {
  text-align: center;
  margin: 2em 0;
}

.milestone.stars::before {
  content: "*       *       *       *       *";
  white-space: pre;
}

.milestone.space {
  height: 2em;
}

table {
  border-collapse: collapse;
  margin: 1em auto;
}

td, th {
  border: 1px solid #ccc;
  padding: 0.5em;
}
'''

def get_chapter_html(chapter, book_title):
    """Generate XHTML for a chapter."""
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta charset="UTF-8"/>
  <title>{chapter['title']} - {book_title}</title>
  <link rel="stylesheet" type="text/css" href="../stylesheet.css"/>
</head>
<body>
{chapter['content']}
</body>
</html>'''

