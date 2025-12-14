"""
v15 to_html.py - Convert TEI to HTML
"""

import os
import glob
from .common import TEI_NS, parse_tei, get_title

def convert(tei_file, output_file, css_file=None):
    """
    Convert TEI XML to HTML.
    
    Args:
        tei_file: Path to TEI XML input file
        output_file: Path to HTML output file
        css_file: Optional path to external CSS file (default: auto-detect or use embedded styles)
    """
    doc = parse_tei(tei_file)
    title = get_title(doc)
    
    # Auto-detect CSS file in same directory if not specified
    if css_file is None:
        input_dir = os.path.dirname(os.path.abspath(tei_file))
        css_files = glob.glob(os.path.join(input_dir, '*.css'))
        if css_files:
            css_file = css_files[0]  # Use first CSS file found
            print(f"Auto-detected CSS file: {os.path.basename(css_file)}")
    
    # Start building HTML
    html_parts = []
    html_parts.append('<!DOCTYPE html>')
    html_parts.append('<html lang="en">')
    html_parts.append('<head>')
    html_parts.append('  <meta charset="UTF-8">')
    html_parts.append('  <meta name="viewport" content="width=device-width, initial-scale=1.0">')
    html_parts.append(f'  <title>{title}</title>')
    
    if css_file:
        # Read and inline CSS
        with open(css_file, 'r', encoding='utf-8') as f:
            css_content = f.read()
        html_parts.append('  <style>')
        html_parts.append(css_content)
        html_parts.append('  </style>')
    else:
        # Embed default styles
        html_parts.append('  <style>')
        html_parts.append('    body { max-width: 40em; margin: 2em auto; padding: 0 1em; font-family: serif; line-height: 1.6; }')
        html_parts.append('    h1 { text-align: center; }')
        html_parts.append('    h2 { margin-top: 2em; }')
        html_parts.append('    .titlepage { text-align: center; margin: 2em 0; }')
        html_parts.append('    .titlepage p { margin: 0.5em 0; }')
        html_parts.append('    .italic { font-style: italic; }')
        html_parts.append('    .bold { font-weight: bold; }')
        html_parts.append('    .underline { text-decoration: underline; }')
        html_parts.append('    .small-caps { font-variant: small-caps; }')
        html_parts.append('    blockquote { margin: 1em 2em; }')
        html_parts.append('    figure { margin: 2em 0; text-align: center; }')
        html_parts.append('    figure img { max-width: 100%; height: auto; }')
        html_parts.append('    figcaption { margin-top: 0.5em; font-style: italic; }')
        html_parts.append('    .poem { margin: 2em 0; }')
        html_parts.append('    .poem-title { text-align: center; font-weight: bold; margin-bottom: 1em; }')
        html_parts.append('    .stanza { margin-bottom: 1em; }')
        html_parts.append('    .line { margin: 0; }')
        html_parts.append('    .indent { margin-left: 2em; }')
        html_parts.append('    .indent2 { margin-left: 4em; }')
        html_parts.append('    .indent3 { margin-left: 6em; }')
        html_parts.append('    .center { text-align: center; }')
        html_parts.append('    .milestone { text-align: center; margin: 2em 0; }')
        html_parts.append('    .milestone.stars::before { content: "*       *       *       *       *"; white-space: pre; }')
        html_parts.append('    .milestone.space { height: 2em; }')
        html_parts.append('    table { border-collapse: collapse; margin: 1em 0; }')
        html_parts.append('    td, th { border: 1px solid #ccc; padding: 0.5em; }')
        html_parts.append('  </style>')
    
    html_parts.append('</head>')
    html_parts.append('<body>')
    
    html_parts.append(f'<h1>{title}</h1>')
    
    # Process front matter
    front = doc.find('.//tei:front', TEI_NS)
    if front is not None:
        for div in front.findall('tei:div', TEI_NS):
            div_type = div.get('type', '')
            if div_type:
                html_parts.append(f'<div class="{div_type}">')
            else:
                html_parts.append('<div>')
            
            for elem in div:
                html_parts.append(process_element(elem))
            
            html_parts.append('</div>')
    
    # Process body
    body = doc.find('.//tei:body', TEI_NS)
    if body is not None:
        for div in body.findall('tei:div', TEI_NS):
            # Chapter/section heading
            head = div.find('tei:head', TEI_NS)
            if head is not None:
                html_parts.append(f'<h2>{process_text_content(head)}</h2>')
            
            # Process all child elements
            for elem in div:
                if not isinstance(elem.tag, str):
                    continue
                if elem.tag != f"{{{TEI_NS['tei']}}}head":  # Skip head, already processed
                    html_parts.append(process_element(elem))
    
    # Process back matter
    back = doc.find('.//tei:back', TEI_NS)
    if back is not None:
        for div in back.findall('tei:div', TEI_NS):
            # Only process top-level divs in back
            if div.getparent().tag == f"{{{TEI_NS['tei']}}}back":
                div_type = div.get('type', '')
                if div_type:
                    html_parts.append(f'<div class="{div_type}">')
                else:
                    html_parts.append('<div>')
                
                # Heading
                head = div.find('tei:head', TEI_NS)
                if head is not None:
                    html_parts.append(f'<h2>{process_text_content(head)}</h2>')
                
                # Process all child elements
                for elem in div:
                    if not isinstance(elem.tag, str):
                        continue
                    if elem.tag != f"{{{TEI_NS['tei']}}}head":
                        html_parts.append(process_element(elem))
                
                html_parts.append('</div>')
    
    html_parts.append('</body>')
    html_parts.append('</html>')
    
    # Write output
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(html_parts))
    
    print(f"HTML conversion complete: {output_file}")

