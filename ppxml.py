#!/usr/bin/env python3
"""
pptei.py - Command-line interface for TEI conversion

Simple standalone TEI converter for bookcove.net
Converts selecgted subset of TEI markup to HTML or plain text.

Usage:
    python bc_tei.py input.xml output.html
    python bc_tei.py input.xml output.html --css mystyles.css
    python bc_tei.py input.xml output.txt [width]
"""

import sys
import os
import argparse

# Import converter modules
from writers import to_html, to_text

def main():
    parser = argparse.ArgumentParser(
        description='TEI Converter for bookcove.net',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python tei_convert.py book.xml book.html
  python tei_convert.py book.xml book.html --css mystyles.css
  python tei_convert.py book.xml book.txt 72
        '''
    )
    
    parser.add_argument('input', help='Input TEI XML file')
    parser.add_argument('output', help='Output file (.html or .txt)')
    parser.add_argument('width', nargs='?', type=int, help='Line width for text output (default: 72)')
    parser.add_argument('--css', help='External CSS file for HTML output')
    
    args = parser.parse_args()
    
    input_file = args.input
    output_file = args.output
    
    if not os.path.exists(input_file):
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)
    
    try:
        if output_file.endswith('.html') or output_file.endswith('.xhtml'):
            to_html.convert(input_file, output_file, css_file=args.css)
        
        elif output_file.endswith('.txt'):
            width = args.width if args.width else 72
            to_text.convert(input_file, output_file, width)
        
        else:
            print("Error: Output file must have .html or .txt extension")
            sys.exit(1)
    
    except Exception as e:
        print(f"Error during conversion: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

