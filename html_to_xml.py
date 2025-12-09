#!/usr/bin/env python3
"""
html_to_xml.py - Convert HTML to TEI XML format

Converts HTML files to TEI XML markup compatible with ppxml.
Attempts to map common HTML elements to appropriate TEI elements.

Usage:
    python html_to_xml.py input.html output.xml
    python html_to_xml.py input.html output.xml --title "Book Title"
"""

import sys
import os
import argparse
from html.parser import HTMLParser
from datetime import date
import re


class HTMLToTEIConverter(HTMLParser):
    """Converts HTML to TEI XML format."""
    
    def __init__(self, title="Untitled", author="Unknown"):
        super().__init__()
        self.title = title
        self.author = author
        self.tei_content = []
        self.current_tags = []
        self.in_head = False
        self.in_body = False
        self.in_front = False
        self.in_back = False
        self.list_stack = []
        self.table_depth = 0
        self.figure_depth = 0
        self.skip_content = False
        self.extracted_title = None
        self.chapter_counter = 0
        
    def handle_starttag(self, tag, attrs):
        """Handle opening HTML tags."""
        attrs_dict = dict(attrs)
        
        # Skip script and style content
        if tag in ['script', 'style']:
            self.skip_content = True
            return
            
        # Extract title from HTML head
        if tag == 'title' and not self.in_body:
            self.in_head = True
            return
            
        # Document structure
        if tag == 'body':
            self.in_body = True
            return
            
        if not self.in_body:
            return
            
        # Headings - map to div with head
        if tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            self.chapter_counter += 1
            level = int(tag[1])
            div_type = 'chapter' if level <= 2 else 'section'
            self.tei_content.append(f'<div type="{div_type}" n="{self.chapter_counter}">')
            self.tei_content.append('<head>')
            self.current_tags.append(('div', div_type))
            self.current_tags.append(('head', None))
            return
            
        # Paragraphs
        if tag == 'p':
            self.tei_content.append('<p>')
            self.current_tags.append(('p', None))
            return
            
        # Line breaks
        if tag == 'br':
            self.tei_content.append('<lb/>')
            return
            
        # Horizontal rule -> milestone
        if tag == 'hr':
            self.tei_content.append('<milestone rend="stars"/>')
            return
            
        # Lists
        if tag in ['ul', 'ol']:
            self.tei_content.append('<list>')
            self.list_stack.append(tag)
            self.current_tags.append(('list', None))
            return
            
        if tag == 'li':
            self.tei_content.append('<item>')
            self.current_tags.append(('item', None))
            return
            
        # Tables
        if tag == 'table':
            self.tei_content.append('<table>')
            self.table_depth += 1
            self.current_tags.append(('table', None))
            return
            
        if tag == 'tr':
            self.tei_content.append('<row>')
            self.current_tags.append(('row', None))
            return
            
        if tag in ['td', 'th']:
            role = ' role="label"' if tag == 'th' else ''
            self.tei_content.append(f'<cell{role}>')
            self.current_tags.append(('cell', None))
            return
            
        # Emphasis and styling
        if tag in ['em', 'i']:
            self.tei_content.append('<hi rend="italic">')
            self.current_tags.append(('hi', 'italic'))
            return
            
        if tag in ['strong', 'b']:
            self.tei_content.append('<hi rend="bold">')
            self.current_tags.append(('hi', 'bold'))
            return
            
        if tag == 'u':
            self.tei_content.append('<hi rend="underline">')
            self.current_tags.append(('hi', 'underline'))
            return
            
        if tag == 'code':
            self.tei_content.append('<hi rend="monospace">')
            self.current_tags.append(('hi', 'monospace'))
            return
            
        # Quotations
        if tag == 'blockquote':
            self.tei_content.append('<quote rend="block">')
            self.current_tags.append(('quote', None))
            return
            
        if tag == 'q':
            self.tei_content.append('<quote>')
            self.current_tags.append(('quote', None))
            return
            
        # Links -> ref
        if tag == 'a':
            href = attrs_dict.get('href', '')
            if href:
                self.tei_content.append(f'<ref target="{self.escape_xml(href)}">')
            else:
                self.tei_content.append('<ref>')
            self.current_tags.append(('ref', None))
            return
            
        # Images -> figure with graphic
        if tag == 'img':
            src = attrs_dict.get('src', '')
            alt = attrs_dict.get('alt', '')
            
            self.tei_content.append('<figure>')
            if src:
                self.tei_content.append(f'<graphic url="{self.escape_xml(src)}"/>')
            if alt:
                self.tei_content.append(f'<figDesc>{self.escape_xml(alt)}</figDesc>')
            self.tei_content.append('</figure>')
            return
            
        # Figure element
        if tag == 'figure':
            self.tei_content.append('<figure>')
            self.figure_depth += 1
            self.current_tags.append(('figure', None))
            return
            
        if tag == 'figcaption':
            self.tei_content.append('<head>')
            self.current_tags.append(('head', None))
            return
            
        # Divs - try to preserve structure
        if tag == 'div':
            css_class = attrs_dict.get('class', '')
            div_id = attrs_dict.get('id', '')
            
            # Try to infer div type from class or id
            div_type = 'section'
            if any(word in css_class.lower() or word in div_id.lower() 
                   for word in ['chapter', 'preface', 'introduction', 'appendix']):
                for word in ['chapter', 'preface', 'introduction', 'appendix']:
                    if word in css_class.lower() or word in div_id.lower():
                        div_type = word
                        break
            
            self.tei_content.append(f'<div type="{div_type}">')
            self.current_tags.append(('div', div_type))
            return
            
    def handle_endtag(self, tag):
        """Handle closing HTML tags."""
        
        if tag in ['script', 'style']:
            self.skip_content = False
            return
            
        if tag == 'title':
            self.in_head = False
            return
            
        if not self.in_body and tag != 'body':
            return
            
        if tag == 'body':
            return
            
        # Skip self-closing tags
        if tag in ['br', 'hr', 'img']:
            return
            
        # Close heading and div
        if tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            if self.current_tags and self.current_tags[-1][0] == 'head':
                self.tei_content.append('</head>')
                self.current_tags.pop()
            # Note: div stays open for content after heading
            return
            
        # Close other tags
        if self.current_tags and self.current_tags[-1][0] in ['p', 'item', 'cell', 'row', 'head', 'ref', 'quote']:
            tag_name, _ = self.current_tags.pop()
            self.tei_content.append(f'</{tag_name}>')
            return
            
        if tag in ['ul', 'ol'] and self.current_tags and self.current_tags[-1][0] == 'list':
            self.current_tags.pop()
            self.tei_content.append('</list>')
            if self.list_stack:
                self.list_stack.pop()
            return
            
        if tag == 'table' and self.current_tags and self.current_tags[-1][0] == 'table':
            self.current_tags.pop()
            self.tei_content.append('</table>')
            self.table_depth -= 1
            return
            
        if tag in ['em', 'i', 'strong', 'b', 'u', 'code'] and self.current_tags and self.current_tags[-1][0] == 'hi':
            self.current_tags.pop()
            self.tei_content.append('</hi>')
            return
            
        if tag == 'figure' and self.current_tags and self.current_tags[-1][0] == 'figure':
            self.current_tags.pop()
            self.tei_content.append('</figure>')
            self.figure_depth -= 1
            return
            
        if tag == 'div' and self.current_tags and self.current_tags[-1][0] == 'div':
            self.current_tags.pop()
            self.tei_content.append('</div>')
            return
            
    def handle_data(self, data):
        """Handle text content."""
        if self.skip_content:
            return
            
        if self.in_head and not self.in_body:
            # Extract title from HTML
            self.extracted_title = data.strip()
            return
            
        if not self.in_body:
            return
            
        # Clean up whitespace but preserve intentional spacing
        data = data.strip()
        if data:
            escaped = self.escape_xml(data)
            self.tei_content.append(escaped)
            
    def escape_xml(self, text):
        """Escape special XML characters."""
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&apos;')
        return text
        
    def generate_tei(self):
        """Generate complete TEI XML document."""
        
        # Close any remaining open tags
        while self.current_tags:
            tag_name, _ = self.current_tags.pop()
            self.tei_content.append(f'</{tag_name}>')
        
        # Use extracted title if available
        doc_title = self.extracted_title if self.extracted_title else self.title
        
        # Build TEI document
        tei_doc = ['<?xml version="1.0" encoding="UTF-8"?>']
        tei_doc.append('<TEI xmlns="http://www.tei-c.org/ns/1.0">')
        tei_doc.append('  <teiHeader>')
        tei_doc.append('    <fileDesc>')
        tei_doc.append('      <titleStmt>')
        tei_doc.append(f'        <title>{self.escape_xml(doc_title)}</title>')
        if self.author != "Unknown":
            tei_doc.append(f'        <author>{self.escape_xml(self.author)}</author>')
        tei_doc.append('      </titleStmt>')
        tei_doc.append('      <publicationStmt>')
        tei_doc.append('        <p>Converted from HTML</p>')
        tei_doc.append('      </publicationStmt>')
        tei_doc.append('      <sourceDesc>')
        tei_doc.append(f'        <p>Converted on {date.today().isoformat()}</p>')
        tei_doc.append('      </sourceDesc>')
        tei_doc.append('    </fileDesc>')
        tei_doc.append('  </teiHeader>')
        tei_doc.append('  <text>')
        tei_doc.append('    <body>')
        
        # Add converted content with basic indentation
        for line in self.tei_content:
            if line.startswith('</'):
                tei_doc.append(f'      {line}')
            else:
                tei_doc.append(f'      {line}')
        
        tei_doc.append('    </body>')
        tei_doc.append('  </text>')
        tei_doc.append('</TEI>')
        
        return '\n'.join(tei_doc)


