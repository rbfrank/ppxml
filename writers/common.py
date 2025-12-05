"""
common.py - Shared utilities for TEI conversion
"""

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

