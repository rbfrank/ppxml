"""
to_text.py - Convert TEI to plain text with wrapping
"""

import textwrap
from .common import TEI_NS, parse_tei

def convert(tei_file, output_file, line_width=72):
    """
    Convert TEI XML to plain text with wrapping.
    
    Args:
        tei_file: Path to TEI XML input file
        output_file: Path to text output file
        line_width: Width for line wrapping (default 72)
    """
    doc = parse_tei(tei_file)
    
    output_lines = []
    
    # Process front matter
    front = doc.find('.//tei:front', TEI_NS)
    if front is not None:
        for div in front.findall('tei:div', TEI_NS):
            # Process all child elements in order
            for elem in div:
                process_element(elem, output_lines, line_width)
        
        output_lines.append('')  # Extra blank after front
    
    # Process body
    body = doc.find('.//tei:body', TEI_NS)
    if body is not None:
        for div in body.findall('tei:div', TEI_NS):
            # Heading - with 3 blank lines before (4 total including paragraph spacing), 2 after
            head = div.find('tei:head', TEI_NS)
            if head is not None:
                heading_text = ''.join(head.itertext()).strip()
                if heading_text:
                    # Add 3 blank lines before chapter heading (becomes 4 with paragraph spacing)
                    for _ in range(3):
                        output_lines.append('')
                    output_lines.append(heading_text.upper())
                    # Add 2 blank lines after chapter heading
                    output_lines.append('')
                    output_lines.append('')
            
            # Process all child elements in order
            for elem in div:
                elem_tag = elem.tag.replace(f"{{{TEI_NS['tei']}}}", '')
                if elem_tag != 'head':  # Skip head, already processed
                    process_element(elem, output_lines, line_width)
    
    # Process back matter
    back = doc.find('.//tei:back', TEI_NS)
    if back is not None:
        output_lines.append('')  # Extra blank before back matter
        
        for div in back.findall('tei:div', TEI_NS):
            # Heading
            head = div.find('tei:head', TEI_NS)
            if head is not None:
                heading_text = ''.join(head.itertext()).strip()
                if heading_text:
                    output_lines.append(heading_text.upper())
                    output_lines.append('')
            
            # Process all child elements in order
            for elem in div:
                elem_tag = elem.tag.replace(f"{{{TEI_NS['tei']}}}", '')
                if elem_tag != 'head':
                    process_element(elem, output_lines, line_width)
    
    # Write output
    with open(output_file, 'w', encoding='utf-8') as f:
        # Convert non-breaking spaces to regular spaces before writing
        output_text = '\n'.join(output_lines)
        output_text = output_text.replace('\xa0', ' ')  # Replace non-breaking spaces
        f.write(output_text)
        if output_lines:
            f.write('\n')
    
    print(f"Text conversion complete: {output_file}")

def process_element(elem, output_lines, line_width):
    """Process a TEI element and add to output_lines."""
    elem_tag = elem.tag.replace(f"{{{TEI_NS['tei']}}}", '')
    
    if elem_tag == 'p':
        text = extract_text_with_emphasis(elem).strip()
        if text:
            wrapped = textwrap.fill(text, width=line_width,
                                  break_long_words=False,
                                  break_on_hyphens=False)
            output_lines.append(wrapped)
            output_lines.append('')
    
    elif elem_tag == 'figure':
        # Get caption from head element
        head = elem.find('tei:head', TEI_NS)
        if head is not None:
            caption = ''.join(head.itertext()).strip()
            if caption:
                # Wrap with [Illustration: caption]
                wrapped = textwrap.fill(f'[Illustration: {caption}]',
                                      width=line_width,
                                      break_long_words=False,
                                      break_on_hyphens=False)
                output_lines.append(wrapped)
            else:
                output_lines.append('[Illustration]')
        else:
            output_lines.append('[Illustration]')
        output_lines.append('')
    
    elif elem_tag == 'quote':
        # Block quote (not inside a paragraph)
        if elem.getparent().tag == f"{{{TEI_NS['tei']}}}div":
            text = extract_text_with_emphasis(elem).strip()
            if text:
                wrapped = textwrap.fill(text, width=line_width-4,
                                      initial_indent='    ',
                                      subsequent_indent='    ',
                                      break_long_words=False,
                                      break_on_hyphens=False)
                output_lines.append(wrapped)
                output_lines.append('')
    
    elif elem_tag == 'lg':
        # Poem/verse
        head = elem.find('tei:head', TEI_NS)
        if head is not None:
            title = ''.join(head.itertext()).strip()
            if title:
                output_lines.append('    ' + title.upper())
                output_lines.append('')
        
        # Check for nested stanzas
        nested_lg = elem.findall('tei:lg', TEI_NS)
        if nested_lg:
            for stanza in nested_lg:
                for line in stanza.findall('tei:l', TEI_NS):
                    line_text = extract_text_with_emphasis(line).strip()
                    rend = line.get('rend', '')
                    # Base indent of 4 spaces, plus additional for rend
                    if rend == 'indent':
                        line_text = '      ' + line_text  # 4 + 2
                    elif rend == 'indent2':
                        line_text = '        ' + line_text  # 4 + 4
                    elif rend == 'indent3':
                        line_text = '          ' + line_text  # 4 + 6
                    else:
                        line_text = '    ' + line_text  # Base 4 spaces
                    output_lines.append(line_text)
                output_lines.append('')  # Blank line between stanzas
        else:
            # Single stanza
            for line in elem.findall('tei:l', TEI_NS):
                line_text = extract_text_with_emphasis(line).strip()
                rend = line.get('rend', '')
                # Base indent of 4 spaces, plus additional for rend
                if rend == 'indent':
                    line_text = '      ' + line_text  # 4 + 2
                elif rend == 'indent2':
                    line_text = '        ' + line_text  # 4 + 4
                elif rend == 'indent3':
                    line_text = '          ' + line_text  # 4 + 6
                else:
                    line_text = '    ' + line_text  # Base 4 spaces
                output_lines.append(line_text)
            output_lines.append('')
    
    elif elem_tag == 'milestone':
        # Section/thought break
        rend = elem.get('rend', 'space')
        if rend == 'stars':
            # Center the asterisks based on line width
            stars = '*       *       *       *       *'
            stars_len = len(stars)
            padding = (line_width - stars_len) // 2
            centered = ' ' * padding + stars
            output_lines.append(centered)
        else:
            output_lines.append('')  # Just blank line for other types
        output_lines.append('')
    
    elif elem_tag == 'div':
        # Nested div - process all its children recursively
        for child in elem:
            process_element(child, output_lines, line_width)

def extract_text_with_emphasis(elem):
    """Extract text from element, marking emphasis with underscores."""
    result = ''
    
    if elem.text:
        result = elem.text
    
    for child in elem:
        tag = child.tag.replace(f"{{{TEI_NS['tei']}}}", '')
        child_text = ''.join(child.itertext())
        
        if tag in ['emph', 'hi']:
            # Mark emphasis with underscores
            result += f'_{child_text}_'
        else:
            result += child_text
        
        if child.tail:
            result += child.tail
    
    return result