def process_element(elem):
    """Process a TEI element and return HTML string."""
    tag = elem.tag.replace(f"{{{TEI_NS['tei']}}}", '')
    
    if tag == 'p':
        return f'<p>{process_text_content(elem)}</p>'
    
    elif tag == 'quote':
        # Check if it's a block quote (standalone) or inline
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
        # Process figure with graphic
        rend = elem.get('rend', '')
        if rend:
            parts = [f'<figure class="{rend}">']
        else:
            parts = ['<figure>']
        
        graphic = elem.find('tei:graphic', TEI_NS)
        if graphic is not None:
            url = graphic.get('url', '')
            
            # Get alt text from figDesc
            figdesc = elem.find('tei:figDesc', TEI_NS)
            alt_text = ''.join(figdesc.itertext()).strip() if figdesc is not None else ''
            
            parts.append(f'  <img src="{url}" alt="{alt_text}">')
        
        # Add caption from head
        head = elem.find('tei:head', TEI_NS)
        if head is not None:
            parts.append(f'  <figcaption>{process_text_content(head)}</figcaption>')
        
        parts.append('</figure>')
        return '\n'.join(parts)
    
    elif tag == 'lg':  # Line group (verse)
        parts = ['<div class="poem">']
        
        # Check for title
        head = elem.find('tei:head', TEI_NS)
        if head is not None:
            parts.append(f'  <div class="poem-title">{process_text_content(head)}</div>')
        
        # Check for nested stanzas
        nested_lg = elem.findall('tei:lg', TEI_NS)
        if nested_lg:
            # Multiple stanzas
            for stanza in nested_lg:
                parts.append('  <div class="stanza">')
                for line in stanza.findall('tei:l', TEI_NS):
                    rend = line.get('rend', '')
                    line_class = f'line {rend}' if rend else 'line'
                    parts.append(f'    <div class="{line_class}">{process_text_content(line)}</div>')
                parts.append('  </div>')
        else:
            # Single stanza - direct lines
            parts.append('  <div class="stanza">')
            for line in elem.findall('tei:l', TEI_NS):
                rend = line.get('rend', '')
                line_class = f'line {rend}' if rend else 'line'
                parts.append(f'    <div class="{line_class}">{process_text_content(line)}</div>')
            parts.append('  </div>')
        
        parts.append('</div>')
        return '\n'.join(parts)
    
    elif tag == 'div':
        # Nested div - process recursively
        div_type = elem.get('type', '')
        parts = []
        if div_type:
            parts.append(f'<div class="{div_type}">')
        else:
            parts.append('<div>')
        
        for child in elem:
            parts.append(process_element(child))
        
        parts.append('</div>')
        return '\n'.join(parts)
    
    elif tag == 'milestone':
        # Section/thought break
        rend = elem.get('rend', 'space')
        return f'<div class="milestone {rend}"></div>'
    
    else:
        # Default: just extract text
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

