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
            # Process heading if present
            head = div.find('tei:head', TEI_NS)
            if head is not None:
                heading_text = ''.join(head.itertext()).strip()
                output_lines.append(heading_text)
                output_lines.append('=' * len(heading_text))
                output_lines.append('')
            
            # Process all other child elements in order
            for elem in div:
                if not isinstance(elem.tag, str):
                    continue
                if elem.tag != f"{{{TEI_NS['tei']}}}head":  # Skip head, already processed
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
            # Collapse internal whitespace (including source line-breaks)
            # so prose paragraphs reflow correctly when wrapped.
            normalized = ' '.join(text.split())
            wrapped = textwrap.fill(normalized, width=line_width,
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
            block_children = [child for child in elem if child.tag.replace(f"{{{TEI_NS['tei']}}}", '') in ['p', 'lg', 'list', 'table', 'figure', 'div', 'quote']]
            if block_children:
                for child in block_children:
                    # Indent each block child
                    block_lines = []
                    process_element(child, block_lines, line_width)
                    for line in block_lines:
                        if line.strip() != '':
                            output_lines.append('    ' + line)
                        else:
                            output_lines.append('')
            else:
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
        # Poem/verse, now recursively process all children
        rend = elem.get('rend', '')
        for child in elem:
            child_tag = child.tag.replace(f"{{{TEI_NS['tei']}}}", '')
            if child_tag == 'head':
                title = ''.join(child.itertext()).strip()
                if title:
                    if rend == 'center':
                        padding = (line_width - len(title)) // 2
                        output_lines.append(' ' * padding + title.upper())
                    else:
                        output_lines.append('    ' + title.upper())
                    output_lines.append('')
            elif child_tag == 'lg':
                # Nested stanza
                stanza_rend = child.get('rend', '')
                lines_to_add = []
                line_rends = []
                for stanza_child in child:
                    stanza_child_tag = stanza_child.tag.replace(f"{{{TEI_NS['tei']}}}", '')
                    if stanza_child_tag == 'l':
                        line_text = extract_text_with_emphasis(stanza_child).strip()
                        line_rend = stanza_child.get('rend', '')
                        line_rends.append(line_rend)
                        if line_rend == 'center':
                            padding = (line_width - visual_length(line_text)) // 2
                            line_text = ' ' * padding + line_text
                        elif line_rend == 'indent':
                            line_text = '  ' + line_text
                        elif line_rend == 'indent2':
                            line_text = '    ' + line_text
                        elif line_rend == 'indent3':
                            line_text = '      ' + line_text
                        lines_to_add.append(line_text)
                    else:
                        # Recursively process any block element in stanza
                        stanza_lines = []
                        process_element(stanza_child, stanza_lines, line_width)
                        for line in stanza_lines:
                            lines_to_add.append(line)
                if stanza_rend == 'center':
                    max_len = max(visual_length(l) for l in lines_to_add) if lines_to_add else 0
                    block_padding = (line_width - max_len) // 2
                    for line_text in lines_to_add:
                        output_lines.append(' ' * block_padding + line_text)
                else:
                    for i, line_text in enumerate(lines_to_add):
                        if i < len(line_rends) and line_rends[i] == 'center':
                            output_lines.append(line_text)
                        else:
                            output_lines.append('    ' + line_text)
                output_lines.append('')
            elif child_tag == 'l':
                line_text = extract_text_with_emphasis(child).strip()
                line_rend = child.get('rend', '')
                if line_rend == 'center':
                    padding = (line_width - visual_length(line_text)) // 2
                    output_lines.append(' ' * padding + line_text)
                elif line_rend == 'indent':
                    output_lines.append('  ' + line_text)
                elif line_rend == 'indent2':
                    output_lines.append('    ' + line_text)
                elif line_rend == 'indent3':
                    output_lines.append('      ' + line_text)
                else:
                    output_lines.append('    ' + line_text)
            else:
                # Recursively process any block element in lg
                process_element(child, output_lines, line_width)
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

def extract_text_with_emphasis(elem, quote_depth=0):
    """Extract text from element, marking emphasis with underscores.
    
    Args:
        elem: The element to process
        quote_depth: Current nesting depth of quotes (0 = not in quote, 1 = outer, 2 = inner, etc.)
    """
    result = ''
    
    if elem.text:
        result = elem.text
    
    for child in elem:
        tag = child.tag.replace(f"{{{TEI_NS['tei']}}}", '')
        
        if tag == 'lb':
            # Line break
            result += '\n'
        elif tag == 'quote':
            # Recursively process quote content at next depth level
            child_text = extract_text_with_emphasis(child, quote_depth + 1)
            # Alternate between double and single quotes
            if quote_depth % 2 == 0:
                # Even depth (0, 2, 4...): use double quotes
                result += '\u201c' + child_text + '\u201d'
            else:
                # Odd depth (1, 3, 5...): use single quotes
                result += '\u2018' + child_text + '\u2019'
        elif tag in ['emph', 'hi']:
            child_text = ''.join(child.itertext())
            # Mark emphasis with underscores
            result += f'_{child_text}_'
        elif tag == 'note':
            child_text = ''.join(child.itertext())
            # Format notes in square brackets
            result += f' [{child_text}]'
        elif tag == 'ref':
            child_text = ''.join(child.itertext())
            # Just include the link text
            result += child_text
        elif tag == 'title':
            child_text = ''.join(child.itertext())
            # Mark titles with underscores like emphasis
            result += f'_{child_text}_'
        elif tag == 'foreign':
            child_text = ''.join(child.itertext())
            # Mark foreign text with underscores
            result += f'_{child_text}_'
        else:
            child_text = ''.join(child.itertext())
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

