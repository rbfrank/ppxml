"""
common.py - Shared utilities for TEI conversion
"""

import os
import glob
from lxml import etree

# TEI namespace
TEI_NS = {'tei': 'http://www.tei-c.org/ns/1.0'}

def parse_tei(tei_file):
    """
    Parse a TEI XML file.
    
    Args:
        tei_file: Path to TEI XML file
        
    Returns:
        lxml etree document
    """
    return etree.parse(tei_file)

def get_title(doc):
    """
    Extract the document title from TEI header.
    
    Args:
        doc: Parsed TEI document
        
    Returns:
        Title string or "Untitled"
    """
    title_elem = doc.find('.//tei:title', TEI_NS)
    return title_elem.text if title_elem is not None else "Untitled"

def get_metadata(doc):
    """
    Extract basic metadata from TEI header.
    
    Args:
        doc: Parsed TEI document
        
    Returns:
        Dictionary with metadata fields
    """
    metadata = {
        'title': get_title(doc),
        'publication': None,
        'source': None
    }
    
    pub_elem = doc.find('.//tei:publicationStmt/tei:p', TEI_NS)
    if pub_elem is not None:
        metadata['publication'] = pub_elem.text
    
    source_elem = doc.find('.//tei:sourceDesc/tei:p', TEI_NS)
    if source_elem is not None:
        metadata['source'] = source_elem.text
    
    return metadata

def find_css_files(xml_file, format_type):
    """
    Find CSS files for the specified output format.

    Looks for CSS files in the format-specific directory:
    ./css/{format_type}/ relative to the XML source file.

    Args:
        xml_file: Path to source XML file
        format_type: 'html' or 'epub'

    Returns:
        List of CSS file paths in alphabetical order (empty if none found)
    """
    xml_dir = os.path.dirname(os.path.abspath(xml_file))
    format_css_dir = os.path.join(xml_dir, 'css', format_type)

    if os.path.isdir(format_css_dir):
        css_files = sorted(glob.glob(os.path.join(format_css_dir, '*.css')))
        return css_files

    return []

def read_css_files(css_paths):
    """
    Read and concatenate multiple CSS files.

    Args:
        css_paths: List of CSS file paths

    Returns:
        Concatenated CSS content as string (empty if no paths provided)
    """
    if not css_paths:
        return ''

    css_parts = []
    for path in css_paths:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                css_parts.append(f.read())
        except IOError as e:
            raise IOError(f"Error reading CSS file {path}: {e}")

    return '\n\n'.join(css_parts)

