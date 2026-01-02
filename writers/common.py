"""
common.py - Shared utilities for TEI conversion
"""

import os
import glob
import re
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

    Discovery priority:
    1. Unified CSS files (co-located or css/ directory)
    2. Format-specific directory: css/{format_type}/ (legacy)

    Unified CSS files may contain @html/@epub/@both directives.
    Format-specific directories are for backward compatibility only.

    Args:
        xml_file: Path to source XML file
        format_type: 'html' or 'epub'

    Returns:
        List of CSS file paths in alphabetical order (empty if none found)
    """
    # Try unified discovery first
    unified_files = find_css_files_unified(xml_file)
    if unified_files:
        return unified_files

    # Fall back to legacy format-specific directory
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

def filter_css_for_format(css_content, format_type):
    """
    Filter CSS content to include only rules for specified format.

    Processes @html, @epub, and @both directives in CSS comments.
    Directives apply to all following rules until next directive.

    Args:
        css_content: Raw CSS content with optional directives
        format_type: Target format ('html' or 'epub')

    Returns:
        Filtered CSS with only applicable rules

    Examples:
        >>> css = '''
        ... /* @both */
        ... body { font-family: serif; }
        ... /* @html */
        ... body { max-width: 40em; }
        ... /* @epub */
        ... body { margin: 0 5%; }
        ... '''
        >>> filter_css_for_format(css, 'html')
        # Returns: body styles for both + html only
    """
    if not css_content:
        return ''

    lines = css_content.split('\n')
    output_lines = []
    current_mode = 'both'  # Default: include in both formats

    # Match: /* @html */ or /* @epub */ or /* @both */
    # Allow flexible whitespace
    directive_pattern = re.compile(r'^\s*/\*\s*@(html|epub|both)\s*\*/\s*$', re.IGNORECASE)

    for line in lines:
        match = directive_pattern.match(line)

        if match:
            # Update mode, don't include directive in output
            current_mode = match.group(1).lower()
            continue

        # Include line if in 'both' mode or matches current format
        if current_mode == 'both' or current_mode == format_type:
            output_lines.append(line)

    return '\n'.join(output_lines)

def find_css_files_unified(xml_file):
    """
    Find CSS files using unified discovery (no format parameter).

    Priority (returns first non-empty):
    1. Co-located: *.css in same directory as XML file
    2. Shared: css/*.css subdirectory
    3. None found: return empty list

    Note: Does NOT check css/html/ or css/epub/ (legacy paths).
    Use find_css_files() for full backward compatibility.

    Args:
        xml_file: Path to source XML file

    Returns:
        List of CSS file paths in alphabetical order (empty if none found)
    """
    xml_dir = os.path.dirname(os.path.abspath(xml_file))

    # Priority 1: Co-located CSS files
    colocated_pattern = os.path.join(xml_dir, '*.css')
    colocated_files = sorted(glob.glob(colocated_pattern))
    if colocated_files:
        return colocated_files

    # Priority 2: Shared css/ directory
    shared_css_dir = os.path.join(xml_dir, 'css')
    if os.path.isdir(shared_css_dir):
        shared_pattern = os.path.join(shared_css_dir, '*.css')
        shared_files = sorted(glob.glob(shared_pattern))
        if shared_files:
            return shared_files

    # Priority 3: Not found
    return []

