"""
Format-specific renderers for TEI conversion.

This package contains renderer implementations for different output formats:
- HTMLRenderer: Converts TEI to HTML
- TextRenderer: Converts TEI to plain text
- EPUBRenderer: Converts TEI to EPUB format
"""

from .html_renderer import HTMLRenderer

__all__ = ['HTMLRenderer']