def convert_html_to_tei(input_file, output_file, title=None, author=None):
    """
    Convert HTML file to TEI XML.
    
    Args:
        input_file: Path to input HTML file
        output_file: Path to output XML file
        title: Optional title (defaults to extracted from HTML or "Untitled")
        author: Optional author name
    """
    
    # Read HTML file
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except Exception as e:
        print(f"Error reading input file: {e}")
        sys.exit(1)
    
    # Convert
    converter = HTMLToTEIConverter(
        title=title or "Untitled",
        author=author or "Unknown"
    )
    
    converter.feed(html_content)
    tei_xml = converter.generate_tei()
    
    # Write output
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(tei_xml)
        print(f"Successfully converted {input_file} to {output_file}")
    except Exception as e:
        print(f"Error writing output file: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Convert HTML to TEI XML format compatible with ppxml',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python html_to_xml.py book.html book.xml
  python html_to_xml.py book.html book.xml --title "My Book" --author "Jane Doe"

Notes:
  - HTML structure is mapped to TEI elements as closely as possible
  - <h1>, <h2> become chapters; <h3>+ become sections
  - <em>, <i> become <hi rend="italic">
  - <strong>, <b> become <hi rend="bold">
  - <img> becomes <figure> with <graphic>
  - Lists, tables, and other structures are preserved
  - Manual review and editing of output is recommended
        '''
    )
    
    parser.add_argument('input', help='Input HTML file')
    parser.add_argument('output', help='Output TEI XML file')
    parser.add_argument('--title', help='Document title (extracted from HTML if not provided)')
    parser.add_argument('--author', help='Document author')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)
    
    convert_html_to_tei(args.input, args.output, args.title, args.author)


if __name__ == '__main__':
    main()
