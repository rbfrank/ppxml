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
                if not isinstance(elem.tag, str):
                    continue
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
                # Skip comments and processing instructions
                if not isinstance(elem.tag, str):
                    continue
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
                if not isinstance(elem.tag, str):
                    continue
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
            # Check if there are line breaks in the text
            if '\n' in text:
                # Split on line breaks and wrap each part separately
                parts = text.split('\n')
                for part in parts:
                    if part.strip():
                        wrapped = textwrap.fill(part.strip(), width=line_width,
                                              break_long_words=False,
                                              break_on_hyphens=False)
                        output_lines.append(wrapped)
            else:
                # Normal paragraph wrapping
                wrapped = textwrap.fill(text, width=line_width,
                                      break_long_words=False,
                                      break_on_hyphens=False)
                output_lines.append(wrapped)
            output_lines.append('')
    
    elif elem_tag == 'list':
        # Process list items
        for item in elem.findall('tei:item', TEI_NS):
            item_text = extract_text_with_emphasis(item).strip()
            if item_text:
                # Wrap with bullet point and hanging indent
                wrapped = textwrap.fill(item_text, width=line_width,
                                      initial_indent='  • ',
                                      subsequent_indent='    ',
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
    
    elif elem_tag == 'table':
        # Simple table rendering for text
        rows_data = []
        for row in elem.findall('tei:row', TEI_NS):
            cells = []
            for cell in row.findall('tei:cell', TEI_NS):
                cell_text = ''.join(cell.itertext()).strip()
                cells.append(cell_text)
            if cells:
                rows_data.append(cells)
        
        if rows_data:
            # Calculate column widths
            num_cols = max(len(row) for row in rows_data)
            col_widths = [0] * num_cols
            for row in rows_data:
                for i, cell in enumerate(row):
                    col_widths[i] = max(col_widths[i], len(cell))
            
            # Render table
            for row in rows_data:
                row_text = '  '.join(cell.ljust(col_widths[i]) for i, cell in enumerate(row))
                output_lines.append('  ' + row_text)
        output_lines.append('')
    
    elif elem_tag == 'lg':
        # Poem/verse
        rend = elem.get('rend', '')
        
        head = elem.find('tei:head', TEI_NS)
        if head is not None:
            title = ''.join(head.itertext()).strip()
            if title:
                if rend == 'center':
                    # Center the title
                    padding = (line_width - len(title)) // 2
                    output_lines.append(' ' * padding + title.upper())
                else:
                    output_lines.append('    ' + title.upper())
                output_lines.append('')
        
        # Check for nested stanzas
        nested_lg = elem.findall('tei:lg', TEI_NS)
        if nested_lg:
            for stanza in nested_lg:
                stanza_rend = stanza.get('rend', '')
                lines_to_add = []
                line_rends = []  # Track which lines are centered
                
                for line in stanza.findall('tei:l', TEI_NS):
                    line_text = extract_text_with_emphasis(line).strip()
                    line_rend = line.get('rend', '')
                    line_rends.append(line_rend)
                    
                    # Apply line-level indentation
                    if line_rend == 'center':
                        # Center individual line - already complete, no base indent needed
                        padding = (line_width - visual_length(line_text)) // 2
                        line_text = ' ' * padding + line_text
                    elif line_rend == 'indent':
                        line_text = '  ' + line_text  # 2 spaces for indent
                    elif line_rend == 'indent2':
                        line_text = '    ' + line_text  # 4 spaces
                    elif line_rend == 'indent3':
                        line_text = '      ' + line_text  # 6 spaces
                    
                    lines_to_add.append(line_text)
                
                # If stanza has center rend, center the block
                if stanza_rend == 'center':
                    # Find longest line (visual length)
                    max_len = max(visual_length(l) for l in lines_to_add) if lines_to_add else 0
                    # Calculate padding to center the block
                    block_padding = (line_width - max_len) // 2
                    # Add padding to all lines
                    for line_text in lines_to_add:
                        output_lines.append(' ' * block_padding + line_text)
                else:
                    # Normal poem indentation (4 spaces base) - but not for individually centered lines
                    for i, line_text in enumerate(lines_to_add):
                        if line_rends[i] == 'center':
                            output_lines.append(line_text)  # Already centered, no base indent
                        else:
                            output_lines.append('    ' + line_text)
                
                output_lines.append('')  # Blank line between stanzas
        else:
            # Single stanza
            lines_to_add = []
            line_rends = []  # Track which lines are centered
            
            for line in elem.findall('tei:l', TEI_NS):
                line_text = extract_text_with_emphasis(line).strip()
                line_rend = line.get('rend', '')
                line_rends.append(line_rend)
                
                # Apply line-level indentation
                if line_rend == 'center':
                    # Center individual line - already complete, no base indent needed
                    padding = (line_width - visual_length(line_text)) // 2
                    line_text = ' ' * padding + line_text
                elif line_rend == 'indent':
                    line_text = '  ' + line_text  # 2 spaces
                elif line_rend == 'indent2':
                    line_text = '    ' + line_text  # 4 spaces
                elif line_rend == 'indent3':
                    line_text = '      ' + line_text  # 6 spaces
                
                lines_to_add.append(line_text)
            
            # If lg has center rend, center the block
            if rend == 'center':
                # Find longest line (visual length)
                max_len = max(visual_length(l) for l in lines_to_add) if lines_to_add else 0
                # Calculate padding to center the block
                block_padding = (line_width - max_len) // 2
                # Add padding to all lines
                for line_text in lines_to_add:
                    output_lines.append(' ' * block_padding + line_text)
            else:
                # Normal poem indentation (4 spaces base) - but not for individually centered lines
                for i, line_text in enumerate(lines_to_add):
                    if line_rends[i] == 'center':
                        output_lines.append(line_text)  # Already centered, no base indent
                    else:
                        output_lines.append('    ' + line_text)
            
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
        
        if tag == 'lb':
            # Line break
            result += '\n'
        elif tag == 'quote':
            # Inline quote - add smart quotes (U+201C and U+201D)
            result += '\u201c' + child_text + '\u201d'
        elif tag in ['emph', 'hi']:
            # Mark emphasis with underscores
            result += f'_{child_text}_'
        elif tag == 'note':
            # Format notes in square brackets
            result += f' [{child_text}]'
        elif tag == 'ref':
            # Just include the link text
            result += child_text
        elif tag == 'title':
            # Mark titles with underscores like emphasis
            result += f'_{child_text}_'
        elif tag == 'foreign':
            # Mark foreign text with underscores
            result += f'_{child_text}_'
        else:
            result += child_text
        
        if child.tail:
            result += child.tail
    
    return result

def visual_length(text):
    """Calculate visual length of text, excluding underscore markers."""
    # Remove underscore pairs that mark emphasis
    import re
    # Replace _text_ with just text for counting purposes
    visual = re.sub(r'_([^_]+)_', r'\1', text)
    return len(visual)

